from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)


class UserUpdate(BaseModel):
    """Schema for updating a user (partial update)."""

    first_name: str | None = Field(None, min_length=1, max_length=50)
    last_name: str | None = Field(None, min_length=1, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=6, max_length=128)


class UserAdminUpdate(BaseModel):
    """Schema for admin updating a user."""

    first_name: str | None = Field(None, min_length=1, max_length=50)
    last_name: str | None = Field(None, min_length=1, max_length=50)
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)."""

    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: dict) -> "UserResponse":
        """Create a UserResponse from a MongoDB document."""
        return cls(
            id=doc["_id"],
            email=doc["email"],
            first_name=doc["first_name"],
            last_name=doc["last_name"],
            role=doc["role"],
            is_active=doc["is_active"],
            is_verified=doc["is_verified"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )
