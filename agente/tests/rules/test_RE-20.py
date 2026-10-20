"""RE-20 · Imagen ≥ 531 × 1328 px (alto × ancho). Umbrales leídos de rules/innosoft/figuras.yaml."""
from app.rules import get_rule_set
from tests.rules.helpers import make_figure, run_rule


def _params() -> dict:
    return get_rule_set().by_id["RE-20"].params_for("original")


def test_positive_large_figure_has_no_finding():
    p = _params()
    assert run_rule("RE-20", [make_figure(height_px=p["min_height_px"], width_px=p["min_width_px"])]) == []
    assert run_rule("RE-20", [make_figure(height_px=800, width_px=2000)]) == []


def test_negative_small_figure_fails_with_values():
    (finding,) = run_rule("RE-20", [make_figure(height_px=300, width_px=600, dpi=300, number=3, page=5)])
    assert finding.rule_id == "RE-20"
    assert finding.severidad == "alta"
    assert finding.pagina == 5
    assert finding.valor_encontrado == "300 × 600 px"
    assert finding.valor_esperado == "≥ 531 × 1328 px"
    assert finding.ubicacion["tipo"] == "figura" and finding.ubicacion["numero"] == 3


def test_negative_only_one_dimension_below_threshold_fails():
    p = _params()
    assert len(run_rule("RE-20", [make_figure(height_px=p["min_height_px"] - 1, width_px=5000)])) == 1
    assert len(run_rule("RE-20", [make_figure(height_px=5000, width_px=p["min_width_px"] - 1)])) == 1


def test_vector_figure_is_skipped_by_default():
    assert run_rule("RE-20", [make_figure(kind="vector")]) == []
