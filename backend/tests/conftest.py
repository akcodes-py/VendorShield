"""Pytest fixtures. WHY: SQLite memory + StaticPool = fast, isolated per test."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import rate_limit
from app.core.security import hash_password
from app.db.base import Base
import app.models  # noqa: F401
from app.db.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture()
def db():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(eng)
    S = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    s = S()
    # WHY: one user per role + 2nd admin for SoD tests.
    s.add_all([
        User(email="admin@example.com", password_hash=hash_password("Password123!"), role="Admin"),
        User(email="admin2@example.com", password_hash=hash_password("Password123!"), role="Admin"),
        User(email="reviewer@example.com", password_hash=hash_password("Password123!"), role="Reviewer"),
        User(email="auditor@example.com", password_hash=hash_password("Password123!"), role="Auditor"),
        User(email="vendor1@example.com", password_hash=hash_password("Password123!"), role="Vendor", vendor_id=None),
    ])
    s.commit()
    # WHY: minimal vendors + questions so Phase 3 tests run without full seed.
    from datetime import date
    from app.models.vendor import Vendor
    from app.models.assessment import Question
    v1 = Vendor(name="Acme SAMPLE", service_type="Cloud", data_access="High", tier=1,
                lifecycle="Onboarding", onboarding_date=date.today(), freq_months=6)
    v2 = Vendor(name="Beta SAMPLE", service_type="Payroll", data_access="Low", tier=3,
                lifecycle="Approved", onboarding_date=date.today(), freq_months=24)
    s.add_all([v1, v2])
    s.flush()
    # link vendor user to v1 for scoping tests
    s.query(User).filter_by(email="vendor1@example.com").first().vendor_id = v1.id
    s.add_all([
        Question(domain="Access Control", text="SAMPLE Q1 MFA?", weight=3.0),
        Question(domain="Access Control", text="SAMPLE Q2 reviews?", weight=1.0),
        Question(domain="Encryption", text="SAMPLE Q3 at rest?", weight=2.0),
    ])
    s.commit()
    rate_limit.reset_for_tests()
    yield s
    s.close()


@pytest.fixture()
def client(db):
    def _override():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()
    rate_limit.reset_for_tests()


def login(client: TestClient, email: str, password: str = "Password123!", code: str | None = None):
    body = {"email": email, "password": password}
    if code:
        body["totp_code"] = code
    return client.post("/api/v1/auth/login", json=body)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
