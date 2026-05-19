from datetime import datetime, timezone
from enum import Enum

import pymongo
from beanie import Document
from pydantic import EmailStr, Field


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Document):
    email: EmailStr
    password_hash: str
    name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
        ]
