"""TransactionService — CRUD with category-ownership validation and denormalization."""

from datetime import datetime

from beanie import PydanticObjectId

from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.modules.categories.domain.repository import CategoryRepository
from app.modules.transactions.application.dtos import (
    TransactionCreate,
    TransactionListOut,
    TransactionOut,
    TransactionUpdate,
)
from app.modules.transactions.domain.repository import TransactionRepository
from app.modules.transactions.infrastructure.models import Transaction, TransactionType

logger = get_logger(__name__)


def _to_out(t: Transaction) -> TransactionOut:
    return TransactionOut(
        id=str(t.id),
        type=t.type,
        amount=t.amount,
        currency=t.currency,
        category_id=str(t.category_id),
        category_name=t.category_name,
        note=t.note,
        date=t.date,
        created_at=t.created_at,
    )


class TransactionService:
    def __init__(
        self,
        transactions: TransactionRepository,
        categories: CategoryRepository,
    ) -> None:
        self._tx = transactions
        self._cats = categories

    async def _resolve_category(
        self,
        user_id: PydanticObjectId,
        category_id: str,
        tx_type: TransactionType,
    ) -> tuple[PydanticObjectId, str]:
        try:
            cid = PydanticObjectId(category_id)
        except Exception as e:
            raise ValidationError("Invalid category_id") from e
        cat = await self._cats.get(user_id, cid)
        if cat is None:
            raise NotFoundError("Category not found")
        # transaction.type must align with category.type
        if cat.type.value != tx_type.value:
            raise ValidationError(
                f"Category type ({cat.type.value}) does not match transaction type ({tx_type.value})"
            )
        return cid, cat.name

    async def create(
        self, user_id: PydanticObjectId, body: TransactionCreate
    ) -> TransactionOut:
        logger.info("creating_transaction", user_id=str(user_id), type=body.type, amount=body.amount)
        cid, cname = await self._resolve_category(user_id, body.category_id, body.type)
        tx = Transaction(
            user_id=user_id,
            type=body.type,
            amount=body.amount,
            currency=body.currency.upper(),
            category_id=cid,
            category_name=cname,
            note=body.note,
            date=body.date,
        )
        await self._tx.create(tx)
        logger.info("transaction_created", transaction_id=str(tx.id), user_id=str(user_id))
        return _to_out(tx)

    async def list(
        self,
        user_id: PydanticObjectId,
        *,
        type_: TransactionType | None,
        category_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        limit: int,
        skip: int,
    ) -> TransactionListOut:
        logger.info(
            "listing_transactions",
            user_id=str(user_id),
            type=type_,
            category_id=category_id,
            limit=limit,
            skip=skip,
        )
        cid: PydanticObjectId | None = None
        if category_id:
            try:
                cid = PydanticObjectId(category_id)
            except Exception as e:
                raise ValidationError("Invalid category_id") from e
        items = await self._tx.list(
            user_id,
            type_=type_,
            category_id=cid,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            skip=skip,
        )
        total = await self._tx.count(
            user_id,
            type_=type_,
            category_id=cid,
            date_from=date_from,
            date_to=date_to,
        )
        return TransactionListOut(
            items=[_to_out(t) for t in items],
            total=total,
            limit=limit,
            skip=skip,
        )

    async def get(
        self, user_id: PydanticObjectId, transaction_id: PydanticObjectId
    ) -> TransactionOut:
        logger.info("getting_transaction", user_id=str(user_id), transaction_id=str(transaction_id))
        tx = await self._tx.get(user_id, transaction_id)
        if tx is None:
            raise NotFoundError("Transaction not found")
        return _to_out(tx)

    async def update(
        self,
        user_id: PydanticObjectId,
        transaction_id: PydanticObjectId,
        body: TransactionUpdate,
    ) -> TransactionOut:
        logger.info("updating_transaction", user_id=str(user_id), transaction_id=str(transaction_id))
        tx = await self._tx.get(user_id, transaction_id)
        if tx is None:
            raise NotFoundError("Transaction not found")

        # Determine the resulting type and category for validation.
        new_type = body.type or tx.type
        if body.category_id is not None:
            cid, cname = await self._resolve_category(user_id, body.category_id, new_type)
            tx.category_id = cid
            tx.category_name = cname
        elif body.type is not None and body.type != tx.type:
            # Type changed but category didn't — verify existing category still aligns.
            cat = await self._cats.get(user_id, tx.category_id)
            if cat is None:
                raise NotFoundError("Existing category not found")
            if cat.type.value != new_type.value:
                raise ValidationError(
                    "Existing category does not match the new transaction type; "
                    "send a category_id as well"
                )

        if body.type is not None:
            tx.type = body.type
        if body.amount is not None:
            tx.amount = body.amount
        if body.currency is not None:
            tx.currency = body.currency.upper()
        if body.note is not None:
            tx.note = body.note
        if body.date is not None:
            tx.date = body.date

        await self._tx.update(tx)
        return _to_out(tx)

    async def delete(
        self, user_id: PydanticObjectId, transaction_id: PydanticObjectId
    ) -> None:
        logger.info("deleting_transaction", user_id=str(user_id), transaction_id=str(transaction_id))
        tx = await self._tx.get(user_id, transaction_id)
        if tx is None:
            raise NotFoundError("Transaction not found")
        await self._tx.delete(tx)
        logger.info("transaction_deleted", transaction_id=str(transaction_id))
