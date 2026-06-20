import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import get_settings
from app.core.enums import UserRole
from app.core.security import hash_password
from app.database import Database, RedisClient
from app.middleware.cors import setup_cors
from app.middleware.logging import setup_logging_middleware
from app.middleware.rate_limit import setup_rate_limit_middleware
from app.models.user import UserDocument
from app.repositories.user import UserRepository
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.users import router as users_router

# ─────────────────────────────────────────────
# Logging configuration
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ─────────────────────────────────────────────
# Application lifespan (startup / shutdown)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to services on startup, disconnect on shutdown."""
    # Startup
    logger.info("Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)

    await Database.connect()
    await RedisClient.connect()

    # Seed admin user if it doesn't exist
    await _seed_admin_user()

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down %s...", settings.APP_NAME)
    await RedisClient.disconnect()
    await Database.disconnect()
    logger.info("Application shut down")


async def _seed_admin_user() -> None:
    """Create the default admin user if it doesn't exist."""
    db = Database.get_db()
    user_repo = UserRepository(db)

    if await user_repo.email_exists(settings.ADMIN_EMAIL):
        logger.info("Admin user already exists: %s", settings.ADMIN_EMAIL)
        return

    admin_doc = UserDocument.create(
        email=settings.ADMIN_EMAIL,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        first_name=settings.ADMIN_FIRST_NAME,
        last_name=settings.ADMIN_LAST_NAME,
        role=UserRole.ADMIN,
    )
    admin_doc["is_verified"] = True

    await user_repo.create(admin_doc)
    logger.info("Admin user created: %s", settings.ADMIN_EMAIL)


# ─────────────────────────────────────────────
# FastAPI application
# ─────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FastAPI application",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
# Middleware (order matters: last added = first executed)
# ─────────────────────────────────────────────
setup_cors(app)
setup_logging_middleware(app)
setup_rate_limit_middleware(app)

# ─────────────────────────────────────────────
# Prometheus instrumentation
# ─────────────────────────────────────────────
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics", "/api/v1/health", "/api/v1/health/ready"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint — API info."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs" if settings.is_development else "disabled",
    }
