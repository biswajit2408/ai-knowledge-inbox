import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.db.database import get_db
from app.schemas.items import IngestRequest, ItemResponse, NoteIngestRequest
from app.services import ingestion

router = APIRouter(tags=["ingest"])


@router.post(
    "/ingest",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a note or a URL",
    responses={
        400: {"description": "URL points to a private/local address"},
        422: {"description": "Invalid body, or the URL has no usable text"},
        502: {"description": "The URL could not be fetched, or embedding failed"},
        503: {"description": "Embedding API rate limit reached; retry later"},
        504: {"description": "Fetching the URL or embedding timed out"},
    },
)
async def ingest(
    payload: IngestRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> ItemResponse:
    if isinstance(payload, NoteIngestRequest):
        item = await ingestion.ingest_note(conn, content=payload.content, title=payload.title)
    else:
        item = await ingestion.ingest_url(conn, url=str(payload.url), title=payload.title)
    return ItemResponse.from_record(item)
