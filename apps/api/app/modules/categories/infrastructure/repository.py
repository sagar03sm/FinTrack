"""Beanie/Mongo implementation of CategoryRepository."""

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.core.errors import ConflictError
from app.modules.categories.infrastructure.models import Category, CategoryType


class MongoCategoryRepository:
    async def list_for_user(
        self, user_id: PydanticObjectId, type_: CategoryType | None = None
    ) -> list[Category]:
        query = Category.find(Category.user_id == user_id)
        if type_ is not None:
            query = query.find(Category.type == type_)
        return await query.sort("+name").to_list()

    async def get(
        self, user_id: PydanticObjectId, category_id: PydanticObjectId
    ) -> Category | None:
        cat = await Category.get(category_id)
        if cat is None or cat.user_id != user_id:
            return None
        return cat

    async def create(self, category: Category) -> Category:
        try:
            await category.insert()
        except DuplicateKeyError as e:
            raise ConflictError("Category with this name already exists") from e
        return category

    async def update(self, category: Category) -> Category:
        try:
            await category.save()
        except DuplicateKeyError as e:
            raise ConflictError("Category with this name already exists") from e
        return category

    async def delete(self, category: Category) -> None:
        await category.delete()
