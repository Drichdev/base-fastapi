from enum import StrEnum


class UserRole(StrEnum):
    """User roles in the application."""

    USER = "user"
    ADMIN = "admin"


class TokenType(StrEnum):
    """JWT token types."""

    ACCESS = "access"
    REFRESH = "refresh"
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"
