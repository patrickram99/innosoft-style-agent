"""RE-21 · Resolución efectiva ≥ 300 dpi. Umbral leído de rules/innosoft/figuras.yaml."""
from app.rules import get_rule_set
from tests.rules.helpers import make_figure, run_rule


def _min_dpi() -> float:
    return get_rule_set().by_id["RE-21"].params_for("original")["min_dpi"]


def test_positive_300_dpi_has_no_finding():
    assert run_rule("RE-21", [make_figure(dpi=_min_dpi())]) == []
    assert run_rule("RE-21", [make_figure(dpi=600)]) == []


def test_negative_150_dpi_fails_with_high_severity():
    (finding,) = run_rule("RE-21", [make_figure(dpi=150, page=2, number=2)])
    assert finding.rule_id == "RE-21"
    assert finding.severidad == "alta"
    assert finding.pagina == 2
    assert finding.valor_encontrado == "≈ 150 dpi"
    assert finding.valor_esperado == "≥ 300 dpi"


def test_negative_uses_the_lower_axis():
    fig = make_figure(dpi=300)
    fig.dpi_y = 200.0
    (finding,) = run_rule("RE-21", [fig])
    assert finding.valor_encontrado == "≈ 200 dpi"


def test_vector_figure_not_applicable():
    assert run_rule("RE-21", [make_figure(kind="vector")]) == []
