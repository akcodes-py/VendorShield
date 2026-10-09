"""SOC tables. WHY: events are facts, alerts are rule outputs, incidents have lifecycle."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _now():
    # WHY: naive UTC keeps SQLite + Postgres TIMESTAMP comparisons simple.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # failed_login|perm_denied|...
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    ip: Mapped[str] = mapped_column(String(50), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    is_sample: Mapped[int] = mapped_column(Integer, default=0)  # 1 = simulation SAMPLE
    # WHY: timestamp required for "5 in 5 min" window rules.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="Medium")
    status: Mapped[str] = mapped_column(String(20), default="New")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="Medium")
    # Detected|Triaged|Contained|Eradicated|Recovered|LessonsLearned
    status: Mapped[str] = mapped_column(String(20), default="Detected")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
