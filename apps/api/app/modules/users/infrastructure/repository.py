"""MongoDB implementation of UserRepository (Beanie-backed)."""

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.core.errors import ConflictError
from app.modules.users.infrastructure.models import User


class MongoUserRepository:
    """Beanie-backed implementation of `UserRepository`."""

    async def get_by_id(self, user_id: PydanticObjectId) -> User | None:
        return await User.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await User.find_one(User.email == email.lower())

    async def create(self, user: User) -> User:
        try:
            await user.insert()
        except DuplicateKeyError as e:
            raise ConflictError("Email already registered") from e
        return user
