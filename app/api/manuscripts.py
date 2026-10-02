"""POST /manuscripts (US-01): receive a PDF plus metadata, persist it and queue the analysis."""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_service_token
from app.api.schemas import ManuscriptAccepted, ManuscriptDuplicate, ManuscriptMetadata
from app.config import Settings, get_settings
from app.models import Manuscript, ManuscriptStatus
from app.workers.pipeline import run_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/manuscripts", tags=["manuscritos"])

PDF_SIGNATURE = b"%PDF-"
MAX_SIZE_BYTES = 25 * 1024 * 1024
CHUNK = 1024 * 1024


def is_pdf_signature(head: bytes) -> bool:
    """A PDF must start with `%PDF-` (US-01 §6.1)."""
    return head.startswith(PDF_SIGNATURE)


async def _read_upload(upload: UploadFile) -> bytes:
    """Read the upload in chunks and abort with 413 as soon as the limit is exceeded."""
    buf = bytearray()
    while chunk := await upload.read(CHUNK):
        buf.extend(chunk)
        if len(buf) > MAX_SIZE_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail={"error": "too_large"})
    return bytes(buf)


def _parse_metadata(raw: str | None) -> ManuscriptMetadata:
    if raw is None or not raw.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": ["body", "metadata"], "msg": "Falta el campo metadata", "type": "missing"}],
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": ["body", "metadata"], "msg": f"metadata no es JSON válido: {exc.msg}", "type": "json_invalid"}],
        ) from exc
    try:
        return ManuscriptMetadata.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc


def store_pdf(path: Path, content: bytes) -> None:
    """Write the PDF to storage. Separated so tests can simulate disk failures (T-07)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ManuscriptAccepted,
    responses={200: {"model": ManuscriptDuplicate}, 400: {}, 401: {}, 413: {}, 422: {}},
    dependencies=[Depends(require_service_token)],
)
async def receive_manuscript(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: str | None = Form(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    meta = _parse_metadata(metadata)

    head = await file.read(len(PDF_SIGNATURE))
    if not is_pdf_signature(head):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "not_pdf"})
    content = head + await _read_upload(file)
    sha256 = hashlib.sha256(content).hexdigest()

    # D-01: identical resubmission returns the existing manuscript, no new record or analysis.
    existing = db.scalar(
        select(Manuscript).where(Manuscript.submission_id == meta.submission_id, Manuscript.sha256 == sha256)
    )
    if existing is not None:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ManuscriptDuplicate(manuscript_id=existing.id, status=existing.status).model_dump(),
        )

    manuscript = Manuscript(
        submission_id=meta.submission_id,
        revision=meta.revision,
        section_id=meta.section_id,
        locale=meta.locale,
        title=meta.title,
        submitted_at=meta.submitted_at,
        filename=file.filename or "manuscrito.pdf",
        sha256=sha256,
        size_bytes=len(content),
        status=ManuscriptStatus.RECEIVED,
    )
    db.add(manuscript)
    db.flush()  # assigns the UUID without committing

    pdf_path = Path(settings.storage_dir) / f"{manuscript.id}.pdf"
    try:
        store_pdf(pdf_path, content)
        db.commit()
    except Exception:
        db.rollback()
        pdf_path.unlink(missing_ok=True)
        logger.exception("No se pudo persistir el manuscrito %s", manuscript.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "storage_failed"})

    background.add_task(run_analysis, manuscript.id)
    return ManuscriptAccepted(manuscript_id=manuscript.id, status=manuscript.status)
