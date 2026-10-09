"""Risks + remediations + exceptions. WHY: 1-5 likelihood x impact = inherent score."""
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(30), default="cyber")
    likelihood: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    impact: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    inherent_score: Mapped[int] = mapped_column(Integer, default=9)
    controls: Mapped[str] = mapped_column(Text, default="")
    residual_score: Mapped[int] = mapped_column(Integer, default=9)
    owner: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|mitigating|closed|accepted
    due_date: Mapped[Date | None] = mapped_column(Date, nullable=True)


class Remediation(Base):
    __tablename__ = "remediations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    risk_id: Mapped[int] = mapped_column(ForeignKey("risks.id"), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(255), default="")
    due_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|done|overdue


class RiskException(Base):
    """WHY: accepting risk needs expiry + approval, never silent."""
    __tablename__ = "exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    risk_id: Mapped[int] = mapped_column(ForeignKey("risks.id"), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    expiry_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Pending")
