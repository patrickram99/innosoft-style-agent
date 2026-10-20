"""GET /manuscripts/{id}/findings (US-10)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_service_token
from app.models import Document, Finding, Manuscript

router = APIRouter(prefix="/manuscripts", tags=["hallazgos"], dependencies=[Depends(require_service_token)])

SEVERITY_ORDER = {"alta": 0, "media": 1, "baja": 2}


@router.get("/{manuscript_id}/findings")
def list_findings(manuscript_id: str, db: Session = Depends(get_db)) -> dict:
    manuscript = db.get(Manuscript, manuscript_id)
    if manuscript is None:
        raise HTTPException(status_code=404, detail={"error": "manuscript_not_found"})
    rows = db.scalars(select(Finding).where(Finding.manuscript_id == manuscript_id)).all()
    rows.sort(key=lambda f: (SEVERITY_ORDER.get(f.severidad, 9), f.pagina or 0, f.rule_id))
    document = db.get(Document, manuscript_id)
    return {
        "manuscript_id": manuscript_id,
        "status": manuscript.status,
        "status_reason": manuscript.status_reason,
        "rules_hash": document.rules_hash if document else None,
        "total": len(rows),
        "findings": [f.to_dict() for f in rows],
        "rule_errors": (document.rule_errors if document else None) or [],
    }
