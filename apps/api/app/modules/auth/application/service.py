"""AuthService — orchestrates register/login/refresh use cases.

Depends only on the UserRepository protocol and core.security primitives.
Has no FastAPI imports — fully testable with an in-memory fake repo.
"""

from app.core.errors import AuthError, ForbiddenError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.application.dtos import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenPair,
    UserPublic,
)
from app.modules.categories.application.seeding import seed_default_categories
from app.modules.users.domain.repository import UserRepository
from app.modules.users.infrastructure.models import User, UserRole


def _to_public(user: User) -> UserPublic:
    return UserPublic(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _issue_tokens(user_id: str, role: UserRole) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id),
    )


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def register(self, body: RegisterRequest) -> AuthResponse:
        user = User(
            email=body.email.lower(),
            password_hash=hash_password(body.password),
            name=body.name,
            role=UserRole.USER,
        )
        await self._users.create(user)  # raises ConflictError on duplicate

        # Seed defaults — non-fatal; account is already created.
        try:
            await seed_default_categories(user.id)
        except Exception:  # noqa: BLE001 — intentionally swallow; logged upstream
            pass

        return AuthResponse(user=_to_public(user), tokens=_issue_tokens(str(user.id), user.role))

    async def login(self, body: LoginRequest) -> AuthResponse:
        user = await self._users.get_by_email(body.email)
        if user is None or not verify_password(body.password, user.password_hash):
            raise AuthError("Invalid email or password")
        if not user.is_active:
            raise ForbiddenError("Account is disabled")
        return AuthResponse(user=_to_public(user), tokens=_issue_tokens(str(user.id), user.role))

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH)
        except ValueError as e:
            raise AuthError(str(e)) from e
        from beanie import PydanticObjectId
        user_id = payload["sub"]
        user = await self._users.get_by_id(PydanticObjectId(user_id))
        if user is None:
            raise AuthError("User not found")
        return _issue_tokens(user_id, user.role)
