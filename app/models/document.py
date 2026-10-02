"""Document model (US-04): structured content of a manuscript, stored as JSON/JSONB."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import JSONVariant
from app.models.base import Base
from app.models.manuscript import utcnow


class Document(Base):
    __tablename__ = "documents"

    manuscript_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("manuscripts.id", ondelete="CASCADE"), primary_key=True
    )
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages: Mapped[list] = mapped_column(JSONVariant, nullable=False, default=list)
    sections: Mapped[list] = mapped_column(JSONVariant, nullable=False, default=list)
    figures: Mapped[list] = mapped_column(JSONVariant, nullable=False, default=list)
    citations: Mapped[list] = mapped_column(JSONVariant, nullable=False, default=list)
    references: Mapped[list] = mapped_column(JSONVariant, nullable=False, default=list)
    extractor_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
