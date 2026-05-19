from datetime import datetime, timezone
from enum import Enum

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(Document):
    user_id: PydanticObjectId
    type: TransactionType
    amount: float  # store as float for now; consider Decimal128 in prod
    currency: str = "INR"
    category_id: PydanticObjectId
    category_name: str  # denormalized for fast reads / aggregations without $lookup
    note: str | None = None
    date: datetime  # the user-specified transaction date (UTC)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "transactions"
        indexes = [
            pymongo.IndexModel([("user_id", pymongo.ASCENDING), ("date", pymongo.DESCENDING)]),
            pymongo.IndexModel(
                [
                    ("user_id", pymongo.ASCENDING),
                    ("category_id", pymongo.ASCENDING),
                    ("date", pymongo.DESCENDING),
                ]
            ),
            pymongo.IndexModel(
                [
                    ("user_id", pymongo.ASCENDING),
                    ("type", pymongo.ASCENDING),
                    ("date", pymongo.DESCENDING),
                ]
            ),
        ]
