"""Risk schemas. WHY: 1-5 bounds stop impossible LxI."""
from datetime import date

from pydantic import BaseModel, Field


class RiskCreate(BaseModel):
    vendor_id: int
    description: str = Field(min_length=5)
    category: str = Field(default="cyber", pattern="^(cyber|operational|compliance|financial)$")
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    controls: str = ""
    owner: str = ""
    due_date: date | None = None


class RiskUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=5)
    category: str | None = Field(default=None, pattern="^(cyber|operational|compliance|financial)$")
    likelihood: int | None = Field(default=None, ge=1, le=5)
    impact: int | None = Field(default=None, ge=1, le=5)
    controls: str | None = None
    residual_score: int | None = Field(default=None, ge=1, le=25)
    owner: str | None = None
    status: str | None = Field(default=None, pattern="^(open|mitigating|closed|accepted)$")
    due_date: date | None = None


class RemediationCreate(BaseModel):
    action: str = Field(min_length=5)
    owner: str = ""
    due_date: date | None = None


class RemediationUpdate(BaseModel):
    status: str = Field(pattern="^(open|done|overdue)$")
