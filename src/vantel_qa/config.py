"""Central application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings.

    Field names map to uppercase environment variables. For example,
    openrouter_api_key is loaded from OPENROUTER_API_KEY. Values can come from
    the process environment or the project .env file.

    Paths are relative to the directory from which the CLI is run, normally the
    repository root.
    """

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
    """Load settings once per process and return the cached instance.

    Caching avoids reparsing .env and guarantees that every pipeline stage sees
    the same model names and storage paths during one command.
    """

    return Settings()
