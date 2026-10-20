"""formato-reglas.md §14: every active, deterministic and implemented rule has a tests/rules/test_RE-nn.py.

Rules whose evaluator is still `not_implemented` are exempt: they cannot have a positive/negative case yet.
"""
from pathlib import Path

from app.rules import get_rule_set

RULES_TESTS_DIR = Path(__file__).resolve().parent


def test_every_active_deterministic_rule_has_a_test_file():
    missing = []
    for rule in get_rule_set().rules:
        if not rule.activa or rule.estado != "active" or not rule.detectable.startswith("D"):
            continue
        if not (RULES_TESTS_DIR / f"test_{rule.id}.py").exists():
            missing.append(rule.id)
    assert not missing, f"reglas sin archivo de prueba: {missing}"


def test_every_finding_rule_id_exists_in_yaml_catalog():
    ids = set(get_rule_set().by_id)
    assert {"RE-20", "RE-21"} <= ids
