"""US-10 · Validar figuras: tamaño y proporción."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.extraction.figures import extract_figures
from app.extraction.text import extract_text
from app.models import Finding as FindingRow
from app.models import ManuscriptStatus
from app.rules import EvaluationContext, get_rule_set, run_rules
from app.rules.engine import Finding
from app.rules.loader import Rule
from app.rules.registry import EvaluatorParams, EvaluatorRegistry
from tests.rules.helpers import context_with, make_figure

EXPECTED = {  # tests/fixtures/pdfs/README.md
    "figuras_pequenas.pdf": {"RE-20": 3, "RE-21": 0},
    "figuras_baja_dpi.pdf": {"RE-20": 1, "RE-21": 2},
    "correcto.pdf": {"RE-20": 0, "RE-21": 0},
    "sin_figuras.pdf": {"RE-20": 0, "RE-21": 0},
    "vectorial.pdf": {"RE-20": 0, "RE-21": 0},
}


def _count(findings: list[Finding]) -> dict[str, int]:
    out = {"RE-20": 0, "RE-21": 0}
    for f in findings:
        out[f.rule_id] = out.get(f.rule_id, 0) + 1
    return out


def test_t01_ac01_300x600_fails_re20():
    result = run_rules(context_with([make_figure(height_px=300, width_px=600, dpi=300)]), get_rule_set().runnable("original"))
    assert [f.rule_id for f in result.findings] == ["RE-20"]
    assert result.findings[0].valor_encontrado == "300 × 600 px"


def test_t02_ac02_800x2000_at_300dpi_passes():
    result = run_rules(context_with([make_figure(height_px=800, width_px=2000, dpi=300)]), get_rule_set().runnable("original"))
    assert result.findings == []
    assert "RE-20" in result.evaluated and "RE-21" in result.evaluated


def test_t03_ac03_150dpi_fails_re21_high_severity():
    result = run_rules(context_with([make_figure(height_px=800, width_px=2000, dpi=150)]), get_rule_set().runnable("original"))
    assert [f.rule_id for f in result.findings] == ["RE-21"]
    assert result.findings[0].severidad == "alta"


def test_t04_vector_figure_re21_not_applicable():
    result = run_rules(context_with([make_figure(kind="vector")]), get_rule_set().runnable("original"))
    assert result.findings == []


def test_one_finding_per_figure_and_rule():
    figures = [make_figure(height_px=300, width_px=600, dpi=150, order=1, number=1), make_figure(height_px=300, width_px=600, dpi=150, order=2, number=2)]
    result = run_rules(context_with(figures), get_rule_set().runnable("original"))
    assert sorted((f.rule_id, f.ubicacion["numero"]) for f in result.findings) == [("RE-20", 1), ("RE-20", 2), ("RE-21", 1), ("RE-21", 2)]


def test_t05_ac04_evaluator_exception_is_isolated():
    reg = EvaluatorRegistry()

    @reg.register("explota", EvaluatorParams)
    def explota(ctx, params, rule):
        raise RuntimeError("fallo forzado")

    @reg.register("ok", EvaluatorParams)
    def ok(ctx, params, rule):
        return [Finding(pagina=1, valor_encontrado="x", valor_esperado="y")]

    base = get_rule_set().by_id["RE-20"].model_dump()
    rule_bad = Rule.model_validate({**base, "id": "RE-98", "condicion": {"evaluador": "explota"}})
    rule_ok = Rule.model_validate({**base, "id": "RE-99", "condicion": {"evaluador": "ok"}})
    result = run_rules(context_with([make_figure()]), [rule_bad, rule_ok], reg)
    assert [f.rule_id for f in result.findings] == ["RE-99"]
    assert result.findings[0].severidad == rule_ok.severidad
    assert len(result.errors) == 1
    assert result.errors[0].rule_id == "RE-98" and result.errors[0].estado == "rule_error"
    assert "fallo forzado" in result.errors[0].detalle


def test_rules_not_applicable_to_article_type_are_skipped():
    base = get_rule_set().by_id["RE-20"].model_dump()
    rule = Rule.model_validate({**base, "seccion_aplicable": ["corto"]})
    result = run_rules(context_with([make_figure(height_px=10, width_px=10)], article_type="original"), [rule])
    assert result.findings == [] and result.skipped == ["RE-20"]


def test_thresholds_come_from_yaml_not_code():
    base = get_rule_set().by_id["RE-20"].model_dump()
    relaxed = Rule.model_validate({**base, "condicion": {"evaluador": "figure_min_pixels", "parametros": {"min_height_px": 100, "min_width_px": 100}}})
    result = run_rules(context_with([make_figure(height_px=300, width_px=600)]), [relaxed])
    assert result.findings == []


@pytest.mark.parametrize("name,expected", sorted(EXPECTED.items()))
def test_t06_corpus_expected_findings(pdf_dir: Path, name: str, expected: dict[str, int]):
    pdf = pdf_dir / name
    extraction = extract_text(pdf)
    figures = extract_figures(pdf, extraction.document)
    result = run_rules(EvaluationContext(document=extraction.document, figures=figures), get_rule_set().runnable(None))
    assert _count(result.findings) == expected
    assert result.errors == []


def _upload(client, headers, pdf_dir: Path, name: str, submission_id: int) -> str:
    r = client.post(
        "/manuscripts",
        files={"file": (name, (pdf_dir / name).read_bytes(), "application/pdf")},
        data={"metadata": json.dumps({"submission_id": submission_id})},
        headers=headers,
    )
    assert r.status_code == 202, r.text
    return r.json()["manuscript_id"]


def test_ac05_get_findings_returns_traceable_rule_ids(client, auth_headers, pdf_dir: Path):
    mid = _upload(client, auth_headers, pdf_dir, "figuras_baja_dpi.pdf", 10001)
    r = client.get(f"/manuscripts/{mid}/findings", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == ManuscriptStatus.VALIDATED
    assert body["total"] == 3
    assert body["rule_errors"] == []
    assert len(body["rules_hash"]) == 64
    valid_ids = set(get_rule_set().by_id)
    for finding in body["findings"]:
        assert finding["rule_id"] in valid_ids
        assert set(finding) >= {"rule_id", "severidad", "pagina", "ubicacion", "evidencia", "valor_encontrado", "valor_esperado"}
        assert finding["evidencia"]["tipo"] == "imagen"
        assert Path(finding["evidencia"]["ruta"]).exists()
    assert _count([Finding.model_validate(f) for f in body["findings"]]) == {"RE-20": 1, "RE-21": 2}


def test_findings_persisted_in_table(client, auth_headers, db_session, pdf_dir: Path):
    from sqlalchemy import select

    mid = _upload(client, auth_headers, pdf_dir, "figuras_pequenas.pdf", 10002)
    rows = db_session.scalars(select(FindingRow).where(FindingRow.manuscript_id == mid)).all()
    assert len(rows) == 3
    assert {r.rule_id for r in rows} == {"RE-20"}


def test_manuscript_without_figures_has_no_findings_and_no_errors(client, auth_headers, pdf_dir: Path):
    mid = _upload(client, auth_headers, pdf_dir, "sin_figuras.pdf", 10003)
    body = client.get(f"/manuscripts/{mid}/findings", headers=auth_headers).json()
    assert body["status"] == ManuscriptStatus.VALIDATED
    assert body["findings"] == [] and body["rule_errors"] == []


def test_findings_unknown_manuscript_404_and_requires_token(client, auth_headers):
    assert client.get("/manuscripts/no-existe/findings", headers=auth_headers).status_code == 404
    assert client.get("/manuscripts/no-existe/findings").status_code == 401


def test_unreadable_manuscript_reports_status_in_findings(client, auth_headers, pdf_dir: Path):
    mid = _upload(client, auth_headers, pdf_dir, "escaneado.pdf", 10004)
    body = client.get(f"/manuscripts/{mid}/findings", headers=auth_headers).json()
    assert body["status"] == ManuscriptStatus.UNREADABLE
    assert body["status_reason"] == "no_text_layer"
    assert body["findings"] == []
