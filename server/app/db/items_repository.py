import sqlite3
from dataclasses import dataclass
from typing import Literal

SourceType = Literal["note", "url"]


@dataclass(frozen=True)
class ItemRecord:
    id: str
    source_type: SourceType
    title: str
    url: str | None
    content: str
    created_at: str
    chunk_count: int = 0


def insert_item(conn: sqlite3.Connection, item: ItemRecord) -> None:
    conn.execute(
        """
        INSERT INTO items (id, source_type, title, url, content, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (item.id, item.source_type, item.title, item.url, item.content, item.created_at),
    )


def list_items(conn: sqlite3.Connection) -> list[ItemRecord]:
    """All items, newest first, with how many chunks each was split into."""
    rows = conn.execute(
        """
        SELECT i.id, i.source_type, i.title, i.url, i.content, i.created_at,
               COUNT(c.id) AS chunk_count
        FROM items i
        LEFT JOIN chunks c ON c.item_id = i.id
        GROUP BY i.id
        ORDER BY i.created_at DESC
        """
    ).fetchall()
    return [ItemRecord(**dict(row)) for row in rows]
