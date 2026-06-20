from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.enums import TokenType, UserRole
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.database import Database
from app.repositories.user import UserRepository

security = HTTPBearer(auto_error=False)


async def get_user_repository() -> UserRepository:
    """Dependency: get UserRepository instance."""
    db = Database.get_db()
    return UserRepository(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict:
    """Dependency: extract and validate the current user from JWT access token.

    Usage: current_user: dict = Depends(get_current_user)
    """
    if not credentials:
        raise UnauthorizedException("Invalid authorization header format. Expected: Bearer <token>")

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise UnauthorizedException("Invalid or expired token")

    if payload.get("type") != TokenType.ACCESS:
        raise UnauthorizedException("Invalid token type. Access token required.")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedException("User not found")

    if not user.get("is_active", False):
        raise ForbiddenException("User account is deactivated")

    return user


async def get_current_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency: ensure the current user is an admin.

    Usage: admin: dict = Depends(get_current_admin)
    """
    if current_user.get("role") != UserRole.ADMIN:
        raise ForbiddenException("Admin access required")
    return current_user
