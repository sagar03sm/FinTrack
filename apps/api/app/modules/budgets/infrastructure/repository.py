from beanie import PydanticObjectId

from app.modules.budgets.infrastructure.models import Budget


class MongoBudgetRepository:
    async def list_for_month(
        self, user_id: PydanticObjectId, month: str
    ) -> list[Budget]:
        return await Budget.find(
            Budget.user_id == user_id, Budget.month == month
        ).to_list()

    async def get_for_category(
        self, user_id: PydanticObjectId, month: str, category_id: PydanticObjectId
    ) -> Budget | None:
        return await Budget.find_one(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.category_id == category_id,
        )

    async def get(
        self, user_id: PydanticObjectId, budget_id: PydanticObjectId
    ) -> Budget | None:
        b = await Budget.get(budget_id)
        if b is None or b.user_id != user_id:
            return None
        return b

    async def upsert(
        self,
        user_id: PydanticObjectId,
        month: str,
        category_id: PydanticObjectId,
        limit: float,
    ) -> Budget:
        existing = await self.get_for_category(user_id, month, category_id)
        if existing is not None:
            existing.limit = limit
            await existing.save()
            return existing
        b = Budget(user_id=user_id, month=month, category_id=category_id, limit=limit)
        await b.insert()
        return b

    async def delete(self, budget: Budget) -> None:
        await budget.delete()
