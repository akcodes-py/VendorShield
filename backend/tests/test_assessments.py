"""Assessment tests. WHY: scoring + evidence rule + Vendor SoD."""
from tests.conftest import auth_header, login
from app.models.assessment import Question
from app.models.vendor import Vendor


def _tok(client, email):
    return login(client, email).json()["access_token"]


def _make_assessment(client, db):
    tr = _tok(client, "reviewer@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    r = client.post(f"/api/v1/vendors/{v.id}/assessments", headers=auth_header(tr))
    assert r.status_code == 201
    return r.json()["id"]


def test_questions_listed(client):
    t = _tok(client, "reviewer@example.com")
    r = client.get("/api/v1/questions", headers=auth_header(t))
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_evidence_required_for_no(client, db):
    tr = _tok(client, "reviewer@example.com")
    aid = _make_assessment(client, db)
    q = db.query(Question).first()
    r = client.put(f"/api/v1/assessments/{aid}/answers",
                   json={"answers": [{"question_id": q.id, "value": "No", "evidence": ""}]},
                   headers=auth_header(tr))
    assert r.status_code == 422  # WHY: unauditable answer rejected


def test_scoring_and_remediation(client, db):
    tr = _tok(client, "reviewer@example.com")
    aid = _make_assessment(client, db)
    qs = db.query(Question).order_by(Question.id).all()
    # Q1 Yes(3.0), Q2 No(1.0), Q3 Partial(2.0) => (3 + 0 + 1)/6 = 66.67 Medium
    body = {"answers": [
        {"question_id": qs[0].id, "value": "Yes", "evidence": ""},
        {"question_id": qs[1].id, "value": "No", "evidence": "no reviews SAMPLE"},
        {"question_id": qs[2].id, "value": "Partial", "evidence": "some TLS SAMPLE"},
    ]}
    assert client.put(f"/api/v1/assessments/{aid}/answers", json=body, headers=auth_header(tr)).status_code == 200
    s = client.post(f"/api/v1/assessments/{aid}/submit", headers=auth_header(tr))
    assert s.status_code == 200
    data = s.json()
    assert data["overall_score"] == 66.67
    assert data["risk_level"] == "Medium"
    assert "Access Control" in data["domain_scores"]
    assert len(data["failed_controls"]) == 1
    assert any("Access Control" in x for x in data["remediation"])


def test_vendor_can_answer_own_but_not_submit(client, db):
    tv = _tok(client, "vendor1@example.com")
    tr = _tok(client, "reviewer@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    aid = _make_assessment(client, db)
    q = db.query(Question).first()
    # Vendor answers own -> allowed
    r = client.put(f"/api/v1/assessments/{aid}/answers",
                   json={"answers": [{"question_id": q.id, "value": "Yes", "evidence": ""}]},
                   headers=auth_header(tv))
    assert r.status_code == 200
    # Vendor submit -> forbidden (Reviewer rates)
    assert client.post(f"/api/v1/assessments/{aid}/submit", headers=auth_header(tv)).status_code == 403
    # Vendor cannot touch other's vendor assessment
    v2 = db.query(Vendor).filter_by(name="Beta SAMPLE").first()
    a2 = client.post(f"/api/v1/vendors/{v2.id}/assessments", headers=auth_header(tr)).json()["id"]
    r2 = client.put(f"/api/v1/assessments/{a2}/answers",
                    json={"answers": [{"question_id": q.id, "value": "Yes", "evidence": ""}]},
                    headers=auth_header(tv))
    assert r2.status_code == 403


def test_sql_injection_blocked_by_orm(client, db):
    # WHY: ORM only - raw payload stored as string, never executed.
    t = _tok(client, "reviewer@example.com")
    r = client.post("/api/v1/vendors", json={"name": "x'; DROP TABLE vendors;--",
                                             "service_type": "Cloud", "tier": 2},
                    headers=auth_header(t))
    assert r.status_code == 201
    from app.models.vendor import Vendor as V
    assert db.query(V).count() >= 3  # table still alive
