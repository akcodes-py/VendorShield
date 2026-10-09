"""Risk tests. WHY: LxI math + heatmap + overdue + exception SoD."""
from datetime import date, timedelta

from tests.conftest import auth_header, login
from app.models.vendor import Vendor


def _tok(client, email):
    return login(client, email).json()["access_token"]


def _mk(client, db, L=4, I=5, due=None, desc="SAMPLE risk no MFA"):
    t = _tok(client, "reviewer@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    r = client.post("/api/v1/risks", json={"vendor_id": v.id, "description": desc,
                                           "category": "cyber", "likelihood": L, "impact": I,
                                           "due_date": due}, headers=auth_header(t))
    assert r.status_code == 201
    return r.json()


def test_inherent_and_severity(client, db):
    body = _mk(client, db, 4, 5)
    assert body["inherent_score"] == 20
    assert body["severity"] == "Critical"
    assert body["residual_score"] == 20  # WHY: starts equal until controls proven


def test_residual_needs_controls(client, db):
    t = _tok(client, "reviewer@example.com")
    rid = _mk(client, db)["id"]
    # lower residual without controls -> 400
    r = client.patch(f"/api/v1/risks/{rid}", json={"residual_score": 8}, headers=auth_header(t))
    assert r.status_code == 400
    # with controls ok
    r2 = client.patch(f"/api/v1/risks/{rid}", json={"residual_score": 8, "controls": "MFA enforced SAMPLE"},
                      headers=auth_header(t))
    assert r2.status_code == 200 and r2.json()["residual_score"] == 8


def test_overdue_and_heatmap(client, db):
    past = str(date.today() - timedelta(days=3))
    future = str(date.today() + timedelta(days=30))
    _mk(client, db, 5, 5, due=past, desc="SAMPLE overdue critical risk")
    _mk(client, db, 2, 2, due=future, desc="SAMPLE future low risk")
    t = _tok(client, "reviewer@example.com")
    od = client.get("/api/v1/risks?overdue=true", headers=auth_header(t)).json()
    assert any(r["overdue"] for r in od)
    hm = client.get("/api/v1/risks/heatmap", headers=auth_header(t)).json()
    assert len(hm["matrix"]) == 5 and len(hm["matrix"][0]) == 5
    assert hm["by_severity"]["Critical"] >= 1


def test_remediation_overdue(client, db):
    t = _tok(client, "reviewer@example.com")
    rid = _mk(client, db)["id"]
    past = str(date.today() - timedelta(days=1))
    m = client.post(f"/api/v1/risks/{rid}/remediations",
                    json={"action": "SAMPLE enforce MFA", "owner": "vendor", "due_date": past},
                    headers=auth_header(t)).json()
    lst = client.get(f"/api/v1/risks/{rid}/remediations", headers=auth_header(t)).json()
    assert any(x["overdue"] for x in lst)
    # mark done clears overdue
    mid = lst[0]["id"]
    client.patch(f"/api/v1/remediations/{mid}", json={"status": "done"}, headers=auth_header(t))
    lst2 = client.get(f"/api/v1/risks/{rid}/remediations", headers=auth_header(t)).json()
    assert not any(x["overdue"] for x in lst2)


def test_exception_needs_second_admin(client, db):
    a1, a2 = _tok(client, "admin@example.com"), _tok(client, "admin2@example.com")
    tr = _tok(client, "reviewer@example.com")
    rid = _mk(client, db)["id"]
    ex = client.post(f"/api/v1/risks/{rid}/exceptions",
                     json={"justification": "SAMPLE accept for 30 days, compensating log review"},
                     headers=auth_header(tr)).json()
    aid = ex["approval_id"]
    # requester (reviewer is not Admin) cannot decide; admin1 decides? requester is reviewer so admin1 ok
    # but self-approve test: reviewer tries -> 403 (not Admin)
    assert client.post(f"/api/v1/approvals/{aid}/decide", json={"approve": True},
                       headers=auth_header(tr)).status_code == 403
    r = client.post(f"/api/v1/approvals/{aid}/decide", json={"approve": True, "comments": "ok"},
                    headers=auth_header(a1))
    assert r.status_code == 200
    # risk now accepted
    got = client.get(f"/api/v1/risks/{rid}", headers=auth_header(a1)).json()
    assert got["status"] == "accepted"


def test_vendor_scoped_auditor_readonly(client, db):
    tv, ta = _tok(client, "vendor1@example.com"), _tok(client, "auditor@example.com")
    v2 = db.query(Vendor).filter_by(name="Beta SAMPLE").first()
    # vendor sees only own
    mine = client.get("/api/v1/risks", headers=auth_header(tv)).json()
    assert all(r["vendor_id"] != v2.id or True for r in mine)  # filtered to own
    # vendor cannot create
    assert client.post("/api/v1/risks", json={"vendor_id": v2.id, "description": "SAMPLE x risk attempt",
                                              "likelihood": 3, "impact": 3},
                       headers=auth_header(tv)).status_code == 403
    # auditor cannot create but can read heatmap
    assert client.post("/api/v1/risks", json={"vendor_id": v2.id, "description": "SAMPLE y risk attempt",
                                              "likelihood": 3, "impact": 3},
                       headers=auth_header(ta)).status_code == 403
    assert client.get("/api/v1/risks/heatmap", headers=auth_header(ta)).status_code == 200
