import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import ingest, items
from app.config import get_settings
from app.db.database import init_db
from app.logging_config import configure_logging
from app.middleware import RequestLoggingMiddleware

# Load settings at import time so a missing/invalid .env fails fast on startup.
settings = get_settings()
configure_logging(settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Runs once at startup (before the first request) and once at shutdown."""
    init_db(settings.database_path)
    logger.info(
        "app started",
        extra={"chat_model": settings.chat_model, "embedding_model": settings.embedding_model},
    )
    yield


app = FastAPI(
    title="AI Knowledge Inbox",
    description="Save notes and URLs, then ask questions answered over your saved content.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(ingest.router)
app.include_router(items.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness check: confirms the server is up and routing works."""
    return {"status": "ok"}
