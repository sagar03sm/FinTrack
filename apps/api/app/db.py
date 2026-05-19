"""Mongo client + Beanie ODM bootstrap."""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: AsyncIOMotorClient | None = None


def _collect_document_models() -> list:
    """Aggregate all Beanie Documents from each module's infrastructure layer.

    Importing these here keeps `core` and `application` layers free of any
    Beanie/Motor coupling.
    """
    from app.modules.budgets.infrastructure.models import Budget
    from app.modules.categories.infrastructure.models import Category
    from app.modules.chat.infrastructure.models import ChatMessage, ChatSession
    from app.modules.transactions.infrastructure.models import Transaction
    from app.modules.users.infrastructure.models import User

    return [User, Category, Transaction, Budget, ChatSession, ChatMessage]


async def init_db() -> None:
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongo_uri)
    db = _client[settings.mongo_db]
    await init_beanie(database=db, document_models=_collect_document_models())
    logger.info("db_initialized", db=settings.mongo_db)


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ping_db() -> bool:
    if _client is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        return False
