"""Tests of the synthetic evaluation dataset tool (D-09). No LaTeX, Word or Gemini is needed here."""
from __future__ import annotations

import math

import pytest

from tools.eval_dataset import design, stats
from tools.eval_dataset.evaluate import evaluate_document, match_findings

TH = {"min_height_px": 531, "min_width_px": 1328, "min_dpi": 300}


def _fig(order: int, page: int, *, w: int = 2000, h: int = 800, dpi: float = 300, number: int | None = -1, kind: str = "raster") -> dict:
    fig = design.FigurePlan(order=order, printed_number=order if number == -1 else number, variant="png", kind=kind)
    if kind == "raster":
        fig.visible_w_px, fig.visible_h_px, fig.source_w_px, fig.source_h_px, fig.dpi = w, h, w, h, dpi
    fig.page, fig.verified = page, True
    fig.truth_source = fig.truth = design.truth(fig, TH)
    return design.asdict(fig)


def _finding(rule: str, page: int, number: int | None, position: int = 1) -> dict:
    return {"rule_id": rule, "pagina": page, "ubicacion": {"numero": number, "posicion": position}, "valor_encontrado": "x"}


def test_plan_is_deterministic_for_a_seed():
    first = [d.to_dict() for d in design.build_plan(12, 6, n_articles=5, seed=1)]
    second = [d.to_dict() for d in design.build_plan(12, 6, n_articles=5, seed=1)]
    assert first == second
    assert first != [d.to_dict() for d in design.build_plan(12, 6, n_articles=5, seed=2)]


def test_plan_survives_a_round_trip_through_json():
    doc = design.build_plan(3, 0, n_articles=5, seed=4)[2]
    assert design.doc_from_dict(doc.to_dict()).to_dict() == doc.to_dict()


def test_cropped_figures_fail_only_because_of_the_crop():
    figures = [f for d in design.build_plan(600, 0, n_articles=5, seed=5) for f in d.figures if f.variant == "recortada"]
    trapped = [f for f in figures if f.truth_source["RE-20"] and not f.truth_source["RE-21"]]
    assert trapped and all(f.source_w_px >= design.MIN_SOURCE_W_FOR_CROP and f.visible_w_px < TH["min_width_px"] for f in trapped)


def test_plan_profiles_match_their_ground_truth():
    docs = design.build_plan(150, 50, n_articles=5, seed=3)
    for doc in docs:
        violations = sum(bool(v) for f in doc.figures for v in f.truth_source.values())
        if doc.profile == "conforme":
            assert violations == 0 and not any(f.caption_defect or not f.referenced for f in doc.figures)
        assert doc.generator == "latex" or all(f.variant in ("png", "jpeg", "png_alfa") for f in doc.figures)
        for fig in doc.figures:
            if fig.kind == "raster":
                assert fig.print_w_in <= design.MAX_PRINT_W_IN and fig.print_h_in <= design.MAX_PRINT_H_IN


@pytest.mark.parametrize(
    ("w", "h", "dpi", "expected"),
    [
        (1328, 531, 300, {"RE-20": False, "RE-21": False}),  # exactly on both thresholds: complies
        (1327, 531, 300, {"RE-20": True, "RE-21": False}),
        (1328, 530, 300, {"RE-20": True, "RE-21": False}),
        (2000, 800, 299, {"RE-20": False, "RE-21": True}),
        (600, 300, 96, {"RE-20": True, "RE-21": True}),
    ],
)
def test_truth_uses_the_yaml_thresholds_at_the_boundary(w, h, dpi, expected):
    fig = design.FigurePlan(order=1, printed_number=1, variant="png", kind="raster", visible_w_px=w, visible_h_px=h, dpi=dpi)
    assert design.truth(fig, design.load_thresholds()) == expected


def test_truth_follows_the_resampling_of_the_converter():
    fig = design.FigurePlan(order=1, printed_number=1, variant="png", kind="raster", visible_w_px=2000, visible_h_px=800, dpi=300)
    fig.print_w_in, fig.print_h_in = 2000 / 300, 800 / 300
    assert design.truth(fig, TH, resampled_px=(1333, 533)) == {"RE-20": False, "RE-21": True}
    assert design.truth(fig, TH, resampled_px=(1328, 531)) == {"RE-20": False, "RE-21": True}  # exactly on the RE-20 limit
    assert design.truth(fig, TH, resampled_px=(1327, 531)) == {"RE-20": True, "RE-21": True}
    vector = design.FigurePlan(order=1, printed_number=1, variant="vectorial", kind="vector")
    assert design.truth(vector, TH) == {"RE-20": None, "RE-21": None}


def test_findings_are_matched_by_page_and_caption_number():
    figures = [_fig(1, 2), _fig(2, 2), _fig(3, 4, number=None)]
    findings = [_finding("RE-21", 2, 2), _finding("RE-20", 4, None), _finding("RE-21", 7, 1)]
    matched, spurious = match_findings(figures, findings)
    assert set(matched) == {(2, "RE-21"), (3, "RE-20")}
    assert [f["pagina"] for f in spurious] == [7]


def test_document_rows_cover_every_outcome():
    doc = {
        "doc_id": "L001", "generator": "latex",
        "figures": [_fig(1, 2, w=600, h=300), _fig(2, 3, dpi=200), _fig(3, 3), _fig(4, 5, kind="vector")],
    }
    findings = [_finding("RE-20", 2, 1), _finding("RE-21", 3, 3), _finding("RE-99", 2, 1), _finding("RE-21", 9, 8)]
    rows = evaluate_document(doc, findings)
    got = {(r["figura"], r["regla"]): r["resultado"] for r in rows}
    assert got == {
        (1, "RE-20"): "TP", (1, "RE-21"): "TN",
        (2, "RE-20"): "TN", (2, "RE-21"): "FN",
        (3, "RE-20"): "TN", (3, "RE-21"): "FP",
        ("", "RE-21"): "FP",  # spurious finding on a page without figures; the vector figure adds no row
    }


def test_confusion_metrics():
    c = stats.Confusion(tp=8, fp=2, fn=1, tn=9)
    assert c.precision == pytest.approx(0.8) and c.recall == pytest.approx(8 / 9)
    assert c.f1 == pytest.approx(2 * 0.8 * (8 / 9) / (0.8 + 8 / 9)) and c.specificity == pytest.approx(9 / 11)
    assert stats.Confusion().precision is None and stats.Confusion(fn=3).f1 is None


def test_wilson_interval_matches_reference_values():
    lo, hi = stats.wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=1e-4) and hi == pytest.approx(0.9433, abs=1e-4)
    lo, hi = stats.wilson(50, 50)
    assert hi == 1.0 and lo == pytest.approx(0.9287, abs=1e-4)
    assert stats.wilson(0, 0) is None


def test_exact_tests_match_reference_values():
    assert stats.binom_test_greater(9, 10, 0.5) == pytest.approx(11 / 1024)
    assert stats.binom_test_greater(0, 10, 0.5) == pytest.approx(1.0)
    assert stats.fisher_exact(3, 1, 1, 3) == pytest.approx(0.485714, abs=1e-6)
    assert stats.fisher_exact(10, 0, 0, 10) == pytest.approx(2 / math.comb(20, 10))


def test_spearman_and_descriptive_statistics():
    result = stats.spearman([1, 2, 3, 4, 5], [5, 6, 7, 8, 7])
    assert result["rho"] == pytest.approx(0.820783, abs=1e-6) and result["p"] == pytest.approx(0.088587, abs=1e-4)
    d = stats.describe([1.0, 2.0, 3.0, 4.0, 10.0])
    assert d["media"] == 4.0 and d["mediana"] == 3.0 and d["desv_est"] == pytest.approx(3.535534, abs=1e-6)
    fit = stats.linear_fit([1, 2, 3], [3, 5, 7])
    assert fit["pendiente"] == pytest.approx(2.0) and fit["intercepto"] == pytest.approx(1.0) and fit["r2"] == pytest.approx(1.0)


def test_figure_pages_are_read_from_the_latex_aux():
    pytest.importorskip("PIL")
    from tools.eval_dataset.gen_latex import _aux_pages

    aux = "\\newlabel{figpos:1}{{1}{3}{T\\'itulo {con} llaves}{figure.1}{}}\n\\newlabel{figpos:2}{{}{12}{}{section*.4}{}}\n\\newlabel{otro}{{1}{9}}"
    assert _aux_pages(aux) == {1: 3, 2: 12}
