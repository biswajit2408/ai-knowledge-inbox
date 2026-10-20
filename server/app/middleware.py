import logging
import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.request_context import request_id_var
from app.timing import elapsed_ms

logger = logging.getLogger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 64


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID, logs one line per request, and turns unhandled
    exceptions into a clean 500 response instead of leaking a stack trace."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = self._resolve_request_id(request)
        token = request_id_var.set(request_id)
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "unhandled error",
                extra={"method": request.method, "path": request.url.path},
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )

        duration_ms = elapsed_ms(start)
        level = logging.ERROR if response.status_code >= 500 else (
            logging.WARNING if response.status_code >= 400 else logging.INFO
        )
        logger.log(
            level,
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        response.headers[REQUEST_ID_HEADER] = request_id
        request_id_var.reset(token)
        return response

    @staticmethod
    def _resolve_request_id(request: Request) -> str:
        """Reuse a caller-supplied ID (useful for tracing across services), else generate one."""
        incoming = request.headers.get(REQUEST_ID_HEADER, "").strip()
        if incoming and len(incoming) <= MAX_REQUEST_ID_LENGTH:
            return incoming
        return uuid.uuid4().hex
