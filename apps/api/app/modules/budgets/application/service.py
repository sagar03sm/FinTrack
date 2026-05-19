from beanie import PydanticObjectId

from app.core.errors import NotFoundError, ValidationError
from app.modules.budgets.application.dtos import BudgetOut, BudgetUpsert
from app.modules.budgets.domain.repository import BudgetRepository
from app.modules.budgets.infrastructure.models import Budget
from app.modules.categories.domain.repository import CategoryRepository


def _to_out(b: Budget) -> BudgetOut:
    return BudgetOut(
        id=str(b.id),
        category_id=str(b.category_id),
        month=b.month,
        limit=b.limit,
        created_at=b.created_at,
    )


class BudgetService:
    def __init__(
        self,
        budgets: BudgetRepository,
        categories: CategoryRepository,
    ) -> None:
        self._budgets = budgets
        self._categories = categories

    async def list(self, user_id: PydanticObjectId, month: str) -> list[BudgetOut]:
        budgets = await self._budgets.list_for_month(user_id, month)
        return [_to_out(b) for b in budgets]

    async def upsert(self, user_id: PydanticObjectId, body: BudgetUpsert) -> BudgetOut:
        # Validate category ownership
        try:
            cid = PydanticObjectId(body.category_id)
        except Exception as e:
            raise ValidationError("Invalid category_id") from e
        cat = await self._categories.get(user_id, cid)
        if cat is None:
            raise NotFoundError("Category not found")
        b = await self._budgets.upsert(user_id, body.month, cid, body.limit)
        return _to_out(b)

    async def delete(
        self, user_id: PydanticObjectId, budget_id: PydanticObjectId
    ) -> None:
        b = await self._budgets.get(user_id, budget_id)
        if b is None:
            raise NotFoundError("Budget not found")
        await self._budgets.delete(b)
