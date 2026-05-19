from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, status

from app.modules.auth.interfaces.http.deps import get_current_user
from app.modules.budgets.application.dtos import BudgetOut, BudgetUpsert
from app.modules.budgets.application.service import BudgetService
from app.modules.budgets.domain.repository import BudgetRepository
from app.modules.categories.domain.repository import CategoryRepository
from app.modules.budgets.infrastructure.repository import MongoBudgetRepository
from app.modules.categories.infrastructure.repository import MongoCategoryRepository
from app.modules.users.infrastructure.models import User

router = APIRouter(prefix="/budgets", tags=["budgets"])


def get_budget_repository() -> BudgetRepository:
    return MongoBudgetRepository()


def get_category_repository() -> CategoryRepository:
    return MongoCategoryRepository()


def get_budget_service(
    budgets: BudgetRepository = Depends(get_budget_repository),
    categories: CategoryRepository = Depends(get_category_repository),
) -> BudgetService:
    return BudgetService(budgets=budgets, categories=categories)


@router.get("", response_model=list[BudgetOut])
async def list_budgets(
    month: str = Query(..., description="Month in YYYY-MM format"),
    user: User = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
) -> list[BudgetOut]:
    return await service.list(user.id, month)


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def upsert_budget(
    body: BudgetUpsert,
    user: User = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
) -> BudgetOut:
    return await service.upsert(user.id, body)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: PydanticObjectId,
    user: User = Depends(get_current_user),
    service: BudgetService = Depends(get_budget_service),
) -> None:
    await service.delete(user.id, budget_id)
