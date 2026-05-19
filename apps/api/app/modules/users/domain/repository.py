"""Domain port for user persistence. Pure — no Beanie/Motor imports."""

from typing import Protocol

from beanie import PydanticObjectId

from app.modules.users.infrastructure.models import User


class UserRepository(Protocol):
    """Storage abstraction for User aggregates.

    NOTE: We treat the Beanie `User` Document as the entity (pragmatic choice).
    The domain layer references it via this Protocol so application services
    remain testable with in-memory fakes.
    """

    async def get_by_id(self, user_id: PydanticObjectId) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def create(self, user: User) -> User: ...
