import logging
import sqlite3
import uuid
from datetime import datetime, timezone

from app.db import items_repository
from app.db.items_repository import ItemRecord

logger = logging.getLogger(__name__)

TITLE_FROM_CONTENT_LENGTH = 80


def ingest_note(conn: sqlite3.Connection, content: str, title: str | None) -> ItemRecord:
    """Store a plain-text note and return the saved record."""
    item = ItemRecord(
        id=uuid.uuid4().hex,
        source_type="note",
        title=title or _title_from_content(content),
        url=None,
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
