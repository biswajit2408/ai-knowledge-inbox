import logging

from fastapi import FastAPI

from app.config import get_settings
from app.logging_config import configure_logging
from app.middleware import RequestLoggingMiddleware

# Load settings at import time so a missing/invalid .env fails fast on startup.
settings = get_settings()
configure_logging(settings.log_level)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Knowledge Inbox",
    description="Save notes and URLs, then ask questions answered over your saved content.",
    version="0.1.0",
)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness check: confirms the server is up and routing works."""
    return {"status": "ok"}


logger.info(
    "app configured",
    extra={"chat_model": settings.chat_model, "embedding_model": settings.embedding_model},
)
