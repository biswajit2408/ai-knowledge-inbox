import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for expected errors that map to a specific HTTP status.

    Services raise these with a message that is safe to show to the client;
    the handler below turns them into `{"detail": "..."}` responses.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST


class UnprocessableContentError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT


class UpstreamError(AppError):
    """A service we depend on (a web page, the LLM API) failed."""

    status_code = status.HTTP_502_BAD_GATEWAY


class UpstreamTimeoutError(AppError):
    status_code = status.HTTP_504_GATEWAY_TIMEOUT


async def app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    logger.warning("request failed", extra={"error_type": type(exc).__name__, "detail": exc.message})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
