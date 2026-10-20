"""Pydantic schemas for the API (US-01)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ManuscriptMetadata(BaseModel):
    """`metadata` part of the multipart request (00-producto.md §8.1)."""

    submission_id: int = Field(..., ge=1)
    section_id: int | None = None
    title: str | None = None
    locale: str | None = None
    revision: int = Field(default=1, ge=1)
    submitted_at: datetime | None = None


class ManuscriptAccepted(BaseModel):
    manuscript_id: str
    status: str


class ManuscriptDuplicate(BaseModel):
    manuscript_id: str
    status: str
    duplicate: bool = True
