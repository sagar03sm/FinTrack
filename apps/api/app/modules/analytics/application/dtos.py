from datetime import datetime

from pydantic import BaseModel


class SummaryStat(BaseModel):
    total_income: float
    total_expense: float
    net: float
    transaction_count: int


class CategoryBreakdown(BaseModel):
    category_id: str
    category_name: str
    type: str
    total: float
    count: int


class MonthlyTrend(BaseModel):
    month: str  # YYYY-MM
    income: float
    expense: float
    net: float


class BudgetProgress(BaseModel):
    category_id: str
    category_name: str
    limit: float
    spent: float
    remaining: float
    percent: float  # 0-100
