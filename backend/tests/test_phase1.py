"""Phase 1 smoke tests on SQLite memory. WHY: fast, no Postgres needed."""
from sqlalchemy.orm import Session

from app.db.base import Base
import app.models  # noqa: F401 -- WHY: registers tables
from app.db.session import make_engine
from app.services.scoring import weighted_score, level_for, tier_frequency


def test_scoring_formula():
    assert weighted_score([(3.0, "Yes"), (1.0, "No")]) == 75.0
    assert weighted_score([(1.0, "N/A")]) == 0.0
    assert level_for(90) == "Low"
    assert level_for(70) == "Medium"
    assert level_for(50) == "High"
    assert level_for(10) == "Critical"


def test_tier_frequency():
    assert tier_frequency(1) == 6
    assert tier_frequency(2) == 12
    assert tier_frequency(3) == 24


def test_tables_exist():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    # WHY: proves all models import without FK errors.
    assert "vendors" in Base.metadata.tables
    assert "users" in Base.metadata.tables
    assert "risks" in Base.metadata.tables
    assert "documents" in Base.metadata.tables
    assert "audit_logs" in Base.metadata.tables


def test_seed_creates_12_vendors(tmp_path):
    # WHY: file DB so seed + assert share same data (memory DBs don't share).
    from app.db.seed import run
    from app.models.vendor import Vendor
    from app.models.user import User

    url = f"sqlite:///{tmp_path}/seed_test.db"
    run(url)
    eng = make_engine(url)
    with Session(eng) as db:
        assert db.query(Vendor).count() == 12
        assert db.query(User).count() == 4  # admin, reviewer, auditor, vendor1
        assert db.query(Vendor).filter_by(tier=1).count() == 5
