from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, StringConstraints

from app.db.items_repository import ItemRecord, SourceType

MAX_NOTE_LENGTH = 50_000
PREVIEW_LENGTH = 200

NoteText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_NOTE_LENGTH)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class NoteIngestRequest(BaseModel):
    source_type: Literal["note"]
    content: NoteText = Field(description="The note text.")
    title: Title | None = Field(default=None, description="Optional; derived from the first line if omitted.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source_type": "note",
                    "title": "RAG basics",
                    "content": "RAG retrieves relevant chunks and passes them to the LLM as context.",
                }
            ]
        }
    }


class UrlIngestRequest(BaseModel):
    source_type: Literal["url"]
    url: HttpUrl = Field(description="An http(s) URL; the page is fetched server-side.")
    title: Title | None = Field(default=None, description="Optional; the page's <title> is used if omitted.")

    model_config = {
        "json_schema_extra": {
            "examples": [{"source_type": "url", "url": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"}]
        }
    }


# `source_type` decides which model validates the body, and gives precise errors.
IngestRequest = Annotated[NoteIngestRequest | UrlIngestRequest, Field(discriminator="source_type")]


class ItemResponse(BaseModel):
    id: str
    source_type: SourceType
    title: str
    url: str | None
    content_preview: str
    content_length: int
    chunk_count: int
    created_at: datetime

    @classmethod
    def from_record(cls, record: ItemRecord) -> "ItemResponse":
        preview = record.content[:PREVIEW_LENGTH]
        if len(record.content) > PREVIEW_LENGTH:
            preview = preview.rstrip() + "…"
        return cls(
            id=record.id,
            source_type=record.source_type,
            title=record.title,
            url=record.url,
            content_preview=preview,
            content_length=len(record.content),
            chunk_count=record.chunk_count,
            created_at=datetime.fromisoformat(record.created_at),
        )


class ItemListResponse(BaseModel):
    items: list[ItemResponse]
    count: int
