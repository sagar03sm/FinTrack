"""Domain port for category persistence."""

from typing import Protocol

from beanie import PydanticObjectId

from app.modules.categories.infrastructure.models import Category, CategoryType


class CategoryRepository(Protocol):
    async def list_for_user(
        self, user_id: PydanticObjectId, type_: CategoryType | None = None
    ) -> list[Category]: ...

    async def get(
        self, user_id: PydanticObjectId, category_id: PydanticObjectId
    ) -> Category | None: ...

    async def create(self, category: Category) -> Category: ...

    async def update(self, category: Category) -> Category: ...

    async def delete(self, category: Category) -> None: ...
