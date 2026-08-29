from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: SecretStr
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    embedding_model: str = "openai/text-embedding-3-small"
    chroma_path: Path = Path("storage/chroma")
    chroma_collection: str = "vantel-documents"
    data_path: Path = Path("data")
    chat_model: str = "openai/gpt-5-mini"
    evaluation_cases_path: Path = Path("evals/cases.yaml")
    evaluation_db_path: Path = Path("storage/evaluations.sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance."""

    return Settings()
