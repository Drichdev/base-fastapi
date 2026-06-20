import logging

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserAdminUpdate, UserResponse, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """Get a user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("User")
        return UserResponse.from_document(user)

    async def get_users(self, page: int = 1, page_size: int = 20) -> PaginatedResponse:
        """Get paginated list of all users (admin)."""
        skip = (page - 1) * page_size
        users = await self.user_repo.get_many(skip=skip, limit=page_size)
        total = await self.user_repo.count()

        items = [UserResponse.from_document(u) for u in users]
        return PaginatedResponse.create(
            items=[item.model_dump() for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_profile(self, user_id: str, data: UserUpdate) -> UserResponse:
        """Update own profile (regular user)."""
        update_data = data.model_dump(exclude_none=True)

        if not update_data:
            raise BadRequestException("No fields to update")

        # Handle password change
        if "password" in update_data:
            update_data["hashed_password"] = hash_password(update_data.pop("password"))

        # Handle email change — check uniqueness
        if "email" in update_data:
            existing = await self.user_repo.get_by_email(update_data["email"])
            if existing and existing["_id"] != user_id:
                raise BadRequestException("A user with this email already exists")

        updated = await self.user_repo.update(user_id, update_data)
        if updated is None:
            raise NotFoundException("User")

        logger.info("User %s updated their profile", user_id)
        return UserResponse.from_document(updated)

    async def admin_update_user(self, user_id: str, data: UserAdminUpdate) -> UserResponse:
        """Update any user (admin)."""
        update_data = data.model_dump(exclude_none=True)

        if not update_data:
            raise BadRequestException("No fields to update")

        # Handle email change — check uniqueness
        if "email" in update_data:
            existing = await self.user_repo.get_by_email(update_data["email"])
            if existing and existing["_id"] != user_id:
                raise BadRequestException("A user with this email already exists")

        updated = await self.user_repo.update(user_id, update_data)
        if updated is None:
            raise NotFoundException("User")

        logger.info("Admin updated user %s", user_id)
        return UserResponse.from_document(updated)

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user (admin)."""
        deleted = await self.user_repo.delete(user_id)
        if not deleted:
            raise NotFoundException("User")

        logger.info("User %s deleted", user_id)
        return True
