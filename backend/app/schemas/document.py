"""Document schemas. WHY: strict enums stop bad doc_type/status."""
from datetime import date

from pydantic import BaseModel, Field


class ReviewIn(BaseModel):
    review_status: str = Field(pattern="^(Pending|Approved|Rejected|Expired)$")
    review_notes: str = ""
