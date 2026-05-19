from datetime import datetime
from typing import Any

from beanie import PydanticObjectId

from app.modules.transactions.infrastructure.models import Transaction, TransactionType


def _build_filter(
    user_id: PydanticObjectId,
    *,
    type_: TransactionType | None,
    category_id: PydanticObjectId | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> dict[str, Any]:
    q: dict[str, Any] = {"user_id": user_id}
    if type_ is not None:
        q["type"] = type_.value
    if category_id is not None:
        q["category_id"] = category_id
    if date_from is not None or date_to is not None:
        date_q: dict[str, Any] = {}
        if date_from is not None:
            date_q["$gte"] = date_from
        if date_to is not None:
            date_q["$lte"] = date_to
        q["date"] = date_q
    return q


class MongoTransactionRepository:
    async def get(
        self, user_id: PydanticObjectId, transaction_id: PydanticObjectId
    ) -> Transaction | None:
        tx = await Transaction.get(transaction_id)
        if tx is None or tx.user_id != user_id:
            return None
        return tx

    async def list(
        self,
        user_id: PydanticObjectId,
        *,
        type_: TransactionType | None = None,
        category_id: PydanticObjectId | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Transaction]:
        q = _build_filter(
            user_id,
            type_=type_,
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
        )
        return (
            await Transaction.find(q)
            .sort("-date", "-_id")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def count(
        self,
        user_id: PydanticObjectId,
        *,
        type_: TransactionType | None = None,
        category_id: PydanticObjectId | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        q = _build_filter(
            user_id,
            type_=type_,
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
        )
        return await Transaction.find(q).count()

    async def create(self, transaction: Transaction) -> Transaction:
        await transaction.insert()
        return transaction

    async def update(self, transaction: Transaction) -> Transaction:
        await transaction.save()
        return transaction

    async def delete(self, transaction: Transaction) -> None:
        await transaction.delete()
