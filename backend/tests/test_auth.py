"""Auth tests. WHY: proves JWT, MFA, refresh rotation, brute-force guard."""
import pyotp

from tests.conftest import auth_header, login
from app.models.audit_log import AuditLog
from app.models.user import User


def test_login_success(client):
    r = login(client, "reviewer@example.com")
    assert r.status_code == 200
    assert "access_token" in r.json() and "refresh_token" in r.json()


def test_login_wrong_password_401(client):
    r = login(client, "reviewer@example.com", "wrong")
    assert r.status_code == 401


def test_admin_mfa_flag_when_not_enabled(client):
    r = login(client, "admin@example.com")
    assert r.status_code == 200
    assert r.json()["mfa_required"] is True  # WHY: forces setup


def test_mfa_setup_verify_then_enforced(client, db):
    # setup as admin
    tok = login(client, "admin@example.com").json()["access_token"]
    s = client.post("/api/v1/auth/mfa/setup", headers=auth_header(tok))
    assert s.status_code == 200
    secret = s.json()["secret"]
    code = pyotp.TOTP(secret).now()
    v = client.post("/api/v1/auth/mfa/verify", json={"code": code}, headers=auth_header(tok))
    assert v.status_code == 200

    # now login without code must fail (MFA enforced)
    r2 = login(client, "admin@example.com")
    assert r2.status_code == 401
    # with fresh code succeeds
    r3 = login(client, "admin@example.com", code=pyotp.TOTP(secret).now())
    assert r3.status_code == 200


def test_refresh_rotation(client):
    tok = login(client, "reviewer@example.com").json()
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r1.status_code == 200
    # WHY: old refresh must die after rotation.
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r2.status_code == 401


def test_bruteforce_429(client):
    for _ in range(5):
        login(client, "reviewer@example.com", "wrong")
    r = login(client, "reviewer@example.com", "wrong")
    assert r.status_code == 429  # WHY: 5 fails in 5 min blocks


def test_audit_on_login(client, db):
    login(client, "reviewer@example.com")
    assert db.query(AuditLog).filter_by(action="login").count() >= 1
