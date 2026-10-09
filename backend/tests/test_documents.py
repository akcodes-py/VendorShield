"""Document tests. WHY: secure upload + expiry + review guards."""
from datetime import date, timedelta

from tests.conftest import auth_header, login
from app.models.vendor import Vendor

PDF = b"%PDF-1.4 SAMPLE fake pdf bytes"
PNG = b"\x89PNG\r\n\x1a\nSAMPLE"


def _tok(client, email):
    return login(client, email).json()["access_token"]


def _upload(client, tok, vendor_id, fname="cert.pdf", ctype="application/pdf", data=None, dtype="ISO27001",
            expiry=None):
    data = data if data is not None else PDF
    form = {"vendor_id": str(vendor_id), "doc_type": dtype}
    if expiry:
        form["expiry_date"] = expiry
    return client.post("/api/v1/documents/upload", data=form,
                       files={"file": (fname, data, ctype)}, headers=auth_header(tok))


def test_upload_valid_random_name(client, db):
    t = _tok(client, "reviewer@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    r = _upload(client, t, v.id)
    assert r.status_code == 201
    body = r.json()
    assert body["expiry_flag"] in ("Valid", "NoExpiry", "Expiring", "Expired")
    assert body["original_name"] == "cert.pdf"
    # WHY: stored random hex, never original path.
    from app.models.document import Document
    d = db.get(Document, body["id"])
    assert d.stored_name != "cert.pdf" and d.stored_name.endswith(".pdf")
    from app.services.documents import UPLOAD_ABS
    assert (UPLOAD_ABS / d.stored_name).exists()


def test_malicious_uploads_blocked(client, db):
    t = _tok(client, "reviewer@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    # exe extension
    assert _upload(client, t, v.id, "evil.exe", "application/octet-stream", b"MZ...").status_code == 400
    # spoof: .pdf name but exe bytes
    assert _upload(client, t, v.id, "fake.pdf", "application/pdf", b"MZ spoof").status_code == 400
    # mime mismatch
    assert _upload(client, t, v.id, "cert.pdf", "image/png", PDF).status_code == 400
    # empty
    assert _upload(client, t, v.id, "cert.pdf", "application/pdf", b"").status_code == 400


def test_auditor_readonly_vendor_scoped(client, db):
    ta, tv = _tok(client, "auditor@example.com"), _tok(client, "vendor1@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    v2 = db.query(Vendor).filter_by(name="Beta SAMPLE").first()
    # auditor cannot upload
    assert _upload(client, ta, v.id).status_code == 403
    # vendor uploads own ok
    assert _upload(client, tv, v.id).status_code == 201
    # vendor cannot upload/list other's
    assert _upload(client, tv, v2.id).status_code == 403
    mine = client.get("/api/v1/documents", headers=auth_header(tv)).json()
    assert all(d["vendor_id"] == v.id for d in mine)


def test_expiry_flags_and_filter(client, db):
    t = _tok(client, "reviewer@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    today = date.today()
    _upload(client, t, v.id, expiry=str(today - timedelta(days=1)))
    _upload(client, t, v.id, expiry=str(today + timedelta(days=10)))
    _upload(client, t, v.id, expiry=str(today + timedelta(days=90)))
    exp = client.get("/api/v1/documents?status=Expired", headers=auth_header(t)).json()
    soon = client.get("/api/v1/documents?status=Expiring", headers=auth_header(t)).json()
    valid = client.get("/api/v1/documents?status=Valid", headers=auth_header(t)).json()
    assert len(exp) >= 1 and len(soon) >= 1 and len(valid) >= 1


def test_review_rbac_and_ai_disabled(client, db):
    tr, tv, ta = _tok(client, "reviewer@example.com"), _tok(client, "vendor1@example.com"), _tok(client, "auditor@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    did = _upload(client, tr, v.id).json()["id"]
    # vendor/auditor cannot review
    for tok in (tv, ta):
        r = client.patch(f"/api/v1/documents/{did}/review",
                         json={"review_status": "Approved", "review_notes": "ok"}, headers=auth_header(tok))
        assert r.status_code == 403
    # reviewer can
    r2 = client.patch(f"/api/v1/documents/{did}/review",
                      json={"review_status": "Approved", "review_notes": "checked SAMPLE"},
                      headers=auth_header(tr))
    assert r2.status_code == 200 and r2.json()["review_status"] == "Approved"
    # AI disabled by default -> honest 400 with risks note, never fake output
    ai = client.post(f"/api/v1/documents/{did}/ai-summary", headers=auth_header(tr))
    assert ai.status_code == 400
    assert "reviewer must confirm" in ai.json()["detail"].lower()
