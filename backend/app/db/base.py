"""WHY: single Base so Alembic autogenerate sees all tables."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
