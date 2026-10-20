import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.db import items_repository
from app.db.database import get_db
from app.schemas.items import ItemListResponse, ItemResponse

router = APIRouter(tags=["items"])


@router.get("/items", response_model=ItemListResponse, summary="List saved items, newest first")
def list_items(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> ItemListResponse:
    items = [ItemResponse.from_record(record) for record in items_repository.list_items(conn)]
    return ItemListResponse(items=items, count=len(items))
