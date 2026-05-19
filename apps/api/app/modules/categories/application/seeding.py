"""Use case: seed default categories for a newly-registered user."""

from beanie import PydanticObjectId

from app.modules.categories.infrastructure.models import Category, CategoryType

DEFAULT_CATEGORIES: list[tuple[str, CategoryType, str]] = [
    # name, type, color
    ("Salary", CategoryType.INCOME, "#10b981"),
    ("Freelance", CategoryType.INCOME, "#34d399"),
    ("Investments", CategoryType.INCOME, "#22d3ee"),
    ("Other Income", CategoryType.INCOME, "#a3e635"),
    ("Food & Dining", CategoryType.EXPENSE, "#f97316"),
    ("Groceries", CategoryType.EXPENSE, "#fb923c"),
    ("Transportation", CategoryType.EXPENSE, "#3b82f6"),
    ("Housing & Rent", CategoryType.EXPENSE, "#6366f1"),
    ("Utilities", CategoryType.EXPENSE, "#8b5cf6"),
    ("Entertainment", CategoryType.EXPENSE, "#ec4899"),
    ("Healthcare", CategoryType.EXPENSE, "#ef4444"),
    ("Shopping", CategoryType.EXPENSE, "#f43f5e"),
    ("Education", CategoryType.EXPENSE, "#14b8a6"),
    ("Other Expense", CategoryType.EXPENSE, "#64748b"),
]


async def seed_default_categories(user_id: PydanticObjectId) -> int:
    docs = [
        Category(
            user_id=user_id,
            name=name,
            type=ctype,
            color=color,
        )
        for (name, ctype, color) in DEFAULT_CATEGORIES
    ]
    await Category.insert_many(docs)
    return len(docs)
