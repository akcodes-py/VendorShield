"""Continuity per vendor. WHY: RTO/RPO prove exit plan exists for critical vendors."""
from sqlalchemy import Boolean, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Continuity(Base):
    __tablename__ = "continuity"

    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), primary_key=True)
    rto_hours: Mapped[int] = mapped_column(Integer, default=24)
    rpo_hours: Mapped[int] = mapped_column(Integer, default=24)
    plan_available: Mapped[bool] = mapped_column(Boolean, default=False)
    last_test_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    exit_plan: Mapped[bool] = mapped_column(Boolean, default=False)
