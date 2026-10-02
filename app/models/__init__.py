"""ORM models. Import every model here so Alembic sees the full metadata."""
from app.models.base import Base
from app.models.manuscript import Manuscript, ManuscriptStatus

__all__ = ["Base", "Manuscript", "ManuscriptStatus"]
