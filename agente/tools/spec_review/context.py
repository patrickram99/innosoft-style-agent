"""Build the review context for one story spec and write the outcome back. No network access here."""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # agente/
SPECS = ROOT / "specs"
REVIEWS = SPECS / "revisiones"
CATALOG = ROOT / "catalogo_requisitos_innosoft.md"
RULES_DIR = ROOT / "rules" / "innosoft"
FORBIDDEN = ROOT / "muestras"  # real manuscripts with personal data (Ley N.º 29733)

REVIEWED_STATE = "Revisada (IA)"
MAX_CONTEXT_CHARS = 120_000  # hard cap on what one review sends to the model


def _read(path: Path) -> str:
    path = path.resolve()
    if path.is_relative_to(FORBIDDEN.resolve()):
        raise PermissionError(f"El revisor no puede leer {path}: muestras/ contiene datos personales")
    return path.read_text(encoding="utf-8-sig")


def normalize_id(raw: str) -> str:
    m = re.fullmatch(r"(?:US-?)?(\d{1,2})", raw.strip(), re.I)
    if not m:
        raise ValueError(f"Identificador de historia no válido: {raw!r} (usa US-05 o 05)")
    return f"US-{int(m.group(1)):02d}"


def frontmatter_list(text: str, key: str) -> list[str]:
    m = re.search(rf"^{key}:\s*\[(.*?)\]", text, re.M)
    return [x.strip().strip("\"'") for x in m.group(1).split(",") if x.strip()] if m else []


def spec_state(text: str) -> str:
    m = re.search(r"^estado_spec:\s*([^#\n]+)", text, re.M)
    return m.group(1).strip() if m else ""


def catalog_excerpt(rule_ids: set[str]) -> str:
    """Lines of the requirements catalog that mention any of the given RE-nn ids."""
    if not rule_ids or not CATALOG.exists():
        return ""
    pattern = re.compile("|".join(sorted(re.escape(r) for r in rule_ids)))
    return "\n".join(line for line in _read(CATALOG).splitlines() if pattern.search(line))


def build_context(story_id: str) -> str:
    """Spec under review plus what it must be consistent with: product spec, dependencies, catalog rules and YAML rules."""
    spec_path = SPECS / f"{story_id}.md"
    spec = _read(spec_path)
    parts = [f"# SPEC EN REVISIÓN: {story_id}\n\n{spec}"]
    parts.append("# SPEC DE PRODUCTO (prevalece sobre la spec de historia)\n\n" + _read(SPECS / "00-producto.md"))
    for dep in frontmatter_list(spec, "depende_de"):
        dep_path = SPECS / f"{dep}.md"
        if dep_path.exists() and dep != story_id:
            parts.append(f"# SPEC DE LA QUE DEPENDE: {dep} (estado: {spec_state(_read(dep_path))})\n\n" + _read(dep_path))
    rule_ids = set(re.findall(r"RE-\d{2}", spec))
    excerpt = catalog_excerpt(rule_ids)
    if excerpt:
        parts.append("# CATÁLOGO DE REQUISITOS: líneas de las reglas citadas\n\n" + excerpt)
    declared = [f"## {p.name}\n\n{_read(p)}" for p in sorted(RULES_DIR.glob("*.yaml"))]
    if declared:
        parts.append("# REGLAS YA DECLARADAS EN YAML\n\n" + "\n\n".join(declared))
    context = "\n\n---\n\n".join(parts)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n[contexto truncado por el tope de tamaño]"
    return context


VERDICT_LABEL = {"favorable": "Favorable", "con_observaciones": "Con observaciones", "bloqueante": "Bloqueante"}


def render_report(story_id: str, verdict: dict, reviews: dict[str, str], model: str, tokens: int, today: dt.date) -> str:
    lines = [
        f"# Revisión multiagente de {story_id}",
        "",
        "| Campo | Valor |",
        "|---|---|",
        f"| Fecha | {today.isoformat()} |",
        f"| Veredicto | **{VERDICT_LABEL.get(verdict['veredicto'], verdict['veredicto'])}** |",
        f"| Modelo | `{model}` (Vertex AI, Google ADK) |",
        f"| Tokens consumidos | {tokens} |",
        "| Ratificación del equipo | Pendiente |",
        "",
        "> Informe generado por `tools/spec_review` (decisión D-07). Es una revisión asistida por IA: el equipo la ratifica u",
        "> observa antes de que la spec pase a `Aprobada`.",
        "",
        "## Resumen",
        "",
        verdict["resumen"].strip(),
        "",
        "## Observaciones",
        "",
    ]
    if verdict["observaciones"]:
        lines += ["| # | Severidad | Sección | Observación | Corrección propuesta |", "|---|---|---|---|---|"]
        for i, o in enumerate(verdict["observaciones"], start=1):
            cells = [str(o.get(k, "")).replace("|", "\\|").replace("\n", " ") for k in ("severidad", "seccion", "descripcion", "correccion")]
            lines.append(f"| {i} | " + " | ".join(cells) + " |")
    else:
        lines.append("Sin observaciones.")
    titles = {"consistencia": "Dictamen de consistencia", "testabilidad": "Dictamen de testabilidad", "alcance": "Dictamen de alcance y reglas"}
    for key, title in titles.items():
        lines += ["", f"## {title}", "", reviews.get(key, "").strip() or "_Sin dictamen._"]
    return "\n".join(lines) + "\n"


def mark_reviewed(story_id: str, today: dt.date) -> bool:
    """Move a `Borrador` spec to `Revisada (IA)`. Returns False if the spec was in another state."""
    path = SPECS / f"{story_id}.md"
    text = _read(path)
    if spec_state(text) != "Borrador":
        return False
    text = re.sub(r"^(estado_spec:\s*)Borrador", rf"\g<1>{REVIEWED_STATE}", text, count=1, flags=re.M)
    row = f"| — | {today.isoformat()} | Revisor multiagente | Veredicto favorable (`specs/revisiones/{story_id}.md`): pasa a `{REVIEWED_STATE}`. |\n"
    path.write_text(text.rstrip("\n") + "\n" + row, encoding="utf-8", newline="\n")
    return True
