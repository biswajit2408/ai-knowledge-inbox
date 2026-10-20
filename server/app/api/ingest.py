import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.db.database import get_db
from app.schemas.items import ItemResponse, NoteIngestRequest
from app.services import ingestion

router = APIRouter(tags=["ingest"])


@router.post(
    "/ingest",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a note",
)
def ingest(
    payload: NoteIngestRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> ItemResponse:
    item = ingestion.ingest_note(conn, content=payload.content, title=payload.title)
    return ItemResponse.from_record(item)
