import logging
import sqlite3
from dataclasses import dataclass

from app.services import answering, retrieval
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

EMPTY_INBOX_ANSWER = "Your inbox is empty. Save some notes or URLs first, then ask again."


@dataclass(frozen=True)
class QueryResult:
    answer: str
    sources: list[RetrievedChunk]  # in citation order: sources[0] is [1]
    cited_numbers: set[int]


async def answer_question(conn: sqlite3.Connection, question: str, top_k: int) -> QueryResult:
    """The RAG pipeline: retrieve relevant chunks, then generate a cited answer."""
    sources = await retrieval.search(conn, question, top_k=top_k)
    if not sources:
        # Nothing to ground an answer in; don't spend an LLM call.
        return QueryResult(answer=EMPTY_INBOX_ANSWER, sources=[], cited_numbers=set())

    answer = await answering.generate_answer(question, sources)
    return QueryResult(answer=answer.text, sources=sources, cited_numbers=answer.cited_numbers)
