"""Analysis pipeline launched with FastAPI BackgroundTasks (D-04).

Stages: extraction (US-04) → figures (US-06) → rules (US-10). Each stage records
its outcome on the manuscript; a failure never loses the manuscript (RNF-06).
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session_factory
from app.extraction.figures import Figure, extract_figures
from app.extraction.text import EXTRACTOR_VERSION, DocumentData, extract_text
from app.models import Document, Finding, Manuscript, ManuscriptStatus
from app.rules import EvaluationContext, get_rule_set, run_rules

logger = logging.getLogger(__name__)


def pdf_path_for(manuscript: Manuscript) -> Path:
    return Path(get_settings().storage_dir) / f"{manuscript.id}.pdf"


def thumbnails_dir_for(manuscript: Manuscript) -> Path:
    return Path(get_settings().storage_dir) / manuscript.id


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


def stage_figures(db: Session, manuscript: Manuscript, document: Document) -> Document:
    """US-06: figures with pixels, DPI and caption; thumbnails under storage/{id}/."""
    data = DocumentData.model_validate({"pages": document.pages})
    figures = extract_figures(pdf_path_for(manuscript), data, thumbnails_dir=thumbnails_dir_for(manuscript))
    document.figures = [f.model_dump() for f in figures]
    db.add(document)
    db.commit()
    logger.info("Manuscrito %s: %d figuras", manuscript.id, len(figures))
    return document


def stage_validate(db: Session, manuscript: Manuscript, document: Document) -> list[Finding]:
    """US-10: run the active rules for the article type and persist the findings."""
    _set_status(db, manuscript, ManuscriptStatus.VALIDATING)
    rule_set = get_rule_set()
    context = EvaluationContext(
        document=DocumentData.model_validate({"pages": document.pages}),
        figures=[Figure.model_validate(f) for f in document.figures or []],
        article_type=manuscript.article_type,
        manuscript_id=manuscript.id,
    )
    result = run_rules(context, rule_set.runnable(manuscript.article_type))

    db.execute(delete(Finding).where(Finding.manuscript_id == manuscript.id))  # re-analysis replaces findings
    rows = [
        Finding(
            manuscript_id=manuscript.id,
            rule_id=f.rule_id,
            severidad=f.severidad,
            pagina=f.pagina,
            ubicacion=f.ubicacion,
            evidencia=f.evidencia,
            valor_encontrado=f.valor_encontrado,
            valor_esperado=f.valor_esperado,
            requires_llm=f.requires_llm,
        )
        for f in result.findings
    ]
    db.add_all(rows)
    document.rule_errors = [e.model_dump() for e in result.errors]
    document.rules_hash = rule_set.rules_hash
    db.add(document)
    _set_status(db, manuscript, ManuscriptStatus.VALIDATED)
    logger.info(
        "Manuscrito %s: %d hallazgos, %d rule_error (%s)",
        manuscript.id, len(rows), len(result.errors), ", ".join(result.evaluated),
    )
    return rows


def run_analysis(manuscript_id: str) -> None:
    """Entry point for the asynchronous analysis of a received manuscript."""
    with get_session_factory()() as db:
        manuscript = db.get(Manuscript, manuscript_id)
        if manuscript is None:
            logger.error("Manuscrito %s no existe; se omite el análisis", manuscript_id)
            return
        stage = "extraction"
        try:
            document = stage_extract(db, manuscript)
            if document is None:
                return
            stage = "figures"
            stage_figures(db, manuscript, document)
            stage = "validation"
            stage_validate(db, manuscript, document)
        except Exception:
            logger.exception("Fallo no recuperable (%s) al analizar el manuscrito %s", stage, manuscript_id)
            db.rollback()
            _set_status(db, manuscript, ManuscriptStatus.FAILED, f"{stage}_error")
