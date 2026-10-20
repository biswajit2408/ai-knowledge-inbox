import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.db.database import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services import query

router = APIRouter(tags=["query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Ask a question over your saved content",
    responses={
        422: {"description": "Invalid body"},
        502: {"description": "Embedding or answer generation failed"},
        503: {"description": "LLM API rate limit reached; retry later"},
        504: {"description": "LLM API timed out"},
    },
)
async def ask(
    payload: QueryRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> QueryResponse:
    result = await query.answer_question(conn, question=payload.question, top_k=payload.top_k)
    return QueryResponse.from_result(result)
