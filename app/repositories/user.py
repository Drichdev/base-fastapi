from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserDocument
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for User documents.

    Extends BaseRepository with user-specific queries.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, UserDocument.COLLECTION)

    async def get_by_email(self, email: str) -> dict | None:
        """Find a user by email address."""
        return await self.get_one({"email": email})

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        return await self.exists({"email": email})

    async def get_active_users(self, skip: int = 0, limit: int = 20) -> list[dict]:
        """Get active users with pagination."""
        return await self.get_many(
            filters={"is_active": True},
            skip=skip,
            limit=limit,
        )

    async def count_active_users(self) -> int:
        """Count active users."""
        return await self.count({"is_active": True})

    async def get_users_by_role(self, role: str, skip: int = 0, limit: int = 20) -> list[dict]:
        """Get users filtered by role."""
        return await self.get_many(
            filters={"role": role},
            skip=skip,
            limit=limit,
        )

    async def deactivate(self, user_id: str) -> dict | None:
        """Soft delete: deactivate a user."""
        return await self.update(user_id, {"is_active": False})

    async def verify_email(self, user_id: str) -> dict | None:
        """Mark a user's email as verified."""
        return await self.update(user_id, {"is_verified": True})
