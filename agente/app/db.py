"""SQLAlchemy 2 engine/session helpers and a JSON type that is JSONB on PostgreSQL."""
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import JSON, create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

# JSON on SQLite (tests), JSONB on PostgreSQL (docker-compose).
JSONVariant = JSON().with_variant(JSONB(), "postgresql")


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    return create_engine(url, **_engine_kwargs(url))


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a session."""
    with get_session_factory()() as session:
        yield session


def check_connection() -> bool:
    with get_engine().connect() as conn:
        return conn.execute(text("SELECT 1")).scalar() == 1


def reset_engine_cache() -> None:
    """Used by tests after changing DATABASE_URL."""
    get_engine.cache_clear()
    get_session_factory.cache_clear()
