from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.transactions.infrastructure.models import TransactionType


class TransactionCreate(BaseModel):
    type: TransactionType
    amount: float = Field(gt=0, le=10_000_000)  # Max 10 million INR
    currency: str = Field(default="INR", min_length=3, max_length=3)
    category_id: str
    note: str | None = Field(default=None, max_length=500)
    date: datetime


class TransactionUpdate(BaseModel):
    type: TransactionType | None = None
    amount: float | None = Field(default=None, gt=0, le=10_000_000)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    category_id: str | None = None
    note: str | None = Field(default=None, max_length=500)
    date: datetime | None = None


class TransactionOut(BaseModel):
    id: str
    type: TransactionType
    amount: float
    currency: str
    category_id: str
    category_name: str
    note: str | None
    date: datetime
    created_at: datetime


class TransactionListOut(BaseModel):
    items: list[TransactionOut]
    total: int
    limit: int
    skip: int
