from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.modules.users.infrastructure.models import UserRole

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_ALG = "HS256"
security = HTTPBearer()


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd_ctx.verify(password, password_hash)
    except Exception:
        return False


def _make_token(sub: str, ttl_seconds: int, token_type: TokenType, role: UserRole) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "role": role.value,
        "type": token_type.value,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALG)


def create_access_token(user_id: str, role: UserRole) -> str:
    settings = get_settings()
    return _make_token(user_id, settings.jwt_access_ttl_seconds, TokenType.ACCESS, role)


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    return _make_token(user_id, settings.jwt_refresh_ttl_seconds, TokenType.REFRESH, UserRole.USER)


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALG])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
    if payload.get("type") != expected_type.value:
        raise ValueError("Wrong token type")
    if "sub" not in payload:
        raise ValueError("Token missing subject")
    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Get the current authenticated user from the JWT token."""
    token = credentials.credentials
    return decode_token(token, TokenType.ACCESS)


async def require_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Require the current user to have admin role."""
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
