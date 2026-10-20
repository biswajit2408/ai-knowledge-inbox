import sqlite3
from dataclasses import dataclass

import numpy as np

from app.db.items_repository import SourceType

EMBEDDING_DTYPE = np.float32


@dataclass(frozen=True)
class StoredChunk:
    """A chunk plus the metadata of the item it came from (for citations)."""

    item_id: str
    item_title: str
    item_url: str | None
    source_type: SourceType
    chunk_index: int
    text: str


def insert_chunks(conn: sqlite3.Connection, item_id: str, texts: list[str], embeddings: np.ndarray) -> None:
    """Store an item's chunks with their embeddings (as raw float32 bytes)."""
    conn.executemany(
        "INSERT INTO chunks (item_id, chunk_index, text, embedding) VALUES (?, ?, ?, ?)",
        [
            (item_id, index, text, embedding.astype(EMBEDDING_DTYPE).tobytes())
            for index, (text, embedding) in enumerate(zip(texts, embeddings, strict=True))
        ],
    )


def load_all_chunks(conn: sqlite3.Connection) -> tuple[list[StoredChunk], np.ndarray]:
    """Every chunk with its item metadata, plus an (n_chunks, dimensions) embedding matrix
    whose rows line up with the returned list."""
    rows = conn.execute(
        """
        SELECT c.item_id, i.title AS item_title, i.url AS item_url, i.source_type,
               c.chunk_index, c.text, c.embedding
        FROM chunks c
        JOIN items i ON i.id = c.item_id
        ORDER BY c.id
        """
    ).fetchall()
    if not rows:
        return [], np.empty((0, 0), dtype=EMBEDDING_DTYPE)

    chunks = [
        StoredChunk(
            item_id=row["item_id"],
            item_title=row["item_title"],
            item_url=row["item_url"],
            source_type=row["source_type"],
            chunk_index=row["chunk_index"],
            text=row["text"],
        )
        for row in rows
    ]
    matrix = np.stack([np.frombuffer(row["embedding"], dtype=EMBEDDING_DTYPE) for row in rows])
    return chunks, matrix
