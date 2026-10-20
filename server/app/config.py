from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM provider
    gemini_api_key: SecretStr
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = Field(default=768, ge=128, le=3072)
    chat_model: str = "gemini-3.5-flash-lite"

    # Chunking (in characters)
    chunk_size: int = Field(default=1000, ge=200, le=8000)
    chunk_overlap: int = Field(default=150, ge=0)

    # Storage
    database_path: str = "data/inbox.db"

    # Logging
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    @model_validator(mode="after")
    def _overlap_smaller_than_chunk(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so .env is read only once."""
    return Settings()
