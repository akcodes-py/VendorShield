"""Audit log. WHY: append-only - never update/delete, proves who did what."""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create|update|delete|login
    entity_type: Mapped[str] = mapped_column(String(50), default="")
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip: Mapped[str] = mapped_column(String(50), default="")
    diff_json: Mapped[str] = mapped_column(Text, default="{}")  # old vs new values
