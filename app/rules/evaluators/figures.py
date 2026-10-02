"""Figure evaluators (US-10): `figure_min_pixels` (RE-20) and `figure_min_dpi` (RE-21).

Thresholds come exclusively from the rule's YAML parameters (RNF-05).
"""
from __future__ import annotations

from app.extraction.figures import Figure
from app.rules.engine import EvaluationContext, Finding
from app.rules.loader import Rule
from app.rules.registry import EvaluatorParams, registry


class MinPixelsParams(EvaluatorParams):
    min_height_px: int
    min_width_px: int
    aplica_a_vectoriales: bool = False


class MinDpiParams(EvaluatorParams):
    min_dpi: float


def _location(fig: Figure) -> dict:
    return {
        "tipo": "figura",
        "numero": fig.caption.number if fig.caption else None,
        "posicion": fig.order,
        "etiqueta": fig.label,
        "bbox": fig.bbox,
    }


def _evidence(fig: Figure) -> dict:
    if fig.thumbnail:
        return {"tipo": "imagen", "ruta": fig.thumbnail}
    return {"tipo": "texto", "fragmento": fig.caption.text if fig.caption else fig.label}


@registry.register("figure_min_pixels", MinPixelsParams)
def figure_min_pixels(ctx: EvaluationContext, params: MinPixelsParams, rule: Rule) -> list[Finding]:
    """RE-20: fails if height_px < min_height_px OR width_px < min_width_px (alto × ancho)."""
    findings: list[Finding] = []
    for fig in ctx.figures:
        if fig.kind == "vector" and not params.aplica_a_vectoriales:
            continue
        if fig.height_px is None or fig.width_px is None:
            continue
        if fig.height_px < params.min_height_px or fig.width_px < params.min_width_px:
            findings.append(
                Finding(
                    pagina=fig.page,
                    ubicacion=_location(fig),
                    evidencia=_evidence(fig),
                    valor_encontrado=f"{fig.height_px} × {fig.width_px} px",
                    valor_esperado=f"≥ {params.min_height_px} × {params.min_width_px} px",
                )
            )
    return findings


@registry.register("figure_min_dpi", MinDpiParams)
def figure_min_dpi(ctx: EvaluationContext, params: MinDpiParams, rule: Rule) -> list[Finding]:
    """RE-21: fails if min(dpi_x, dpi_y) < min_dpi. Vector figures: not applicable."""
    findings: list[Finding] = []
    for fig in ctx.figures:
        if fig.kind == "vector" or fig.dpi_x is None or fig.dpi_y is None:
            continue
        dpi = min(fig.dpi_x, fig.dpi_y)
        if dpi < params.min_dpi:
            findings.append(
                Finding(
                    pagina=fig.page,
                    ubicacion=_location(fig),
                    evidencia=_evidence(fig),
                    valor_encontrado=f"≈ {dpi:.0f} dpi",
                    valor_esperado=f"≥ {params.min_dpi:.0f} dpi",
                )
            )
    return findings
