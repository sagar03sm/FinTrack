import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class BudgetUpsert(BaseModel):
    category_id: str
    month: str = Field(description="Month in YYYY-MM format")
    limit: float = Field(gt=0, le=100_000_000)  # Max 100 million INR

    @field_validator("month")
    @classmethod
    def _validate_month(cls, v: str) -> str:
        if not _MONTH_RE.match(v):
            raise ValueError("month must be in YYYY-MM format")
        return v


class BudgetOut(BaseModel):
    id: str
    category_id: str
    month: str
    limit: float
    created_at: datetime
