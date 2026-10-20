from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.db.items_repository import SourceType
from app.services.query import QueryResult

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class QueryRequest(BaseModel):
    question: Question
    top_k: int = Field(default=5, ge=1, le=20, description="How many chunks to retrieve as context.")

    model_config = {"json_schema_extra": {"examples": [{"question": "What is RAG and why is it useful?"}]}}


class SourceResponse(BaseModel):
    number: int = Field(description="Matches the [n] markers in the answer.")
    cited: bool = Field(description="Whether the answer actually cites this source.")
    item_id: str
    title: str
    url: str | None
    source_type: SourceType
    chunk_index: int
    snippet: str
    score: float = Field(description="Cosine similarity to the question (higher is more relevant).")


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]

    @classmethod
    def from_result(cls, result: QueryResult) -> "QueryResponse":
        return cls(
            answer=result.answer,
            sources=[
                SourceResponse(
                    number=number,
                    cited=number in result.cited_numbers,
                    item_id=retrieved.chunk.item_id,
                    title=retrieved.chunk.item_title,
                    url=retrieved.chunk.item_url,
                    source_type=retrieved.chunk.source_type,
                    chunk_index=retrieved.chunk.chunk_index,
                    snippet=retrieved.chunk.text,
                    score=round(retrieved.score, 4),
                )
                for number, retrieved in enumerate(result.sources, start=1)
            ],
        )
