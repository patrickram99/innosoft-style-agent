"""Application settings. Values come from environment variables or a .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./agent.sqlite"
    agent_service_token: str = "cambia-este-token"
    storage_dir: Path = ROOT_DIR / "storage"
    rules_dir: Path = ROOT_DIR / "rules" / "innosoft"
    rules_schema: Path = ROOT_DIR / "rules" / "schema" / "rule.schema.json"
    gemini_api_key: str = ""

    # Umbral técnico de US-04 §6.3 (no es una regla editorial): promedio mínimo de caracteres por página.
    min_chars_per_page: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()
