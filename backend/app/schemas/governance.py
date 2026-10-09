"""Governance schemas. WHY: version + approval enums stop free-text chaos."""
from datetime import date

from pydantic import BaseModel, Field


class PolicyCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    owner: str = ""
    review_date: date | None = None
    content: str = Field(default="", max_length=20000)


class PolicyUpdate(BaseModel):
    approval_status: str = Field(pattern="^(Draft|Pending|Approved|Rejected)$")
    review_date: date | None = None


class VersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=10, max_length=20000)


class MapIn(BaseModel):
    question_id: int
    control_id: int


class ContinuityUpdate(BaseModel):
    rto_hours: int = Field(ge=0, le=8760)
    rpo_hours: int = Field(ge=0, le=8760)
    plan_available: bool
    last_test_date: date | None = None
    exit_plan: bool


class ITGCCreate(BaseModel):
    domain: str = Field(pattern="^(access|change|operations)$")
    control: str = Field(min_length=5)
    evidence: str = ""
    status: str = Field(default="Fail", pattern="^(Pass|Fail)$")


class ITGCUpdate(BaseModel):
    evidence: str | None = None
    status: str | None = Field(default=None, pattern="^(Pass|Fail)$")


class ConfigCreate(BaseModel):
    change: str = Field(min_length=5, max_length=5000)
