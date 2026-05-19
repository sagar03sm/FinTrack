from datetime import datetime, timezone

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field


class Budget(Document):
    user_id: PydanticObjectId
    category_id: PydanticObjectId
    month: str  # "YYYY-MM"
    limit: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "budgets"
        indexes = [
            pymongo.IndexModel(
                [
                    ("user_id", pymongo.ASCENDING),
                    ("month", pymongo.ASCENDING),
                    ("category_id", pymongo.ASCENDING),
                ],
                unique=True,
            ),
        ]
