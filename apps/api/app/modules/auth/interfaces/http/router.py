"""HTTP adapter — translates requests/responses for AuthService."""

from fastapi import APIRouter, Depends, Request, status

from app.core.logging import get_logger
from app.core.rate_limit import limiter
from app.modules.auth.application.dtos import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserPublic,
)
from app.modules.auth.application.service import AuthService
from app.modules.auth.interfaces.http.deps import (
    get_auth_service,
    get_current_user,
)
from app.modules.users.infrastructure.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


def _user_to_public(user: User) -> UserPublic:
    return UserPublic(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    result = await service.register(body)
    logger.info("user_registered", user_id=result.user.id, email=result.user.email)
    return result


@router.post("/login", response_model=AuthResponse)
@limiter.limit("20/minute")
async def login(
    request: Request,
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    result = await service.login(body)
    logger.info("user_logged_in", user_id=result.user.id)
    return result


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("60/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await service.refresh(body.refresh_token)


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)) -> UserPublic:
    return _user_to_public(user)
