from datetime import datetime, timezone
from enum import Enum

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Category(Document):
    user_id: PydanticObjectId
    name: str
    type: CategoryType
    color: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "categories"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("name", pymongo.ASCENDING)],
                unique=True,
            ),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING), ("type", pymongo.ASCENDING)]),
        ]
