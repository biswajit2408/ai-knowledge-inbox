import sqlite3

import numpy as np

EMBEDDING_DTYPE = np.float32


def insert_chunks(conn: sqlite3.Connection, item_id: str, texts: list[str], embeddings: np.ndarray) -> None:
    """Store an item's chunks with their embeddings (as raw float32 bytes)."""
    conn.executemany(
        "INSERT INTO chunks (item_id, chunk_index, text, embedding) VALUES (?, ?, ?, ?)",
        [
            (item_id, index, text, embedding.astype(EMBEDDING_DTYPE).tobytes())
            for index, (text, embedding) in enumerate(zip(texts, embeddings, strict=True))
        ],
    )
