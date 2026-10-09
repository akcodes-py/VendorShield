"""Attack tests on own app. WHY: proves broken-access + IDOR + SoD guards."""
from tests.conftest import auth_header, login


def _tok(client, email):
    return login(client, email).json()["access_token"]


def test_reviewer_cannot_create_user(client):
    t = _tok(client, "reviewer@example.com")
    r = client.post("/api/v1/users", json={"email": "x@test.com", "password": "Password123!", "role": "Reviewer"},
                    headers=auth_header(t))
    assert r.status_code == 403  # WHY: Admin only


def test_vendor_cannot_list_users(client):
    t = _tok(client, "vendor1@example.com")
    r = client.get("/api/v1/users", headers=auth_header(t))
    assert r.status_code == 403


def test_auditor_readonly_cannot_create(client):
    t = _tok(client, "auditor@example.com")
    r = client.post("/api/v1/users", json={"email": "y@test.com", "password": "Password123!", "role": "Reviewer"},
                    headers=auth_header(t))
    assert r.status_code == 403
    # but CAN read list + audit
    assert client.get("/api/v1/users", headers=auth_header(t)).status_code == 200
    assert client.get("/api/v1/audit-logs", headers=auth_header(t)).status_code == 200


def test_vendor_idor_blocked(client, db):
    from app.models.user import User
    rev = db.query(User).filter_by(email="reviewer@example.com").first()
    t = _tok(client, "vendor1@example.com")
    r = client.get(f"/api/v1/users/{rev.id}", headers=auth_header(t))
    assert r.status_code == 403  # WHY: cannot see other users


def test_sod_second_admin_required(client, db):
    from app.models.user import User
    a1 = _tok(client, "admin@example.com")
    target = db.query(User).filter_by(email="reviewer@example.com").first()
    rr = client.post(f"/api/v1/users/{target.id}/role-request",
                     json={"new_role": "Auditor", "reason": "rotation test"},
                     headers=auth_header(a1))
    assert rr.status_code == 201
    aid = rr.json()["approval_id"]
    # self-approve must fail
    bad = client.post(f"/api/v1/approvals/{aid}/decide", json={"approve": True},
                      headers=auth_header(a1))
    assert bad.status_code == 403
    # 2nd admin approves -> role actually changes
    a2 = _tok(client, "admin2@example.com")
    good = client.post(f"/api/v1/approvals/{aid}/decide", json={"approve": True, "comments": "ok"},
                       headers=auth_header(a2))
    assert good.status_code == 200
    db.refresh(target)
    assert target.role == "Auditor"


def test_revoked_cannot_login(client, db):
    from app.models.user import User
    a1 = _tok(client, "admin@example.com")
    rev = db.query(User).filter_by(email="reviewer@example.com").first()
    client.post(f"/api/v1/users/{rev.id}/revoke", headers=auth_header(a1))
    r = login(client, "reviewer@example.com")
    assert r.status_code == 401


def test_audit_immutable(client):
    t = _tok(client, "admin@example.com")
    # WHY: no DELETE/PUT route exists -> 404/405 proves append-only.
    assert client.delete("/api/v1/audit-logs").status_code in (404, 405)


def test_security_headers(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
