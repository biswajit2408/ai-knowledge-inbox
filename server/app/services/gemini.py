import logging
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

import httpx
from google import genai
from google.genai import errors, types

from app.config import get_settings
from app.errors import ServiceUnavailableError, UpstreamError, UpstreamTimeoutError

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_MS = 30_000
RETRY_ATTEMPTS = 3  # retries transient failures (429/5xx) with exponential backoff


@lru_cache
def get_client() -> genai.Client:
    """One shared Gemini client for the whole app (it holds an HTTP connection pool)."""
    settings = get_settings()
    return genai.Client(
        api_key=settings.gemini_api_key.get_secret_value(),
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=RETRY_ATTEMPTS),
        ),
    )


@contextmanager
def translate_gemini_errors(operation: str) -> Iterator[None]:
    """Turn SDK/network exceptions into our AppErrors.

    Full details go to the log; the client gets a short message without
    provider internals.
    """
    try:
        yield
    except errors.APIError as exc:
        logger.warning(
            "gemini call failed",
            extra={"operation": operation, "code": exc.code, "status": exc.status, "error": exc.message},
        )
        if exc.code == 429:
            raise ServiceUnavailableError(f"Gemini rate limit reached during {operation}; try again shortly.") from exc
        raise UpstreamError(f"Gemini {operation} failed ({exc.status or exc.code}).") from exc
    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(f"Gemini {operation} timed out.") from exc
    except httpx.HTTPError as exc:
        raise UpstreamError(f"Could not reach Gemini for {operation} ({type(exc).__name__}).") from exc
