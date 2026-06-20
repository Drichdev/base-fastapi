import logging
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.core.exceptions import RateLimitException
from app.database import RedisClient

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis sliding window.

    Limits requests per IP address per minute.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()

        # Skip rate limiting for health checks and metrics
        if request.url.path.startswith(("/api/v1/health", "/metrics")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        rate_limit_key = f"rate_limit:{client_ip}"

        try:
            redis = RedisClient.get_client()

            # Increment request count
            current = await redis.incr(rate_limit_key)

            # Set expiry on first request in the window
            if current == 1:
                await redis.expire(rate_limit_key, 60)

            if current > settings.RATE_LIMIT_PER_MINUTE:
                logger.warning("Rate limit exceeded for IP: %s", client_ip)
                raise RateLimitException()

        except RateLimitException:
            raise
        except Exception:
            # If Redis is down, allow the request through
            logger.warning("Rate limiter unavailable, allowing request through")

        response = await call_next(request)

        # Add rate limit headers
        try:
            redis = RedisClient.get_client()
            remaining = max(0, settings.RATE_LIMIT_PER_MINUTE - int(await redis.get(rate_limit_key) or 0))
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        except Exception:
            pass

        return response


def setup_rate_limit_middleware(app: FastAPI) -> None:
    """Add rate limiting middleware to the application."""
    app.add_middleware(RateLimitMiddleware)
