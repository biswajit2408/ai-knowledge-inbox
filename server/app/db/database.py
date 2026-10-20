import logging
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id          TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (source_type IN ('note', 'url')),
    title       TEXT NOT NULL,
    url         TEXT,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text        TEXT NOT NULL,
    embedding   BLOB NOT NULL,
    UNIQUE (item_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at);
CREATE INDEX IF NOT EXISTS idx_chunks_item_id ON chunks(item_id);
"""


def connect(database_path: str) -> sqlite3.Connection:
    """Open a SQLite connection with sensible defaults."""
    conn = sqlite3.connect(database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(database_path: str) -> None:
    """Create the database file, its folder and the schema if they don't exist yet."""
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as conn:
        # WAL lets reads continue while a write is in progress.
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
    logger.info("database ready", extra={"database_path": database_path})


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request, always closed afterwards."""
    conn = connect(get_settings().database_path)
    try:
        yield conn
    finally:
        conn.close()
