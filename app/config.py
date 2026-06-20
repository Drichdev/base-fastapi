from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ===========================
    # APPLICATION
    # ===========================
    APP_NAME: str = "BaseFastAPIPro"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_VERSION: str = "1.0.0"

    # ===========================
    # MONGODB
    # ===========================
    MONGODB_URL: str = "mongodb://mongo:27017"
    MONGODB_DATABASE: str = "base_fastapi_pro"

    # ===========================
    # JWT AUTHENTICATION
    # ===========================
    JWT_SECRET_KEY: str = "change-me-to-a-very-long-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===========================
    # REDIS
    # ===========================
    REDIS_URL: str = "redis://redis:6379/0"

    # ===========================
    # CELERY
    # ===========================
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # ===========================
    # EMAIL (SMTP)
    # ===========================
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_FROM_NAME: str = "BaseFastAPIPro"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # ===========================
    # CORS
    # ===========================
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # ===========================
    # RATE LIMITING
    # ===========================
    RATE_LIMIT_PER_MINUTE: int = 60

    # ===========================
    # ADMIN
    # ===========================
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin123456"
    ADMIN_FIRST_NAME: str = "Admin"
    ADMIN_LAST_NAME: str = "System"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
