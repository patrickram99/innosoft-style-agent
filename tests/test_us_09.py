"""US-09 · Cargar reglas Innosoft desde YAML."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from app.rules.loader import RuleLoadError, load_rules
from app.rules.registry import EvaluatorParams, EvaluatorRegistry
from tests.conftest import ROOT

RULES_DIR = ROOT / "rules" / "innosoft"
SCHEMA = ROOT / "rules" / "schema" / "rule.schema.json"
EXPECTED_IDS = [f"RE-{n}" for n in range(20, 28)]


def _base_rule(**overrides) -> dict:
    rule = {
        "id": "RE-20",
        "categoria": "figuras",
        "descripcion": "Imagen de al menos 531 × 1328 px",
        "condicion": {"evaluador": "figure_min_pixels", "parametros": {"min_height_px": 531, "min_width_px": 1328}},
        "severidad": "alta",
        "detectable": "D",
        "mensaje": "La {figura} (página {pagina}) mide {encontrado}; se requiere {esperado}.",
        "seccion_aplicable": ["corto", "original", "revision"],
        "fuente": {"documentos": ["a"], "url": "https://revistas.ulasalle.edu.pe/innosoft/about/submissions"},
    }
    rule.update(overrides)
    return rule


def _write(tmp_path: Path, name: str, rules: list[dict], categoria: str = "figuras") -> Path:
    data = {"schema_version": 1, "categoria": categoria, "actualizado": "2026-10-02", "reglas": rules}
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


class MinPixelsParams(EvaluatorParams):
    min_height_px: int
    min_width_px: int


@pytest.fixture()
def reg() -> EvaluatorRegistry:
    """Registry with a single dummy evaluator so loader tests do not depend on US-10."""
    r = EvaluatorRegistry()
    r.register("figure_min_pixels", MinPixelsParams)(lambda *a, **k: [])
    return r


def test_t01_real_figuras_yaml_loads_eight_rules():
    rs = load_rules(RULES_DIR, SCHEMA, EvaluatorRegistry())
    assert [r.id for r in rs.rules] == EXPECTED_IDS
    assert rs.files == ["figuras.yaml"]
    assert len(rs.rules_hash) == 64
    assert all(r.categoria == "figuras" for r in rs.rules)


def test_t02_rule_without_id_fails_with_file_and_position(tmp_path: Path, reg):
    rule = _base_rule()
    del rule["id"]
    _write(tmp_path, "figuras.yaml", [_base_rule(id="RE-21"), rule])
    with pytest.raises(RuleLoadError) as exc:
        load_rules(tmp_path, SCHEMA, reg)
    msg = str(exc.value)
    assert "figuras.yaml" in msg and "#1" in msg and "id" in msg


def test_t03_duplicate_ids_across_files_fail(tmp_path: Path, reg):
    _write(tmp_path, "a_figuras.yaml", [_base_rule(id="RE-20")])
    _write(tmp_path, "b_figuras.yaml", [_base_rule(id="RE-20")])
    with pytest.raises(RuleLoadError) as exc:
        load_rules(tmp_path, SCHEMA, reg)
    assert "duplicado" in str(exc.value) and "RE-20" in str(exc.value) and "a_figuras.yaml" in str(exc.value)


def test_t05_unknown_evaluator_loads_as_not_implemented(tmp_path: Path, reg):
    _write(tmp_path, "figuras.yaml", [
        _base_rule(id="RE-20"),
        _base_rule(id="RE-24", condicion={"evaluador": "figure_numbering_sequence"}),
    ])
    rs = load_rules(tmp_path, SCHEMA, reg)
    assert rs.by_id["RE-20"].estado == "active"
    assert rs.by_id["RE-24"].estado == "not_implemented"
    assert rs.not_implemented == ["RE-24"]
    assert [r.id for r in rs.runnable("original")] == ["RE-20"]


def test_category_mismatch_fails(tmp_path: Path, reg):
    _write(tmp_path, "figuras.yaml", [_base_rule(categoria="citas")])
    with pytest.raises(RuleLoadError) as exc:
        load_rules(tmp_path, SCHEMA, reg)
    assert "categoria" in str(exc.value)


def test_unknown_message_marker_fails(tmp_path: Path, reg):
    _write(tmp_path, "figuras.yaml", [_base_rule(mensaje="La {figura} tiene {ancho} px, mínimo {esperado}.")])
    with pytest.raises(RuleLoadError) as exc:
        load_rules(tmp_path, SCHEMA, reg)
    assert "{ancho}" in str(exc.value) and "mensaje" in str(exc.value)


def test_missing_required_parameter_fails(tmp_path: Path, reg):
    _write(tmp_path, "figuras.yaml", [
        _base_rule(condicion={"evaluador": "figure_min_pixels", "parametros": {"min_height_px": 531}})
    ])
    with pytest.raises(RuleLoadError) as exc:
        load_rules(tmp_path, SCHEMA, reg)
    assert "min_width_px" in str(exc.value)


def test_malformed_yaml_reports_line_and_column(tmp_path: Path, reg):
    (tmp_path / "figuras.yaml").write_text("schema_version: 1\ncategoria: figuras\nreglas:\n  - id: RE-20\n   malo: [\n", encoding="utf-8")
    with pytest.raises(RuleLoadError) as exc:
        load_rules(tmp_path, SCHEMA, reg)
    assert "línea" in str(exc.value)


def test_invalid_severity_fails_via_schema(tmp_path: Path, reg):
    _write(tmp_path, "figuras.yaml", [_base_rule(severidad="critica")])
    with pytest.raises(RuleLoadError) as exc:
        load_rules(tmp_path, SCHEMA, reg)
    assert "severidad" in str(exc.value)


def test_rules_hash_changes_when_a_threshold_changes(tmp_path: Path, reg):
    rule = _base_rule()
    _write(tmp_path, "figuras.yaml", [rule])
    h1 = load_rules(tmp_path, SCHEMA, reg).rules_hash
    changed = copy.deepcopy(rule)
    changed["condicion"]["parametros"]["min_width_px"] = 1000
    _write(tmp_path, "figuras.yaml", [changed])
    h2 = load_rules(tmp_path, SCHEMA, reg).rules_hash
    assert h1 != h2


def test_params_per_article_type_are_merged(tmp_path: Path, reg):
    rule = _base_rule(condicion={
        "evaluador": "figure_min_pixels",
        "parametros": {"min_height_px": 531, "min_width_px": 1328},
        "parametros_por_tipo": {"corto": {"min_width_px": 1000}},
    })
    _write(tmp_path, "figuras.yaml", [rule])
    rs = load_rules(tmp_path, SCHEMA, reg)
    assert rs.by_id["RE-20"].params_for("corto") == {"min_height_px": 531, "min_width_px": 1000}
    assert rs.by_id["RE-20"].params_for("original") == {"min_height_px": 531, "min_width_px": 1328}


# --- Integración: GET /rules ---------------------------------------------------------------


def test_ac01_t04_get_rules_section_original_returns_all_eight(client):
    r = client.get("/rules", params={"section": "original"})
    assert r.status_code == 200
    body = r.json()
    assert [x["id"] for x in body["reglas"]] == EXPECTED_IDS
    assert body["total"] == 8
    assert len(body["rules_hash"]) == 64
    assert "not_implemented" in body
    assert all("notas" not in x for x in body["reglas"])


def test_get_rules_filters_by_categoria_and_rejects_bad_section(client):
    assert client.get("/rules", params={"categoria": "citas"}).json()["total"] == 0
    assert client.get("/rules", params={"categoria": "figuras"}).json()["total"] == 8
    assert client.get("/rules", params={"section": "poster"}).status_code == 422


def test_ac03_rule_restricted_to_corto_is_hidden_for_original(tmp_path: Path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import create_app

    _write(tmp_path, "figuras.yaml", [
        _base_rule(id="RE-20"),
        _base_rule(id="RE-21", seccion_aplicable=["corto"]),
    ])
    monkeypatch.setattr(get_settings(), "rules_dir", tmp_path)
    with TestClient(create_app()) as c:
        original = [x["id"] for x in c.get("/rules", params={"section": "original"}).json()["reglas"]]
        corto = [x["id"] for x in c.get("/rules", params={"section": "corto"}).json()["reglas"]]
    assert original == ["RE-20"]
    assert corto == ["RE-20", "RE-21"]


def test_ac02_invalid_rule_file_stops_startup(tmp_path: Path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import create_app

    rule = _base_rule()
    del rule["id"]
    _write(tmp_path, "figuras.yaml", [rule])
    monkeypatch.setattr(get_settings(), "rules_dir", tmp_path)
    with pytest.raises(RuleLoadError) as exc:
        with TestClient(create_app()):
            pass
    assert "figuras.yaml" in str(exc.value)
