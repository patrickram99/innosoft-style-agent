"""Rule engine package: registry, loader, engine and evaluators."""
from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.rules.engine import EvaluationContext, Finding, RunResult, run_rules
from app.rules.loader import Rule, RuleLoadError, RuleSet, load_rules
from app.rules.registry import registry


@lru_cache
def get_rule_set() -> RuleSet:
    """Rule set loaded from the configured rules directory (validated once per process)."""
    from app.rules import evaluators  # noqa: F401  (registers the evaluators before loading)

    settings = get_settings()
    return load_rules(settings.rules_dir, settings.rules_schema, registry)


def reset_rule_set_cache() -> None:
    get_rule_set.cache_clear()


from app.rules import evaluators  # noqa: E402,F401  (after engine/loader to avoid a circular import)

__all__ = [
    "EvaluationContext", "Finding", "Rule", "RuleLoadError", "RuleSet", "RunResult",
    "get_rule_set", "load_rules", "registry", "reset_rule_set_cache", "run_rules",
]
