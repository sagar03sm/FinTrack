from typing import Protocol

from beanie import PydanticObjectId

from app.modules.budgets.infrastructure.models import Budget


class BudgetRepository(Protocol):
    async def list_for_month(
        self, user_id: PydanticObjectId, month: str
    ) -> list[Budget]: ...

    async def get_for_category(
        self, user_id: PydanticObjectId, month: str, category_id: PydanticObjectId
    ) -> Budget | None: ...

    async def get(
        self, user_id: PydanticObjectId, budget_id: PydanticObjectId
    ) -> Budget | None: ...

    async def upsert(
        self,
        user_id: PydanticObjectId,
        month: str,
        category_id: PydanticObjectId,
        limit: float,
    ) -> Budget: ...

    async def delete(self, budget: Budget) -> None: ...
