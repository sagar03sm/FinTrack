from datetime import datetime, timezone
from enum import Enum
from typing import Any

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatSession(Document):
    user_id: PydanticObjectId
    title: str = "New chat"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "chat_sessions"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("updated_at", pymongo.DESCENDING)]
            ),
        ]


class ChatMessage(Document):
    session_id: PydanticObjectId
    user_id: PydanticObjectId
    role: ChatRole
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "chat_messages"
        indexes = [
            pymongo.IndexModel(
                [("session_id", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)]
            ),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)]),
        ]
