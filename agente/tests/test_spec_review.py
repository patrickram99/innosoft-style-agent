"""Spec review tooling (D-07): context building and outcome handling. No network and no ADK import here."""
import datetime as dt

import pytest

from tools.spec_review import context as ctx

TODAY = dt.date(2026, 11, 10)
SPEC = """---
id: US-90
estado_spec: Borrador   # Borrador → Aprobada
depende_de: [US-91]
---

# US-90 · Historia de ejemplo

Valida RE-20.

## Historial de cambios

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 0.1 | 2026-09-29 | Equipo | Borrador inicial. |
"""


@pytest.fixture
def specs_dir(tmp_path, monkeypatch):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "US-90.md").write_text(SPEC, encoding="utf-8")
    (specs / "US-91.md").write_text("---\nid: US-91\nestado_spec: Aprobada\n---\n# US-91 · Dependencia\n", encoding="utf-8")
    (specs / "00-producto.md").write_text("# Especificación general del producto\n", encoding="utf-8")
    monkeypatch.setattr(ctx, "SPECS", specs)
    return specs


def test_normalize_id_accepts_short_and_long_forms():
    assert ctx.normalize_id("5") == "US-05"
    assert ctx.normalize_id("us-07") == "US-07"
    with pytest.raises(ValueError):
        ctx.normalize_id("RE-20")


def test_context_includes_spec_product_dependency_and_cited_rules(specs_dir):
    context = ctx.build_context("US-90")
    assert context.startswith("# SPEC EN REVISIÓN: US-90")
    assert "# SPEC DE PRODUCTO" in context
    assert "# SPEC DE LA QUE DEPENDE: US-91 (estado: Aprobada)" in context
    assert "RE-20" in context.split("# CATÁLOGO DE REQUISITOS", 1)[1]


def test_reviewer_refuses_to_read_real_manuscripts(tmp_path, monkeypatch):
    private = tmp_path / "muestras"
    private.mkdir()
    (private / "manuscrito.txt").write_text("datos personales", encoding="utf-8")
    monkeypatch.setattr(ctx, "FORBIDDEN", private)
    with pytest.raises(PermissionError):
        ctx._read(private / "manuscrito.txt")


def test_favourable_spec_moves_to_reviewed_state_once(specs_dir):
    assert ctx.mark_reviewed("US-90", TODAY) is True
    text = (specs_dir / "US-90.md").read_text(encoding="utf-8")
    assert ctx.spec_state(text) == ctx.REVIEWED_STATE
    assert "Revisor multiagente" in text.splitlines()[-1]
    assert ctx.mark_reviewed("US-90", TODAY) is False  # already reviewed: no second row


def test_report_lists_observations_and_pending_ratification():
    verdict = {
        "veredicto": "con_observaciones",
        "resumen": "Falta un caso de prueba.",
        "observaciones": [{"severidad": "mayor", "seccion": "§9", "descripcion": "AC-02 sin caso | ver §8", "correccion": "Agregar T-05"}],
    }
    report = ctx.render_report("US-90", verdict, {"consistencia": "Sin observaciones."}, "modelo-x", 1234, TODAY)
    assert "| Veredicto | **Con observaciones** |" in report
    assert "| Ratificación del equipo | Pendiente |" in report
    assert "| 1 | mayor | §9 | AC-02 sin caso \\| ver §8 | Agregar T-05 |" in report
    assert "_Sin dictamen._" in report  # reviewers that returned nothing are visible, not silently dropped
