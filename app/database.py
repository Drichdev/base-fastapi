import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class Database:
    """MongoDB async database manager using Motor."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

    @classmethod
    async def connect(cls) -> None:
        """Establish connection to MongoDB."""
        logger.info("Connecting to MongoDB at %s", settings.MONGODB_URL)
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        cls.db = cls.client[settings.MONGODB_DATABASE]

        # Create indexes
        await cls._create_indexes()
        logger.info("Connected to MongoDB — database: %s", settings.MONGODB_DATABASE)

    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")

    @classmethod
    async def _create_indexes(cls) -> None:
        """Create database indexes."""
        if cls.db is None:
            return

        # Users collection indexes
        await cls.db.users.create_index("email", unique=True)
        await cls.db.users.create_index("role")
        await cls.db.users.create_index("is_active")
        logger.info("Database indexes created")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get the database instance."""
        if cls.db is None:
            raise RuntimeError("Database not initialized. Call Database.connect() first.")
        return cls.db


class RedisClient:
    """Redis async client manager."""

    client: Redis | None = None

    @classmethod
    async def connect(cls) -> None:
        """Establish connection to Redis."""
        logger.info("Connecting to Redis at %s", settings.REDIS_URL)
        cls.client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        # Test connection
        await cls.client.ping()
        logger.info("Connected to Redis")

    @classmethod
    async def disconnect(cls) -> None:
        """Close Redis connection."""
        if cls.client:
            await cls.client.close()
            logger.info("Disconnected from Redis")

    @classmethod
    def get_client(cls) -> Redis:
        """Get the Redis client instance."""
        if cls.client is None:
            raise RuntimeError("Redis not initialized. Call RedisClient.connect() first.")
        return cls.client
