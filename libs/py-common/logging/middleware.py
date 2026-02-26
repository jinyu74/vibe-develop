"""FastAPI middleware for request-scoped structured logging."""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


class RequestLoggingMiddleware:
    """Attach request_id and log request/response lifecycle."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=scope.get("method", ""),
            path=scope.get("path", ""),
        )

        logger = structlog.get_logger("http")

        status_code = 500
        original_send = send

        async def capture_send(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                if "headers" not in message:
                    message["headers"] = []
                message["headers"].append(
                    (b"x-request-id", request_id.encode())
                )
            await original_send(message)

        try:
            await self.app(scope, receive, capture_send)
        except Exception:
            logger.exception("unhandled_error")
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "request_completed",
                status=status_code,
                duration_ms=duration_ms,
            )
            structlog.contextvars.unbind_contextvars(
                "request_id", "method", "path",
            )
