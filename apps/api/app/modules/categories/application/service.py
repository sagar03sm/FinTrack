"""CategoryService — list/create/update/delete with deletion safety."""

from beanie import PydanticObjectId

from app.core.errors import ConflictError, NotFoundError
from app.modules.categories.application.dtos import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
)
from app.modules.categories.domain.repository import CategoryRepository
from app.modules.categories.infrastructure.models import Category, CategoryType
from app.modules.transactions.infrastructure.models import Transaction


def _to_out(c: Category) -> CategoryOut:
    return CategoryOut(
        id=str(c.id),
        name=c.name,
        type=c.type,
        color=c.color,
        created_at=c.created_at,
    )


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def list(
        self, user_id: PydanticObjectId, type_: CategoryType | None = None
    ) -> list[CategoryOut]:
        cats = await self._repo.list_for_user(user_id, type_)
        return [_to_out(c) for c in cats]

    async def create(
        self, user_id: PydanticObjectId, body: CategoryCreate
    ) -> CategoryOut:
        cat = Category(
            user_id=user_id,
            name=body.name,
            type=body.type,
            color=body.color,
        )
        await self._repo.create(cat)
        return _to_out(cat)

    async def update(
        self,
        user_id: PydanticObjectId,
        category_id: PydanticObjectId,
        body: CategoryUpdate,
    ) -> CategoryOut:
        cat = await self._repo.get(user_id, category_id)
        if cat is None:
            raise NotFoundError("Category not found")
        if body.name is not None:
            cat.name = body.name
        if body.color is not None:
            cat.color = body.color
        await self._repo.update(cat)
        return _to_out(cat)

    async def delete(
        self, user_id: PydanticObjectId, category_id: PydanticObjectId
    ) -> None:
        cat = await self._repo.get(user_id, category_id)
        if cat is None:
            raise NotFoundError("Category not found")
        # Refuse delete if any transactions still reference this category.
        in_use = await Transaction.find(
            Transaction.user_id == user_id, Transaction.category_id == category_id
        ).count()
        if in_use:
            raise ConflictError(
                f"Category is used by {in_use} transaction(s); "
                "reassign or delete them first"
            )
        await self._repo.delete(cat)
