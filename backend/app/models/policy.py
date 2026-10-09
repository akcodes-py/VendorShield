"""Policy library + framework mapping. WHY: proves coverage vs ISO/NIST."""
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    owner: Mapped[str] = mapped_column(String(255), default="")
    approval_status: Mapped[str] = mapped_column(String(20), default="Draft")
    review_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    is_sample: Mapped[int] = mapped_column(Integer, default=0)  # 1 = template SAMPLE


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")


class FrameworkControl(Base):
    __tablename__ = "framework_controls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    framework: Mapped[str] = mapped_column(String(20), nullable=False)  # ISO27001|NISTCSF
    control_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="")


class QuestionControlMap(Base):
    __tablename__ = "question_control_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    control_id: Mapped[int] = mapped_column(ForeignKey("framework_controls.id"), nullable=False)
