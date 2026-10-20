import logging
import time
from typing import Literal

import numpy as np
from google.genai import types

from app.config import get_settings
from app.errors import UpstreamError
from app.services.gemini import get_client, translate_gemini_errors

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 100  # Gemini's per-request limit for batch embedding

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]


async def embed_documents(texts: list[str], title: str | None = None) -> np.ndarray:
    """Embed chunks for storage. Returns a (len(texts), dimensions) float32 matrix
    of unit-length vectors."""
    return await _embed(texts, task_type="RETRIEVAL_DOCUMENT", title=title)


async def embed_query(text: str) -> np.ndarray:
    """Embed a search question. Returns one unit-length float32 vector."""
    return (await _embed([text], task_type="RETRIEVAL_QUERY"))[0]


async def _embed(texts: list[str], task_type: TaskType, title: str | None = None) -> np.ndarray:
    settings = get_settings()
    if not texts:
        return np.empty((0, settings.embedding_dimensions), dtype=np.float32)

    config = types.EmbedContentConfig(
        task_type=task_type,
        output_dimensionality=settings.embedding_dimensions,
        # Gemini uses the document title as extra context for document embeddings.
        title=title if task_type == "RETRIEVAL_DOCUMENT" else None,
    )

    start = time.perf_counter()
    vectors: list[list[float]] = []
    for offset in range(0, len(texts), MAX_BATCH_SIZE):
        batch = texts[offset : offset + MAX_BATCH_SIZE]
        with translate_gemini_errors("embedding"):
            response = await get_client().aio.models.embed_content(
                model=settings.embedding_model, contents=batch, config=config
            )
        if not response.embeddings or len(response.embeddings) != len(batch):
            raise UpstreamError("Gemini returned an unexpected number of embeddings.")
        vectors.extend(embedding.values or [] for embedding in response.embeddings)

    matrix = np.asarray(vectors, dtype=np.float32)
    logger.info(
        "texts embedded",
        extra={
            "task_type": task_type,
            "count": len(texts),
            "dimensions": matrix.shape[1],
            "duration_ms": round((time.perf_counter() - start) * 1000, 2),
        },
    )
    return _normalize(matrix)


def _normalize(matrix: np.ndarray) -> np.ndarray:
    """Scale each row to length 1, so cosine similarity becomes a plain dot product.
    (Gemini only pre-normalizes full 3072-dim vectors, not truncated ones.)"""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-12, None)
