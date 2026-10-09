"""Vendor tests. WHY: lifecycle + tier freq + IDOR + delete SoD."""
from tests.conftest import auth_header, login
from app.models.vendor import Vendor


def _tok(client, email):
    return login(client, email).json()["access_token"]


def test_create_vendor_auto_freq(client):
    t = _tok(client, "reviewer@example.com")
    r = client.post("/api/v1/vendors", json={"name": "NewCo SAMPLE", "service_type": "Cloud",
                                             "data_access": "High", "tier": 1},
                    headers=auth_header(t))
    assert r.status_code == 201
    assert r.json()["freq_months"] == 6  # WHY: T1 = 6mo
    assert r.json()["lifecycle"] == "Onboarding"


def test_auditor_cannot_create_vendor(client):
    t = _tok(client, "auditor@example.com")
    r = client.post("/api/v1/vendors", json={"name": "X", "service_type": "Cloud", "tier": 2},
                    headers=auth_header(t))
    assert r.status_code == 403


def test_vendor_sees_only_own(client, db):
    t = _tok(client, "vendor1@example.com")
    r = client.get("/api/v1/vendors", headers=auth_header(t))
    assert r.status_code == 200
    assert len(r.json()) == 1  # WHY: scoped to own vendor_id
    # IDOR: other vendor blocked
    other = db.query(Vendor).filter_by(name="Beta SAMPLE").first()
    assert client.get(f"/api/v1/vendors/{other.id}", headers=auth_header(t)).status_code == 403


def test_lifecycle_reviewer_cannot_approve(client, db):
    t = _tok(client, "reviewer@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    # Reviewer can move Onboarding->Assessment
    assert client.post(f"/api/v1/vendors/{v.id}/transition", json={"to": "Assessment"},
                       headers=auth_header(t)).status_code == 200
    # but NOT Assessment->Approved (Admin only)
    r2 = client.post(f"/api/v1/vendors/{v.id}/transition", json={"to": "Approved"},
                     headers=auth_header(t))
    assert r2.status_code == 400


def test_lifecycle_admin_can_approve(client, db):
    tr = _tok(client, "reviewer@example.com")
    ta = _tok(client, "admin@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    client.post(f"/api/v1/vendors/{v.id}/transition", json={"to": "Assessment"}, headers=auth_header(tr))
    r = client.post(f"/api/v1/vendors/{v.id}/transition", json={"to": "Approved"}, headers=auth_header(ta))
    assert r.status_code == 200
    assert r.json()["lifecycle"] == "Approved"


def test_illegal_transition_blocked(client, db):
    t = _tok(client, "admin@example.com")
    v = db.query(Vendor).filter_by(name="Beta SAMPLE").first()  # Approved
    r = client.post(f"/api/v1/vendors/{v.id}/transition", json={"to": "Onboarding"},
                    headers=auth_header(t))
    assert r.status_code == 400


def test_delete_needs_second_admin(client, db):
    a1 = _tok(client, "admin@example.com")
    # Beta has no history in test DB (no risks/docs) so hard delete allowed
    v = db.query(Vendor).filter_by(name="Beta SAMPLE").first()
    rr = client.post(f"/api/v1/vendors/{v.id}/delete-request", headers=auth_header(a1))
    assert rr.status_code == 201
    aid = rr.json()["approval_id"]
    # self-approve blocked
    assert client.post(f"/api/v1/approvals/{aid}/decide", json={"approve": True},
                       headers=auth_header(a1)).status_code == 403
    a2 = _tok(client, "admin2@example.com")
    assert client.post(f"/api/v1/approvals/{aid}/decide", json={"approve": True},
                       headers=auth_header(a2)).status_code == 200
    assert db.get(Vendor, v.id) is None
