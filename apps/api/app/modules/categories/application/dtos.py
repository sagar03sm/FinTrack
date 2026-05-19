from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.categories.infrastructure.models import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    type: CategoryType
    color: str | None = Field(default=None, max_length=20)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    color: str | None = Field(default=None, max_length=20)


class CategoryOut(BaseModel):
    id: str
    name: str
    type: CategoryType
    color: str | None
    created_at: datetime
