"""DB session. WHY: one factory; tests override URL with SQLite memory."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def make_engine(url: str | None = None):
    db_url = url or settings.DATABASE_URL
    # WHY: SQLite needs check_same_thread=False for pytest + FastAPI TestClient.
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
