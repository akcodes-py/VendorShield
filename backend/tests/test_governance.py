"""Governance tests. WHY: version history + coverage math + BCP gaps + ITGC guards."""
from datetime import date, timedelta

from tests.conftest import auth_header, login
from app.models.vendor import Vendor


def _tok(client, email):
    return login(client, email).json()["access_token"]


def test_policy_version_history_and_approval(client):
    tr, ta, tv = _tok(client, "reviewer@example.com"), _tok(client, "admin@example.com"), _tok(client, "vendor1@example.com")
    # vendor blocked from policies
    assert client.get("/api/v1/policies", headers=auth_header(tv)).status_code == 403
    # reviewer creates
    p = client.post("/api/v1/policies", json={"title": "TPRM SAMPLE", "content": "short sample policy v1 content here"},
                    headers=auth_header(tr))
    assert p.status_code == 201
    pid = p.json()["id"]
    assert len(client.get(f"/api/v1/policies/{pid}/versions", headers=auth_header(tr)).json()) == 1
    # reviewer cannot Approve, only Pending
    assert client.patch(f"/api/v1/policies/{pid}", json={"approval_status": "Approved"},
                        headers=auth_header(tr)).status_code == 403
    assert client.patch(f"/api/v1/policies/{pid}", json={"approval_status": "Pending"},
                        headers=auth_header(tr)).status_code == 200
    # admin approves + new version bumps latest
    assert client.patch(f"/api/v1/policies/{pid}", json={"approval_status": "Approved"},
                        headers=auth_header(ta)).status_code == 200
    v2 = client.post(f"/api/v1/policies/{pid}/versions",
                     json={"version": "2.0", "content": "updated sample content v2 longer text"},
                     headers=auth_header(ta))
    assert v2.status_code == 201
    assert client.get(f"/api/v1/policies/{pid}", headers=auth_header(ta)).json()["version"] == "2.0"


def test_framework_coverage(client, db):
    from app.models.policy import FrameworkControl
    from app.models.assessment import Question
    tr = _tok(client, "reviewer@example.com")
    # seed 2 ISO controls directly (no POST endpoint by design)
    db.add_all([FrameworkControl(framework="ISO27001", control_id="A.5.15", title="Access"),
                FrameworkControl(framework="ISO27001", control_id="A.8.24", title="Crypto")])
    db.commit()
    ctrls = client.get("/api/v1/frameworks/controls?framework=ISO27001", headers=auth_header(tr)).json()
    assert len(ctrls) == 2
    cov0 = client.get("/api/v1/frameworks/coverage?framework=ISO27001", headers=auth_header(tr)).json()
    assert cov0["coverage_pct"] == 0.0
    q = db.query(Question).first()
    assert client.post("/api/v1/frameworks/map", json={"question_id": q.id, "control_id": ctrls[0]["id"]},
                       headers=auth_header(tr)).status_code == 201
    cov1 = client.get("/api/v1/frameworks/coverage?framework=ISO27001", headers=auth_header(tr)).json()
    assert cov1["coverage_pct"] == 50.0
    assert ctrls[1]["control_id"] in cov1["unmapped"]


def test_bcp_gaps_and_update(client, db):
    tr, tv = _tok(client, "reviewer@example.com"), _tok(client, "vendor1@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    v2 = db.query(Vendor).filter_by(name="Beta SAMPLE").first()
    # Acme tier1 with no continuity row -> gap
    gaps = client.get("/api/v1/continuity/report/gaps", headers=auth_header(tr)).json()
    assert any(g["vendor_id"] == v.id for g in gaps)
    # vendor sees own but not other's
    assert client.get(f"/api/v1/continuity/{v.id}", headers=auth_header(tv)).status_code == 200
    assert client.get(f"/api/v1/continuity/{v2.id}", headers=auth_header(tv)).status_code == 403
    # reviewer adds tested plan + exit -> gap clears
    up = client.put(f"/api/v1/continuity/{v.id}",
                    json={"rto_hours": 24, "rpo_hours": 12, "plan_available": True,
                          "last_test_date": str(date.today()), "exit_plan": True},
                    headers=auth_header(tr))
    assert up.status_code == 200
    gaps2 = client.get("/api/v1/continuity/report/gaps", headers=auth_header(tr)).json()
    assert not any(g["vendor_id"] == v.id for g in gaps2)
    # stale test (>1yr) reappears as gap
    client.put(f"/api/v1/continuity/{v.id}",
               json={"rto_hours": 24, "rpo_hours": 12, "plan_available": True,
                     "last_test_date": str(date.today() - timedelta(days=400)), "exit_plan": True},
               headers=auth_header(tr))
    gaps3 = client.get("/api/v1/continuity/report/gaps", headers=auth_header(tr)).json()
    assert any(g["vendor_id"] == v.id for g in gaps3)


def test_itgc_evidence_and_config_log(client):
    tr, ta, tv = _tok(client, "reviewer@example.com"), _tok(client, "admin@example.com"), _tok(client, "vendor1@example.com")
    assert client.get("/api/v1/itgc", headers=auth_header(tv)).status_code == 403
    # Pass without evidence blocked
    bad = client.post("/api/v1/itgc", json={"domain": "access", "control": "SAMPLE quarterly review",
                                            "evidence": "", "status": "Pass"}, headers=auth_header(tr))
    assert bad.status_code == 422
    good = client.post("/api/v1/itgc", json={"domain": "access", "control": "SAMPLE quarterly review",
                                              "evidence": "ticket-123 SAMPLE", "status": "Pass"},
                       headers=auth_header(tr))
    assert good.status_code == 201
    # config change: admin only
    assert client.post("/api/v1/config-changes", json={"change": "SAMPLE rotate JWT secret"},
                       headers=auth_header(tr)).status_code == 403
    assert client.post("/api/v1/config-changes", json={"change": "SAMPLE rotate JWT secret"},
                       headers=auth_header(ta)).status_code == 201
    assert len(client.get("/api/v1/config-changes", headers=auth_header(ta)).json()) >= 1
