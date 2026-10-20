import logging
import sqlite3
import time
from dataclasses import dataclass

import numpy as np

from app.db import chunks_repository
from app.db.chunks_repository import StoredChunk
from app.services import embeddings

logger = logging.getLogger(__name__)

# Cap how many chunks one item may contribute, so a single long document can't
# crowd out every other source (e.g. a question that spans a note and a web page).
MAX_CHUNKS_PER_ITEM = 3


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: StoredChunk
    score: float  # cosine similarity, -1..1 (higher = more relevant)


async def search(conn: sqlite3.Connection, question: str, top_k: int) -> list[RetrievedChunk]:
    """Return the `top_k` chunks most similar in meaning to the question.

    Brute-force (exact) search: compare the question against every stored chunk.
    Vectors are unit length, so cosine similarity is a single matrix-vector
    product. This is fast for thousands of chunks; see README for scaling.
    """
    chunks, matrix = chunks_repository.load_all_chunks(conn)
    if not chunks:
        return []

    query_vector = await embeddings.embed_query(question)

    start = time.perf_counter()
    scores = matrix @ query_vector

    results: list[RetrievedChunk] = []
    taken_per_item: dict[str, int] = {}
    for i in np.argsort(-scores):
        item_id = chunks[i].item_id
        if taken_per_item.get(item_id, 0) >= MAX_CHUNKS_PER_ITEM:
            continue
        taken_per_item[item_id] = taken_per_item.get(item_id, 0) + 1
        results.append(RetrievedChunk(chunk=chunks[i], score=float(scores[i])))
        if len(results) == top_k:
            break

    logger.info(
        "chunks retrieved",
        extra={
            "searched": len(chunks),
            "returned": len(results),
            "top_score": round(results[0].score, 4),
            "search_ms": round((time.perf_counter() - start) * 1000, 2),
        },
    )
    return results
