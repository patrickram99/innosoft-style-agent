"""Helpers for per-rule tests (formato-reglas.md §14)."""
from __future__ import annotations

from app.extraction.figures import Caption, Figure
from app.extraction.text import DocumentData, Page
from app.rules import EvaluationContext, RuleSet, get_rule_set, run_rules


def make_figure(
    *,
    height_px: int | None = 800,
    width_px: int | None = 2000,
    dpi: float | None = 300.0,
    kind: str = "raster",
    page: int = 1,
    order: int = 1,
    number: int | None = 1,
) -> Figure:
    if kind == "vector":
        height_px = width_px = None
        dpi = None
    w_in = (width_px / dpi) if (width_px and dpi) else 5.0
    h_in = (height_px / dpi) if (height_px and dpi) else 3.0
    caption = None
    if number is not None:
        caption = Caption(text=f"Figura {number}. Prueba", number=number, position="below",
                          bbox=[90.0, 420.0, 520.0, 440.0], font="TimesNewRomanPSMT", size=10.0)
    return Figure(
        order=order, page=page, kind=kind, bbox=[90.0, 100.0, 90.0 + w_in * 72, 100.0 + h_in * 72],
        width_px=width_px, height_px=height_px,
        print_width_in=round(w_in, 3), print_height_in=round(h_in, 3),
        dpi_x=dpi, dpi_y=dpi, caption=caption,
    )


def context_with(figures: list[Figure], article_type: str | None = "original") -> EvaluationContext:
    doc = DocumentData(pages=[Page(page=1, width=612, height=792)])
    return EvaluationContext(document=doc, figures=figures, article_type=article_type, manuscript_id="test")


def run_rule(rule_id: str, figures: list[Figure], article_type: str = "original", rule_set: RuleSet | None = None):
    rule_set = rule_set or get_rule_set()
    rule = rule_set.by_id[rule_id]
    result = run_rules(context_with(figures, article_type), [rule])
    assert not result.errors, result.errors
    return result.findings
