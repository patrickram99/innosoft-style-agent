"""US-09 · Rule loader: reads rules/innosoft/*.yaml, validates against the JSON Schema and the
additional loader checks of formato-reglas.md §7, and builds an in-memory RuleSet.

Any invalid file raises RuleLoadError (file, index and field in the message) so the API refuses
to start with a half-loaded rule set.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Literal

import jsonschema
import yaml
from pydantic import BaseModel, ConfigDict, Field

from app.rules.registry import EvaluatorRegistry, registry as default_registry

logger = logging.getLogger(__name__)

ALLOWED_MARKERS = {"pagina", "figura", "tabla", "referencia", "encontrado", "esperado", "fragmento"}
MARKER_RE = re.compile(r"\{([^{}]*)\}")
ArticleType = Literal["corto", "original", "revision"]


class RuleLoadError(Exception):
    """Raised when a rules file is invalid. Message names file, index and field."""

    def __init__(self, message: str, *, file: str | None = None, index: int | None = None, field: str | None = None):
        self.file, self.index, self.field = file, index, field
        where = " · ".join(
            part for part in (
                f"archivo {file}" if file else None,
                f"regla #{index}" if index is not None else None,
                f"campo {field}" if field else None,
            ) if part
        )
        super().__init__(f"{where}: {message}" if where else message)


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluador: str
    parametros: dict[str, Any] = Field(default_factory=dict)
    parametros_por_tipo: dict[str, dict[str, Any]] = Field(default_factory=dict)


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documentos: list[str]
    url: str
    referencia: str | None = None


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    categoria: str
    descripcion: str
    condicion: Condition
    severidad: Literal["alta", "media", "baja"]
    detectable: Literal["D", "L", "D/L", "I", "L/I"]
    mensaje: str
    seccion_aplicable: list[ArticleType]
    fuente: Source
    activa: bool = True
    notas: str | None = None
    # Loader-derived fields
    estado: Literal["active", "not_implemented"] = "active"
    archivo: str = ""

    def params_for(self, article_type: str | None) -> dict[str, Any]:
        """`parametros` merged with the entry of `parametros_por_tipo` for the article type (§4.1)."""
        merged = dict(self.condicion.parametros)
        if article_type and article_type in self.condicion.parametros_por_tipo:
            merged.update(self.condicion.parametros_por_tipo[article_type])
        return merged

    def applies_to(self, article_type: str | None) -> bool:
        return article_type is None or article_type in self.seccion_aplicable


class RuleSet(BaseModel):
    rules: list[Rule] = Field(default_factory=list)
    rules_hash: str = ""
    files: list[str] = Field(default_factory=list)

    @property
    def by_id(self) -> dict[str, Rule]:
        return {r.id: r for r in self.rules}

    @property
    def not_implemented(self) -> list[str]:
        return [r.id for r in self.rules if r.estado == "not_implemented"]

    def active(self) -> list[Rule]:
        return [r for r in self.rules if r.activa]

    def runnable(self, article_type: str | None = None) -> list[Rule]:
        """Active, implemented rules that apply to the article type (None = all types)."""
        return [r for r in self.active() if r.estado == "active" and r.applies_to(article_type)]

    def for_section(self, article_type: str | None = None, categoria: str | None = None) -> list[Rule]:
        return [
            r for r in self.active()
            if r.applies_to(article_type) and (categoria is None or r.categoria == categoria)
        ]


def _load_schema(schema_path: Path) -> dict:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" (línea {mark.line + 1}, columna {mark.column + 1})" if mark else ""
        raise RuleLoadError(f"YAML mal formado{where}: {getattr(exc, 'problem', exc)}", file=path.name) from exc


def _validate_schema(data: Any, schema: dict, file: str) -> None:
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errors:
        return
    err = errors[0]
    path = list(err.absolute_path)
    index = path[1] if len(path) > 1 and path[0] == "reglas" and isinstance(path[1], int) else None
    field = ".".join(str(p) for p in path[2:]) if index is not None else ".".join(str(p) for p in path)
    if err.validator == "required":
        missing = err.message.split("'")[1] if "'" in err.message else err.message
        field = f"{field}.{missing}".strip(".")
        raise RuleLoadError(f"falta el campo obligatorio '{missing}'", file=file, index=index, field=field)
    raise RuleLoadError(err.message, file=file, index=index, field=field or None)


def _check_markers(rule: Rule, file: str, index: int) -> None:
    unknown = sorted({m for m in MARKER_RE.findall(rule.mensaje) if m not in ALLOWED_MARKERS})
    if unknown:
        raise RuleLoadError(
            f"marcadores desconocidos en mensaje: {', '.join('{' + m + '}' for m in unknown)}; "
            f"permitidos: {', '.join('{' + m + '}' for m in sorted(ALLOWED_MARKERS))}",
            file=file, index=index, field="mensaje",
        )


def _check_params(rule: Rule, reg: EvaluatorRegistry, file: str, index: int) -> None:
    variants = [rule.condicion.parametros]
    variants += [rule.params_for(t) for t in rule.condicion.parametros_por_tipo]
    for params in variants:
        try:
            reg.validate_params(rule.condicion.evaluador, params)
        except Exception as exc:
            raise RuleLoadError(
                f"parámetros inválidos para el evaluador '{rule.condicion.evaluador}': {exc}",
                file=file, index=index, field="condicion.parametros",
            ) from exc


def load_rules(
    rules_dir: Path | str,
    schema_path: Path | str,
    reg: EvaluatorRegistry | None = None,
) -> RuleSet:
    """Load every *.yaml in `rules_dir` (alphabetical order). Raises RuleLoadError on any invalid file."""
    reg = reg if reg is not None else default_registry
    rules_dir, schema_path = Path(rules_dir), Path(schema_path)
    schema = _load_schema(schema_path)
    files = sorted(rules_dir.glob("*.yaml")) + sorted(rules_dir.glob("*.yml"))
    if not files:
        raise RuleLoadError(f"no hay archivos de reglas en {rules_dir}")

    rules: list[Rule] = []
    seen: dict[str, str] = {}
    normalized: list[str] = []
    for path in files:
        data = _read_yaml(path)
        _validate_schema(data, schema, path.name)
        normalized.append(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
        file_category = data["categoria"]
        for index, raw in enumerate(data["reglas"]):
            rule = Rule.model_validate({**raw, "archivo": path.name})
            if rule.id in seen:
                raise RuleLoadError(
                    f"id duplicado '{rule.id}' (ya definido en {seen[rule.id]})", file=path.name, index=index, field="id"
                )
            seen[rule.id] = path.name
            if rule.categoria != file_category:
                raise RuleLoadError(
                    f"categoria '{rule.categoria}' no coincide con la del archivo ('{file_category}')",
                    file=path.name, index=index, field="categoria",
                )
            _check_markers(rule, path.name, index)
            if rule.condicion.evaluador in reg:
                _check_params(rule, reg, path.name, index)
            else:
                rule.estado = "not_implemented"
                logger.warning(
                    "Regla %s: evaluador '%s' no implementado; se omite", rule.id, rule.condicion.evaluador
                )
            rules.append(rule)

    rules_hash = hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()
    logger.info("Reglas cargadas: %d (%d not_implemented), rules_hash=%s", len(rules), sum(r.estado != "active" for r in rules), rules_hash[:12])
    return RuleSet(rules=rules, rules_hash=rules_hash, files=[p.name for p in files])
