from fastapi import FastAPI

from app.config import get_settings

# Load settings at import time so a missing/invalid .env fails fast on startup.
settings = get_settings()

app = FastAPI(
    title="AI Knowledge Inbox",
    description="Save notes and URLs, then ask questions answered over your saved content.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness check: confirms the server is up and routing works."""
    return {"status": "ok"}
