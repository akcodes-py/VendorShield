"""Users + roles. WHY: least-privilege starts here; Vendor role scoped by vendor_id."""
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # WHY: unique email prevents duplicate accounts.
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Admin | Reviewer | Auditor | Vendor
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="Reviewer")
    # WHY: Vendor users see only their own vendor. NULL for staff.
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|revoked
