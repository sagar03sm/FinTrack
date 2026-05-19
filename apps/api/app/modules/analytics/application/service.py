"""AnalyticsService — Mongo aggregations for summary, breakdowns, trends, budget progress."""

from datetime import datetime

from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.modules.analytics.application.dtos import (
    BudgetProgress,
    CategoryBreakdown,
    MonthlyTrend,
    SummaryStat,
)
from app.modules.budgets.infrastructure.models import Budget
from app.modules.transactions.infrastructure.models import Transaction, TransactionType


class AnalyticsService:
    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None

    async def _db(self):
        settings = get_settings()
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.mongo_uri)
        return self._client[settings.mongo_db]

    async def summary(
        self, user_id: PydanticObjectId, date_from: datetime, date_to: datetime
    ) -> SummaryStat:
        db = await self._db()
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "date": {"$gte": date_from, "$lte": date_to},
                }
            },
            {
                "$group": {
                    "_id": "$type",
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1},
                }
            },
        ]
        results = await db.transactions.aggregate(pipeline).to_list(None)
        income = next((r["total"] for r in results if r["_id"] == "income"), 0.0)
        expense = next((r["total"] for r in results if r["_id"] == "expense"), 0.0)
        total_tx = sum(r["count"] for r in results)
        return SummaryStat(
            total_income=income,
            total_expense=expense,
            net=income - expense,
            transaction_count=total_tx,
        )

    async def by_category(
        self, user_id: PydanticObjectId, date_from: datetime, date_to: datetime
    ) -> list[CategoryBreakdown]:
        db = await self._db()
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "date": {"$gte": date_from, "$lte": date_to},
                }
            },
            {
                "$group": {
                    "_id": {"category_id": "$category_id", "category_name": "$category_name", "type": "$type"},
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "category_id": "$_id.category_id",
                    "category_name": "$_id.category_name",
                    "type": "$_id.type",
                    "total": 1,
                    "count": 1,
                    "_id": 0,
                }
            },
            {"$sort": {"total": -1}},
        ]
        results = await db.transactions.aggregate(pipeline).to_list(None)
        return [
            CategoryBreakdown(
                category_id=str(r["category_id"]),
                category_name=r["category_name"],
                type=r["type"],
                total=r["total"],
                count=r["count"],
            )
            for r in results
        ]

    async def monthly_trend(
        self, user_id: PydanticObjectId, months: int = 6
    ) -> list[MonthlyTrend]:
        db = await self._db()
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                }
            },
            {
                "$addFields": {
                    "month": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}
                }
            },
            {
                "$group": {
                    "_id": {"month": "$month", "type": "$type"},
                    "total": {"$sum": "$amount"},
                }
            },
            {
                "$group": {
                    "_id": "$_id.month",
                    "income": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$_id.type", "income"]},
                                "$total",
                                0,
                            ]
                        }
                    },
                    "expense": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$_id.type", "expense"]},
                                "$total",
                                0,
                            ]
                        }
                    },
                }
            },
            {"$sort": {"_id": -1}},
            {"$limit": months},
        ]
        results = await db.transactions.aggregate(pipeline).to_list(None)
        return [
            MonthlyTrend(
                month=r["_id"],
                income=r.get("income", 0.0),
                expense=r.get("expense", 0.0),
                net=r.get("income", 0.0) - r.get("expense", 0.0),
            )
            for r in results
        ]

    async def budget_progress(
        self, user_id: PydanticObjectId, month: str
    ) -> list[BudgetProgress]:
        # Fetch budgets for the month
        budgets = await Budget.find(
            Budget.user_id == user_id, Budget.month == month
        ).to_list()

        if not budgets:
            return []

        # Aggregate spending per category for the month
        db = await self._db()
        # Parse month to date range
        year, mon = month.split("-")
        date_from = datetime(int(year), int(mon), 1)
        # Last day of month
        if mon == "12":
            date_to = datetime(int(year) + 1, 1, 1)
        else:
            date_to = datetime(int(year), int(mon) + 1, 1)

        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "date": {"$gte": date_from, "$lt": date_to},
                }
            },
            {
                "$group": {
                    "_id": "$category_id",
                    "spent": {"$sum": "$amount"},
                }
            },
        ]
        spent_by_cat = {
            str(r["_id"]): r["spent"] for r in await db.transactions.aggregate(pipeline).to_list(None)
        }

        progress = []
        for b in budgets:
            spent = spent_by_cat.get(str(b.category_id), 0.0)
            remaining = b.limit - spent
            pct = (spent / b.limit) * 100 if b.limit > 0 else 0.0
            progress.append(
                BudgetProgress(
                    category_id=str(b.category_id),
                    category_name="",  # could join with Category if needed
                    limit=b.limit,
                    spent=spent,
                    remaining=remaining,
                    percent=pct,
                )
            )
        return progress
