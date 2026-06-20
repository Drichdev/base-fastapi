import logging

from fastapi import APIRouter

from app.database import Database, RedisClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["Health"])


@router.get(
    "/",
    summary="Health check",
    description="Basic health check endpoint.",
)
async def health_check() -> dict:
    """Return application status."""
    return {
        "status": "healthy",
        "service": "base-fastapi-pro",
    }


@router.get(
    "/ready",
    summary="Readiness check",
    description="Check that all dependencies (MongoDB, Redis) are ready.",
)
async def readiness_check() -> dict:
    """Check connectivity to MongoDB and Redis."""
    checks = {}

    # MongoDB check
    try:
        db = Database.get_db()
        await db.command("ping")
        checks["mongodb"] = "connected"
    except Exception:
        checks["mongodb"] = "disconnected"
        logger.exception("MongoDB readiness check failed")

    # Redis check
    try:
        redis = RedisClient.get_client()
        await redis.ping()
        checks["redis"] = "connected"
    except Exception:
        checks["redis"] = "disconnected"
        logger.exception("Redis readiness check failed")

    all_ready = all(v == "connected" for v in checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
    }
