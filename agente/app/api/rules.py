"""GET /rules?section=&categoria= (US-09)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.rules.loader import Rule, RuleSet

router = APIRouter(prefix="/rules", tags=["reglas"])
ARTICLE_TYPES = ("corto", "original", "revision")


def get_rule_set(request: Request) -> RuleSet:
    rule_set = getattr(request.app.state, "rules", None)
    if rule_set is None:
        raise HTTPException(status_code=503, detail={"error": "rules_not_loaded"})
    return rule_set


def _serialize(rule: Rule) -> dict:
    return rule.model_dump(exclude={"notas"})


@router.get("")
def list_rules(
    request: Request,
    section: str | None = Query(default=None, description="corto | original | revision"),
    categoria: str | None = Query(default=None),
) -> dict:
    if section is not None and section not in ARTICLE_TYPES:
        raise HTTPException(status_code=422, detail={"error": "section_invalid", "permitidas": list(ARTICLE_TYPES)})
    rule_set = get_rule_set(request)
    rules = rule_set.for_section(section, categoria)
    return {
        "rules_hash": rule_set.rules_hash,
        "archivos": rule_set.files,
        "total": len(rules),
        "reglas": [_serialize(r) for r in rules],
        "not_implemented": [r.id for r in rules if r.estado == "not_implemented"],
    }
