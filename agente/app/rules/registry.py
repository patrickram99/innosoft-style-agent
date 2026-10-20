"""Evaluator registry (formato-reglas.md §1 and §7.3).

A rule names an `evaluador`; the code registers a function under that name together with the
Pydantic model that describes the parameters it requires. Rules whose evaluator is not registered
are loaded as `not_implemented` and skipped with a warning.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict


class EvaluatorParams(BaseModel):
    """Base class for evaluator parameter models. Unknown keys are allowed so YAML can carry notes."""

    model_config = ConfigDict(extra="allow")


EvaluatorFn = Callable[..., list]


@dataclass(frozen=True)
class EvaluatorSpec:
    name: str
    fn: EvaluatorFn
    params_model: type[EvaluatorParams]


class EvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[str, EvaluatorSpec] = {}

    def register(
        self, name: str, params_model: type[EvaluatorParams] = EvaluatorParams
    ) -> Callable[[EvaluatorFn], EvaluatorFn]:
        def decorator(fn: EvaluatorFn) -> EvaluatorFn:
            self._evaluators[name] = EvaluatorSpec(name=name, fn=fn, params_model=params_model)
            return fn

        return decorator

    def get(self, name: str) -> EvaluatorSpec | None:
        return self._evaluators.get(name)

    def __contains__(self, name: object) -> bool:
        return name in self._evaluators

    def names(self) -> list[str]:
        return sorted(self._evaluators)

    def validate_params(self, name: str, params: dict[str, Any]) -> EvaluatorParams:
        return self._evaluators[name].params_model.model_validate(params)


registry = EvaluatorRegistry()
"""Global registry populated by `app.rules.evaluators` modules on import."""
