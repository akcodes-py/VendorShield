"""Pydantic schemas. WHY: validation blocks bad input before DB (XSS/SQLi first layer)."""
from datetime import date

from pydantic import BaseModel, Field


class VendorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    service_type: str = Field(min_length=2, max_length=100)
    data_access: str = Field(default="Low", pattern="^(None|Low|Moderate|High)$")
    tier: int = Field(ge=1, le=3)
    contact_name: str = ""
    contact_email: str = ""


class VendorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    service_type: str | None = None
    data_access: str | None = Field(default=None, pattern="^(None|Low|Moderate|High)$")
    tier: int | None = Field(default=None, ge=1, le=3)
    contact_name: str | None = None
    contact_email: str | None = None


class VendorOut(VendorCreate):
    id: int
    lifecycle: str
    freq_months: int
    next_review_date: date | None = None

    model_config = {"from_attributes": True}


class TransitionIn(BaseModel):
    to: str = Field(pattern="^(Onboarding|Assessment|Approved|Rejected|Review|Offboarded)$")


class AnswerIn(BaseModel):
    question_id: int
    value: str = Field(pattern="^(Yes|Partial|No|N/A)$")
    evidence: str = ""


class AnswersIn(BaseModel):
    answers: list[AnswerIn]


class RiskCreate(BaseModel):
    vendor_id: int
    description: str = Field(min_length=5)
    category: str = Field(default="cyber")
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    controls: str = ""
    owner: str = ""
