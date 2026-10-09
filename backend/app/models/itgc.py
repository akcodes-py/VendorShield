"""ITGC + config changes. WHY: auditors need pass/fail + evidence trail."""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ITGCCheck(Base):
    __tablename__ = "itgc_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)  # access|change|operations
    control: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="Fail")  # Pass|Fail


class ConfigChange(Base):
    __tablename__ = "config_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    change: Mapped[str] = mapped_column(Text, nullable=False)
