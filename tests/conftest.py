import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.database import Database, RedisClient
from app.main import app

settings = get_settings()


@pytest_asyncio.fixture(autouse=True)
async def initialize_db() -> AsyncGenerator[None, None]:
    """Initialize test database and Redis client."""
    # Override settings for testing
    settings.MONGODB_DATABASE = "test_base_fastapi_pro"

    # Connect to MongoDB & Redis
    Database.client = AsyncIOMotorClient(settings.MONGODB_URL)
    Database.db = Database.client[settings.MONGODB_DATABASE]
    await Database._create_indexes()

    await RedisClient.connect()

    yield

    # Clean up test database
    await Database.client.drop_database(settings.MONGODB_DATABASE)
    Database.client.close()
    await RedisClient.disconnect()


@pytest_asyncio.fixture(autouse=True)
async def clean_collections(initialize_db) -> AsyncGenerator[None, None]:
    """Clean collections before each test to ensure test isolation."""
    db = Database.get_db()
    collections = await db.list_collection_names()
    for col in collections:
        if not col.startswith("system."):
            await db[col].delete_many({})
    yield


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing the FastAPI application."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
