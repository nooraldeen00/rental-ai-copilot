"""
Middleware for RentalAI Copilot.

Provides request/response logging, request ID tracking, and error handling.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and outgoing responses.

    Features:
    - Generates unique request ID for each request
    - Logs request details (method, path, client IP)
    - Logs response details (status code, duration)
    - Logs errors with full stack traces
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        client_ip = request.client.host if request.client else "unknown"

        # Start timing
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Incoming request: {method} {path}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "query_params": query_params,
                    "client_ip": client_ip,
                    "event": "request_start",
                }
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful response
            logger.info(
                f"Request completed: {method} {path} - {response.status_code} ({duration_ms}ms)",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "event": "request_complete",
                    }
                },
            )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log error
            logger.error(
                f"Request failed: {method} {path} - {type(exc).__name__}: {str(exc)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "duration_ms": duration_ms,
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                        "event": "request_error",
                    }
                },
            )

            # Re-raise to let exception handlers deal with it
            raise
