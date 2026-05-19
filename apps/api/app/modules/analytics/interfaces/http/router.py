from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query

from app.modules.analytics.application.dtos import (
    BudgetProgress,
    CategoryBreakdown,
    MonthlyTrend,
    SummaryStat,
)
from app.modules.analytics.application.service import AnalyticsService
from app.modules.auth.interfaces.http.deps import get_current_user
from app.modules.users.infrastructure.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


@router.get("/summary", response_model=SummaryStat)
async def summary(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> SummaryStat:
    return await service.summary(user.id, date_from, date_to)


@router.get("/by-category", response_model=list[CategoryBreakdown])
async def by_category(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[CategoryBreakdown]:
    return await service.by_category(user.id, date_from, date_to)


@router.get("/monthly-trend", response_model=list[MonthlyTrend])
async def monthly_trend(
    months: int = Query(default=6, ge=1, le=24),
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[MonthlyTrend]:
    return await service.monthly_trend(user.id, months)


@router.get("/budget-progress", response_model=list[BudgetProgress])
async def budget_progress(
    month: str = Query(..., description="Month in YYYY-MM format"),
    user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[BudgetProgress]:
    return await service.budget_progress(user.id, month)
