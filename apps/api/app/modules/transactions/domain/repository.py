from datetime import datetime
from typing import Protocol

from beanie import PydanticObjectId

from app.modules.transactions.infrastructure.models import Transaction, TransactionType


class TransactionRepository(Protocol):
    async def get(
        self, user_id: PydanticObjectId, transaction_id: PydanticObjectId
    ) -> Transaction | None: ...

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
    ) -> list[Transaction]: ...

    async def count(
        self,
        user_id: PydanticObjectId,
        *,
        type_: TransactionType | None = None,
        category_id: PydanticObjectId | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int: ...

    async def create(self, transaction: Transaction) -> Transaction: ...

    async def update(self, transaction: Transaction) -> Transaction: ...

    async def delete(self, transaction: Transaction) -> None: ...
