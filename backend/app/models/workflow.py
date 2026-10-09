"""Approvals. WHY: onboarding + privileged actions need 2nd person check."""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # vendor|exception|role_change|delete
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision: Mapped[str] = mapped_column(String(20), default="Pending")  # Pending|Approved|Rejected
    comments: Mapped[str] = mapped_column(Text, default="")
