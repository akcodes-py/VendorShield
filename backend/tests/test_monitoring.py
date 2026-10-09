"""SOC tests. WHY: rules fire on facts, dedupe, stepwise incidents, no Vendor SOC."""
from tests.conftest import auth_header, login
from app.models.vendor import Vendor


def _tok(client, email):
    return login(client, email).json()["access_token"]


def _ev(client, tok, etype, ip="9.9.9.9", uid=None, detail="SAMPLE test"):
    return client.post("/api/v1/security-events",
                       json={"type": etype, "user_id": uid, "ip": ip, "detail": detail},
                       headers=auth_header(tok))


def test_bruteforce_rule_and_dedupe(client, db):
    tr = _tok(client, "reviewer@example.com")
    for _ in range(5):
        assert _ev(client, tr, "failed_login", "9.9.9.9").status_code == 201
    r1 = client.post("/api/v1/detection/run", headers=auth_header(tr)).json()
    assert any(a["rule"] == "brute-force" and a["severity"] == "High" for a in r1)
    # WHY: second run creates nothing - dedupe stops storm.
    r2 = client.post("/api/v1/detection/run", headers=auth_header(tr)).json()
    assert not any(a["rule"] == "brute-force" and "9.9.9.9" in a["detail"] for a in r2)


def test_new_ip_and_perm_probe(client, db):
    from app.models.user import User
    tr = _tok(client, "reviewer@example.com")
    rev = db.query(User).filter_by(email="reviewer@example.com").first()
    _ev(client, tr, "login_success", "1.1.1.1", rev.id, "known")
    _ev(client, tr, "login_success", "8.8.8.8", rev.id, "unknown SAMPLE")
    for _ in range(10):
        _ev(client, tr, "perm_denied", "9.9.9.9")
    out = client.post("/api/v1/detection/run", headers=auth_header(tr)).json()
    assert any(a["rule"] == "new-ip" for a in out)
    assert any(a["rule"] == "perm-probe" for a in out)


def test_triage_rbac_and_vendor_blocked(client):
    tr, tv, ta = _tok(client, "reviewer@example.com"), _tok(client, "vendor1@example.com"), _tok(client, "auditor@example.com")
    assert client.get("/api/v1/security-events", headers=auth_header(tv)).status_code == 403
    assert client.get("/api/v1/alerts", headers=auth_header(tv)).status_code == 403
    for _ in range(5):
        _ev(client, tr, "failed_login", "7.7.7.7")
    aid = client.post("/api/v1/detection/run", headers=auth_header(tr)).json()[0]["id"]
    # auditor read ok but cannot triage (read-only)
    assert client.get("/api/v1/alerts", headers=auth_header(ta)).status_code == 200
    assert client.patch(f"/api/v1/alerts/{aid}", json={"status": "Investigating"},
                        headers=auth_header(ta)).status_code == 403
    assert client.patch(f"/api/v1/alerts/{aid}", json={"status": "Investigating"},
                        headers=auth_header(tr)).status_code == 200


def test_failed_login_auto_logged(client):
    login(client, "reviewer@example.com", "wrong")
    tr = _tok(client, "reviewer@example.com")
    evs = client.get("/api/v1/security-events", headers=auth_header(tr)).json()
    assert any(e["type"] == "failed_login" for e in evs)


def test_incident_stepwise_and_vendor_link(client, db):
    tr, tv = _tok(client, "reviewer@example.com"), _tok(client, "vendor1@example.com")
    assert client.post("/api/v1/incidents", json={"title": "x"},
                       headers=auth_header(tr)).status_code == 422
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    inc = client.post("/api/v1/incidents", json={"title": "SAMPLE phishing via vendor",
                                                 "vendor_id": v.id, "severity": "High"},
                      headers=auth_header(tr)).json()
    iid = inc["id"]
    # skip Detected->Contained must fail
    bad = client.post(f"/api/v1/incidents/{iid}/transition", json={"to": "Contained"},
                      headers=auth_header(tr))
    assert bad.status_code == 400
    # stepwise ok + notes timeline
    assert client.post(f"/api/v1/incidents/{iid}/transition", json={"to": "Triaged"},
                       headers=auth_header(tr)).status_code == 200
    assert client.post(f"/api/v1/incidents/{iid}/notes", json={"note": "SAMPLE isolated host"},
                       headers=auth_header(tr)).status_code == 201
    got = client.get(f"/api/v1/incidents/{iid}", headers=auth_header(tr)).json()
    assert got["vendor_id"] == v.id and len(got["timeline"]) >= 2
    # vendor blocked from incidents
    assert client.get("/api/v1/incidents", headers=auth_header(tv)).status_code == 403
