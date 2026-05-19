from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, status

from app.modules.auth.interfaces.http.deps import get_current_user
from app.modules.categories.application.dtos import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
)
from app.modules.categories.application.service import CategoryService
from app.modules.categories.domain.repository import CategoryRepository
from app.modules.categories.infrastructure.models import CategoryType
from app.modules.categories.infrastructure.repository import MongoCategoryRepository
from app.modules.users.infrastructure.models import User

router = APIRouter(prefix="/categories", tags=["categories"])


def get_category_repository() -> CategoryRepository:
    return MongoCategoryRepository()


def get_category_service(
    repo: CategoryRepository = Depends(get_category_repository),
) -> CategoryService:
    return CategoryService(repo=repo)


@router.get("", response_model=list[CategoryOut])
async def list_categories(
    type: CategoryType | None = None,
    user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> list[CategoryOut]:
    return await service.list(user.id, type)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> CategoryOut:
    return await service.create(user.id, body)


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: PydanticObjectId,
    body: CategoryUpdate,
    user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> CategoryOut:
    return await service.update(user.id, category_id, body)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: PydanticObjectId,
    user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> None:
    await service.delete(user.id, category_id)
