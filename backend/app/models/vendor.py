"""Vendors. WHY: tier drives assessment frequency (T1=6mo, T2=12mo, T3=24mo)."""
from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. Cloud, Payroll
    data_access: Mapped[str] = mapped_column(String(20), default="Low")  # None|Low|Moderate|High
    tier: Mapped[int] = mapped_column(Integer, default=3)  # 1|2|3, 1 = most critical
    contact_name: Mapped[str] = mapped_column(String(255), default="")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    # Onboarding|Assessment|Approved|Rejected|Review|Offboarded
    lifecycle: Mapped[str] = mapped_column(String(20), default="Onboarding")
    onboarding_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    next_review_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    freq_months: Mapped[int] = mapped_column(Integer, default=24)
