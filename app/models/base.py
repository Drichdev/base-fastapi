from datetime import UTC, datetime

from bson import ObjectId


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(UTC)


def new_object_id() -> str:
    """Generate a new MongoDB ObjectId as string."""
    return str(ObjectId())


class BaseDocument:
    """Base document structure for all MongoDB documents.

    Provides common fields: _id, created_at, updated_at.
    """

    @staticmethod
    def base_fields() -> dict:
        """Return base fields for a new document."""
        now = utc_now()
        return {
            "_id": new_object_id(),
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def update_timestamp() -> dict:
        """Return updated_at field for updates."""
        return {"updated_at": utc_now()}
