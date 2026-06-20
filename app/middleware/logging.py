import logging
import time
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every incoming request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request details
        logger.info(
            "%s %s — %d — %.2fms — %s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request.client.host if request.client else "unknown",
        )

        # Add timing header
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"

        return response


def setup_logging_middleware(app: FastAPI) -> None:
    """Add request logging middleware to the application."""
    app.add_middleware(RequestLoggingMiddleware)
