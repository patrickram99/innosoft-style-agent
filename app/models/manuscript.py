"""Manuscript model (US-01). Column names follow 00-producto.md §8.4 and US-01 §5."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ManuscriptStatus:
    """Manuscript lifecycle states (00-producto.md §7.1, US-01 §6.6)."""

    RECEIVED = "received"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    VALIDATING = "validating"
    VALIDATED = "validated"
    GENERATING = "generating"
    READY_FOR_REVIEW = "ready_for_review"
    IN_REVIEW = "in_review"
    PUBLISH_PENDING = "publish_pending"
    PUBLISHED = "published"
    NO_OBSERVATIONS = "no_observations"
    UNREADABLE = "unreadable"
    OUT_OF_SCOPE = "out_of_scope"
    PUBLISH_FAILED = "publish_failed"
    FAILED = "failed"


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Manuscript(Base):
    __tablename__ = "manuscripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    submission_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    section_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    article_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(16), nullable=True)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ManuscriptStatus.RECEIVED)
    status_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
