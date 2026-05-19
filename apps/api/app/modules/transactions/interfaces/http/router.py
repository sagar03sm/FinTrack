from datetime import datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.modules.auth.interfaces.http.deps import get_current_user
from app.modules.categories.domain.repository import CategoryRepository
from app.modules.categories.infrastructure.models import Category, CategoryType
from app.modules.categories.infrastructure.repository import MongoCategoryRepository
from app.modules.chat.application.service import ChatService
from app.modules.transactions.application.dtos import (
    TransactionCreate,
    TransactionListOut,
    TransactionOut,
    TransactionUpdate,
)
from app.modules.transactions.application.service import TransactionService
from app.modules.transactions.domain.repository import TransactionRepository
from app.modules.transactions.infrastructure.models import TransactionType
from app.modules.transactions.infrastructure.repository import MongoTransactionRepository
from app.modules.users.infrastructure.models import User

router = APIRouter(prefix="/transactions", tags=["transactions"])


class SuggestCategoryRequest(BaseModel):
    note: str
    type: TransactionType


class SuggestCategoryResponse(BaseModel):
    category_id: str | None
    category_name: str | None
    confidence: str  # "high" | "medium" | "low"


def get_transaction_repository() -> TransactionRepository:
    return MongoTransactionRepository()


def get_category_repository() -> CategoryRepository:
    return MongoCategoryRepository()


def get_transaction_service(
    transactions: TransactionRepository = Depends(get_transaction_repository),
    categories: CategoryRepository = Depends(get_category_repository),
) -> TransactionService:
    return TransactionService(transactions=transactions, categories=categories)


@router.get("", response_model=TransactionListOut)
async def list_transactions(
    type: TransactionType | None = None,
    category_id: str | None = None,
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionListOut:
    return await service.list(
        user.id,
        type_=type,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        skip=skip,
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionOut:
    return await service.create(user.id, body)


@router.post("/suggest-category", response_model=SuggestCategoryResponse)
async def suggest_category(
    body: SuggestCategoryRequest,
    user: User = Depends(get_current_user),
) -> SuggestCategoryResponse:
    """AI-powered category suggestion based on transaction note."""
    # Map TransactionType to CategoryType
    cat_type = CategoryType.INCOME if body.type == TransactionType.INCOME else CategoryType.EXPENSE
    categories = await Category.find(
        Category.user_id == user.id,
        Category.type == cat_type,
    ).to_list()

    if not categories:
        return SuggestCategoryResponse(category_id=None, category_name=None, confidence="low")

    chat = ChatService()
    if not chat.client:
        # No AI configured — fall back to keyword match
        return SuggestCategoryResponse(category_id=None, category_name=None, confidence="low")

    category_list = "\n".join(f"- {c.name}" for c in categories)
    prompt = f"""You are a transaction categorization assistant. Given a transaction note, pick the single best matching category from the list.

Transaction type: {body.type.value}
Transaction note: "{body.note}"

Available categories:
{category_list}

Respond with ONLY the exact category name from the list. No explanation, no punctuation, just the name."""

    try:
        response = await chat.client.chat.completions.create(
            model=chat.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=20,
        )
        suggestion = (response.choices[0].message.content or "").strip()
        # Find exact match
        match = next((c for c in categories if c.name.lower() == suggestion.lower()), None)
        if match:
            return SuggestCategoryResponse(
                category_id=str(match.id),
                category_name=match.name,
                confidence="high",
            )
        # Find partial match
        match = next((c for c in categories if suggestion.lower() in c.name.lower() or c.name.lower() in suggestion.lower()), None)
        if match:
            return SuggestCategoryResponse(
                category_id=str(match.id),
                category_name=match.name,
                confidence="medium",
            )
    except Exception:
        pass

    return SuggestCategoryResponse(category_id=None, category_name=None, confidence="low")


@router.get("/{transaction_id}", response_model=TransactionOut)
async def get_transaction(
    transaction_id: PydanticObjectId,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionOut:
    return await service.get(user.id, transaction_id)


@router.patch("/{transaction_id}", response_model=TransactionOut)
async def update_transaction(
    transaction_id: PydanticObjectId,
    body: TransactionUpdate,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionOut:
    return await service.update(user.id, transaction_id, body)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: PydanticObjectId,
    user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> None:
    await service.delete(user.id, transaction_id)
