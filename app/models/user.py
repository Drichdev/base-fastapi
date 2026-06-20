from app.core.enums import UserRole
from app.models.base import BaseDocument


class UserDocument:
    """User document structure for MongoDB.

    Collection: users
    """

    COLLECTION = "users"

    @staticmethod
    def create(
        email: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.USER,
    ) -> dict:
        """Create a new user document."""
        return {
            **BaseDocument.base_fields(),
            "email": email,
            "hashed_password": hashed_password,
            "first_name": first_name,
            "last_name": last_name,
            "role": role.value,
            "is_active": True,
            "is_verified": False,
        }
