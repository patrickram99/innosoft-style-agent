"""Evaluator modules. Importing this package registers every evaluator in `app.rules.registry.registry`."""
from app.rules.evaluators import figures  # noqa: F401

__all__ = ["figures"]
