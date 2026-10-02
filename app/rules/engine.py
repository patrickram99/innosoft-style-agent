"""US-10 · Minimal rule engine: `run_rules(context, rules) -> RunResult`.

Each rule is evaluated in isolation: an exception inside an evaluator is recorded as
`rule_error` and the remaining rules still run (RNF-06, AC común de la épica C).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from app.extraction.figures import Figure
from app.extraction.text import DocumentData
from app.rules.loader import Rule
from app.rules.registry import EvaluatorRegistry, registry as default_registry

logger = logging.getLogger(__name__)


class Finding(BaseModel):
    """Output of an evaluator (formato-reglas.md §9). `rule_id` and `severidad` are set by the engine."""

    rule_id: str = ""
    severidad: str = ""
    pagina: int | None
    ubicacion: dict[str, Any] = Field(default_factory=dict)
    evidencia: dict[str, Any] = Field(default_factory=dict)
    valor_encontrado: str | None = None
    valor_esperado: str | None = None
    requires_llm: bool = False


class RuleError(BaseModel):
    rule_id: str
    estado: str = "rule_error"
    detalle: str


@dataclass
class EvaluationContext:
    """Everything an evaluator may look at. Extended by later stories (sections, citations, references)."""

    document: DocumentData
    figures: list[Figure] = field(default_factory=list)
    article_type: str | None = None
    manuscript_id: str | None = None


@dataclass
class RunResult:
    findings: list[Finding] = field(default_factory=list)
    errors: list[RuleError] = field(default_factory=list)
    evaluated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def run_rules(
    context: EvaluationContext,
    rules: list[Rule],
    reg: EvaluatorRegistry | None = None,
) -> RunResult:
    reg = reg if reg is not None else default_registry
    result = RunResult()
    for rule in rules:
        if not rule.activa or not rule.applies_to(context.article_type):
            result.skipped.append(rule.id)
            continue
        spec = reg.get(rule.condicion.evaluador)
        if spec is None:
            result.skipped.append(rule.id)
            continue
        try:
            params = spec.params_model.model_validate(rule.params_for(context.article_type))
            findings = spec.fn(context, params, rule) or []
            for finding in findings:
                finding.rule_id = rule.id
                finding.severidad = rule.severidad
                if rule.detectable in ("L", "L/I"):
                    finding.requires_llm = True
            result.findings.extend(findings)
            result.evaluated.append(rule.id)
        except Exception as exc:  # the engine must survive a broken evaluator
            logger.exception("rule_error en %s (%s)", rule.id, rule.condicion.evaluador)
            result.errors.append(RuleError(rule_id=rule.id, detalle=f"{type(exc).__name__}: {exc}"))
    return result
