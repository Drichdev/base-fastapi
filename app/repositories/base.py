from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.base import BaseDocument


class BaseRepository:
    """Generic async CRUD repository for MongoDB.

    Provides reusable data-access methods for all collections.
    """

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str) -> None:
        self.db = db
        self.collection = db[collection_name]

    async def create(self, document: dict) -> dict:
        """Insert a new document."""
        await self.collection.insert_one(document)
        return document

    async def get_by_id(self, document_id: str) -> dict | None:
        """Find a document by its _id."""
        return await self.collection.find_one({"_id": document_id})

    async def get_one(self, filters: dict) -> dict | None:
        """Find a single document matching the filters."""
        return await self.collection.find_one(filters)

    async def get_many(
        self,
        filters: dict | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1,
    ) -> list[dict]:
        """Find multiple documents with pagination and sorting."""
        query_filters = filters or {}
        cursor = (
            self.collection.find(query_filters)
            .sort(sort_by, sort_order)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def count(self, filters: dict | None = None) -> int:
        """Count documents matching the filters."""
        query_filters = filters or {}
        return await self.collection.count_documents(query_filters)

    async def update(self, document_id: str, update_data: dict) -> dict | None:
        """Update a document by its _id. Returns the updated document."""
        update_data.update(BaseDocument.update_timestamp())
        result = await self.collection.find_one_and_update(
            {"_id": document_id},
            {"$set": update_data},
            return_document=True,
        )
        return result

    async def delete(self, document_id: str) -> bool:
        """Delete a document by its _id. Returns True if deleted."""
        result = await self.collection.delete_one({"_id": document_id})
        return result.deleted_count > 0

    async def exists(self, filters: dict) -> bool:
        """Check if a document exists matching the filters."""
        doc = await self.collection.find_one(filters, {"_id": 1})
        return doc is not None

    async def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict]:
        """Run an aggregation pipeline."""
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)
