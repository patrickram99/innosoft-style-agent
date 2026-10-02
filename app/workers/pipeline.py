"""Analysis pipeline launched with FastAPI BackgroundTasks (D-04).

Stages: extraction (US-04) → figures (US-06) → rules (US-10). Each stage records
its outcome on the manuscript; a failure never loses the manuscript (RNF-06).
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session_factory
from app.extraction.text import EXTRACTOR_VERSION, extract_text
from app.models import Document, Manuscript, ManuscriptStatus

logger = logging.getLogger(__name__)


def pdf_path_for(manuscript: Manuscript) -> Path:
    return Path(get_settings().storage_dir) / f"{manuscript.id}.pdf"


def _set_status(db: Session, manuscript: Manuscript, status: str, reason: str | None = None) -> None:
    manuscript.status = status
    manuscript.status_reason = reason
    db.commit()


def stage_extract(db: Session, manuscript: Manuscript) -> Document | None:
    """US-04: text extraction. Returns the persisted Document, or None if the PDF is unreadable."""
    _set_status(db, manuscript, ManuscriptStatus.EXTRACTING)
    result = extract_text(pdf_path_for(manuscript), min_chars_per_page=get_settings().min_chars_per_page)
    if result.status == "unreadable":
        logger.warning("Manuscrito %s ilegible: %s (%s)", manuscript.id, result.reason, result.detail)
        _set_status(db, manuscript, ManuscriptStatus.UNREADABLE, result.reason)
        return None

    document = db.get(Document, manuscript.id) or Document(manuscript_id=manuscript.id)
    document.page_count = result.document.page_count
    document.pages = [p.model_dump() for p in result.document.pages]
    document.extractor_version = EXTRACTOR_VERSION
    db.add(document)
    _set_status(db, manuscript, ManuscriptStatus.EXTRACTED)
    return document


def run_analysis(manuscript_id: str) -> None:
    """Entry point for the asynchronous analysis of a received manuscript."""
    with get_session_factory()() as db:
        manuscript = db.get(Manuscript, manuscript_id)
        if manuscript is None:
            logger.error("Manuscrito %s no existe; se omite el análisis", manuscript_id)
            return
        try:
            document = stage_extract(db, manuscript)
            if document is None:
                return
        except Exception:
            logger.exception("Fallo no recuperable al analizar el manuscrito %s", manuscript_id)
            db.rollback()
            _set_status(db, manuscript, ManuscriptStatus.FAILED, "extraction_error")
