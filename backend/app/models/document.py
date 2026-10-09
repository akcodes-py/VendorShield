"""Documents. WHY: store random filename, never original path (path traversal safe)."""
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False)  # ISO27001|SOC2|Policy|Pentest
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)  # random hex
    original_name: Mapped[str] = mapped_column(String(255), default="")
    mime: Mapped[str] = mapped_column(String(100), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    issue_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), default="Pending")
    review_notes: Mapped[str] = mapped_column(Text, default="")
    # WHY: AI output is draft only, reviewer must confirm.
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confirmed: Mapped[bool | None] = mapped_column(Integer, nullable=True, default=0)
