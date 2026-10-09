"""Report tests. WHY: dashboard shape + PDFs are real PDFs + RBAC."""
from tests.conftest import auth_header, login


def _tok(client, email):
    return login(client, email).json()["access_token"]


def test_dashboard_shape(client):
    t = _tok(client, "reviewer@example.com")
    d = client.get("/api/v1/reports/dashboard", headers=auth_header(t)).json()
    for k in ("vendors_by_lifecycle", "vendors_by_risk_level", "open_risks_by_severity",
              "heatmap", "expiring_documents", "overdue_remediations",
              "top_5_riskiest", "assessment_completion_rate"):
        assert k in d
    assert isinstance(d["assessment_completion_rate"], (int, float))


def test_vendor_pdf_and_scoping(client, db):
    from app.models.vendor import Vendor
    tr, tv = _tok(client, "reviewer@example.com"), _tok(client, "vendor1@example.com")
    v = db.query(Vendor).filter_by(name="Acme SAMPLE").first()
    v2 = db.query(Vendor).filter_by(name="Beta SAMPLE").first()
    r = client.get(f"/api/v1/reports/vendor/{v.id}.pdf", headers=auth_header(tr))
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")  # WHY: proves real PDF, not JSON renamed
    # vendor own ok, other's blocked
    assert client.get(f"/api/v1/reports/vendor/{v.id}.pdf", headers=auth_header(tv)).status_code == 200
    assert client.get(f"/api/v1/reports/vendor/{v2.id}.pdf", headers=auth_header(tv)).status_code == 403


def test_executive_pdf_roles(client):
    tr, ta, tv = _tok(client, "reviewer@example.com"), _tok(client, "auditor@example.com"), _tok(client, "vendor1@example.com")
    for tok in (tr, ta):
        r = client.get("/api/v1/reports/executive.pdf", headers=auth_header(tok))
        assert r.status_code == 200 and r.content.startswith(b"%PDF")
    assert client.get("/api/v1/reports/executive.pdf", headers=auth_header(tv)).status_code == 403


def test_analysis_script_writes(tmp_path):
    # WHY: run analysis on temp SQLite seed - proves charts + insights without Postgres.
    from app.db.seed import run
    url = f"sqlite:///{tmp_path}/a.db"
    run(url)
    import scripts.analysis as az
    az.OUT = str(tmp_path)  # redirect outputs
    az.main(url)
    import os
    names = os.listdir(tmp_path)
    assert "insights.md" in names
    assert any(n.endswith(".png") for n in names)
