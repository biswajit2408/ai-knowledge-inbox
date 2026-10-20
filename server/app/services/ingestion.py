import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.db import items_repository
from app.db.items_repository import ItemRecord, SourceType
from app.services import url_fetcher

logger = logging.getLogger(__name__)

TITLE_FROM_CONTENT_LENGTH = 80


def ingest_note(conn: sqlite3.Connection, content: str, title: str | None) -> ItemRecord:
    """Store a plain-text note and return the saved record."""
    return _save_item(
        conn,
        source_type="note",
        title=title or _title_from_content(content),
        url=None,
        content=content,
    )


async def ingest_url(conn: sqlite3.Connection, url: str, title: str | None) -> ItemRecord:
    """Fetch a web page, extract its text, and store it."""
    page = await url_fetcher.fetch_page(url)
    return _save_item(
        conn,
        source_type="url",
        title=title or page.title or urlparse(url).hostname or url,
        url=url,
        content=page.text,
    )


def _save_item(
    conn: sqlite3.Connection,
    source_type: SourceType,
    title: str,
    url: str | None,
    content: str,
) -> ItemRecord:
    item = ItemRecord(
        id=uuid.uuid4().hex,
        source_type=source_type,
        title=title,
        url=url,
        content=content,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with conn:  # commits on success, rolls back on error
        items_repository.insert_item(conn, item)

    logger.info(
        "item ingested",
        extra={"item_id": item.id, "source_type": item.source_type, "content_length": len(content)},
    )
    return item


def _title_from_content(content: str) -> str:
    """Use the first line of the content, shortened, as a fallback title."""
    first_line = content.strip().splitlines()[0].strip()
    if len(first_line) <= TITLE_FROM_CONTENT_LENGTH:
        return first_line
    return first_line[:TITLE_FROM_CONTENT_LENGTH].rstrip() + "…"
