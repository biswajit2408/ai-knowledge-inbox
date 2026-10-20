import logging
import sqlite3
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.config import get_settings
from app.db import chunks_repository, items_repository
from app.db.items_repository import ItemRecord, SourceType
from app.services import embeddings, url_fetcher
from app.services.chunking import chunk_text

logger = logging.getLogger(__name__)

TITLE_FROM_CONTENT_LENGTH = 80


async def ingest_note(conn: sqlite3.Connection, content: str, title: str | None) -> ItemRecord:
    """Store a plain-text note and index it for search."""
    return await _index_and_save(
        conn,
        source_type="note",
        title=title or _title_from_content(content),
        url=None,
        content=content,
    )


async def ingest_url(conn: sqlite3.Connection, url: str, title: str | None) -> ItemRecord:
    """Fetch a web page, extract its text, and store and index it."""
    page = await url_fetcher.fetch_page(url)
    return await _index_and_save(
        conn,
        source_type="url",
        title=title or page.title or urlparse(url).hostname or url,
        url=url,
        content=page.text,
    )


async def _index_and_save(
    conn: sqlite3.Connection,
    source_type: SourceType,
    title: str,
    url: str | None,
    content: str,
) -> ItemRecord:
    """Chunk and embed the content, then save the item and its chunks together.

    Embedding happens before any write, so if Gemini fails nothing is stored and
    we never end up with an item that can't be searched.
    """
    settings = get_settings()
    chunks = chunk_text(content, chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
    vectors = await embeddings.embed_documents(chunks, title=title)

    item = ItemRecord(
        id=uuid.uuid4().hex,
        source_type=source_type,
        title=title,
        url=url,
        content=content,
        created_at=datetime.now(timezone.utc).isoformat(),
        chunk_count=len(chunks),
    )
    with conn:  # one transaction: commits both on success, rolls back both on error
        items_repository.insert_item(conn, item)
        chunks_repository.insert_chunks(conn, item.id, chunks, vectors)

    logger.info(
        "item ingested",
        extra={
            "item_id": item.id,
            "source_type": item.source_type,
            "content_length": len(content),
            "chunk_count": item.chunk_count,
        },
    )
    return item


def _title_from_content(content: str) -> str:
    """Use the first line of the content, shortened, as a fallback title."""
    first_line = content.strip().splitlines()[0].strip()
    if len(first_line) <= TITLE_FROM_CONTENT_LENGTH:
        return first_line
    return first_line[:TITLE_FROM_CONTENT_LENGTH].rstrip() + "…"
