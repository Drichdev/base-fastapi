import logging

from app.config import get_settings
from app.core.enums import TokenType
from app.core.exceptions import BadRequestException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_verification_token,
    create_password_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import UserDocument
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

settings = get_settings()


class AuthService:
    """Service for authentication and token management."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, data: UserCreate) -> tuple[dict, str]:
        """Register a new user and generate verification token."""
        # Check if email already exists
        if await self.user_repo.email_exists(data.email):
            raise BadRequestException("A user with this email already exists")

        # Create user document
        user_doc = UserDocument.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
        )

        user = await self.user_repo.create(user_doc)
        verification_token = create_verification_token(user["_id"])
        logger.info("New user registered: %s", data.email)
        return user, verification_token

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT tokens."""
        user = await self.user_repo.get_by_email(data.email)

        if user is None:
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(data.password, user["hashed_password"]):
            raise UnauthorizedException("Invalid email or password")

        if not user.get("is_active", False):
            raise UnauthorizedException("User account is deactivated")

        if not user.get("is_verified", False):
            raise UnauthorizedException("Email not verified. Please verify your email first.")

        # Generate tokens
        access_token = create_access_token(subject=user["_id"], role=user["role"])
        refresh_token = create_refresh_token(subject=user["_id"])

        logger.info("User logged in: %s", data.email)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, refresh_token_str: str) -> TokenResponse:
        """Refresh access token using a valid refresh token."""
        payload = decode_token(refresh_token_str)

        if payload is None:
            raise UnauthorizedException("Invalid or expired refresh token")

        if payload.get("type") != TokenType.REFRESH:
            raise UnauthorizedException("Invalid token type. Refresh token required.")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedException("User not found")

        if not user.get("is_active", False):
            raise UnauthorizedException("User account is deactivated")

        # Generate new tokens
        access_token = create_access_token(subject=user["_id"], role=user["role"])
        new_refresh_token = create_refresh_token(subject=user["_id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def verify_email(self, token: str) -> dict:
        """Verify user's email using a verification token."""
        payload = decode_token(token)
        if payload is None:
            raise BadRequestException("Invalid or expired verification token")

        if payload.get("type") != TokenType.VERIFY_EMAIL:
            raise BadRequestException("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise BadRequestException("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise BadRequestException("User not found")

        if user.get("is_verified", False):
            return user

        updated_user = await self.user_repo.verify_email(user_id)
        logger.info("User email verified: %s", updated_user["email"])
        return updated_user

    async def forgot_password(self, email: str) -> tuple[dict, str]:
        """Request a password reset. Returns the user dict and reset token."""
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise BadRequestException("User with this email does not exist")

        if not user.get("is_active", False):
            raise BadRequestException("User account is deactivated")

        reset_token = create_password_reset_token(user["_id"])
        return user, reset_token

    async def reset_password(self, token: str, new_password: str) -> dict:
        """Reset password using a reset token."""
        payload = decode_token(token)
        if payload is None:
            raise BadRequestException("Invalid or expired password reset token")

        if payload.get("type") != TokenType.RESET_PASSWORD:
            raise BadRequestException("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise BadRequestException("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.get("is_active", False):
            raise BadRequestException("User not found or deactivated")

        hashed_password = hash_password(new_password)
        updated_user = await self.user_repo.update(user_id, {"hashed_password": hashed_password})
        logger.info("User password reset successfully: %s", updated_user["email"])
        return updated_user

