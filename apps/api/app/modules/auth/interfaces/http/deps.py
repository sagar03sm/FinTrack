"""HTTP-layer dependency factories for the auth module."""

from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import TokenType, decode_token
from app.modules.auth.application.service import AuthService
from app.modules.users.domain.repository import UserRepository
from app.modules.users.infrastructure.models import User, UserRole
from app.modules.users.infrastructure.repository import MongoUserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ---- DI factories ----------------------------------------------------------
def get_user_repository() -> UserRepository:
    return MongoUserRepository()


def get_auth_service(
    users: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(users=users)


# ---- Request-scoped auth ---------------------------------------------------
async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token, TokenType.ACCESS)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e

    try:
        oid = PydanticObjectId(payload["sub"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject"
        ) from e

    user = await users.get_by_id(oid)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*roles: UserRole):
    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _guard
