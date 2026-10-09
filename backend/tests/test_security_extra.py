"""Extra attack tests (Phase 10). WHY: self-hack proves JWT/traversal/XSS guards."""
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from tests.conftest import auth_header, login


def _tok(client, email):
    return login(client, email).json()["access_token"]


def test_jwt_tamper_rejected(client):
    t = _tok(client, "reviewer@example.com")
    bad = t[:-2] + ("ab" if not t.endswith("ab") else "cd")
    r = client.get("/api/v1/users", headers=auth_header(bad))
    assert r.status_code == 401  # WHY: signature check fails


def test_expired_token_rejected(client, db):
    from app.models.user import User
    u = db.query(User).filter_by(email="reviewer@example.com").first()
    exp = datetime.now(timezone.utc) - timedelta(minutes=1)
    tok = jwt.encode({"sub": str(u.id), "role": u.role, "type": "access", "exp": exp},
                     settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    assert client.get("/api/v1/users", headers=auth_header(tok)).status_code == 401


def test_refresh_with_access_token_rejected(client):
    t = _tok(client, "reviewer@example.com")
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": t})
    assert r.status_code == 401  # WHY: type claim stops confusion


def test_path_traversal_filename_neutralised(client, db):
    from app.models.document import Document
    from app.services.documents import UPLOAD_ABS
    t = _tok(client, "reviewer@example.com")
    from app.models.vendor import Vendor
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    pdf = b"%PDF-1.4 SAMPLE"
    # WHY: traversal name must not escape upload dir - stored random hex.
    r = client.post("/api/v1/documents/upload", data={"vendor_id": str(v.id), "doc_type": "ISO27001"},
                    files={"file": ("../../etc/passwd.pdf", pdf, "application/pdf")},
                    headers=auth_header(t))
    assert r.status_code == 201
    d = db.get(Document, r.json()["id"])
    assert ".." not in d.stored_name and "/" not in d.stored_name
    assert (UPLOAD_ABS / d.stored_name).exists()


def test_xss_payload_stored_not_executed(client):
    t = _tok(client, "reviewer@example.com")
    xss = "<script>alert(1)</script> SAMPLE"
    r = client.post("/api/v1/vendors", json={"name": xss, "service_type": "Cloud", "tier": 3},
                    headers=auth_header(t))
    assert r.status_code == 201
    vid = r.json()["id"]
    got = client.get(f"/api/v1/vendors/{vid}", headers=auth_header(t)).json()
    # WHY: server stores inert string; React escapes on render (no dangerouslySetInnerHTML used).
    assert got["name"] == xss


def test_oversize_upload_blocked(client, db, monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, "MAX_UPLOAD_MB", 1)
    t = _tok(client, "reviewer@example.com")
    from app.models.vendor import Vendor
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    big = b"%PDF" + b"\x00" * (2 * 1024 * 1024)  # 2MB > 1MB limit
    r = client.post("/api/v1/documents/upload", data={"vendor_id": str(v.id), "doc_type": "ISO27001"},
                    files={"file": ("big.pdf", big, "application/pdf")},
                    headers=auth_header(t))
    assert r.status_code == 400
