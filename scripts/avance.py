"""Regenera el bloque automático de AVANCE.md (fuente única del avance).

Lee el estado directamente de los artefactos del repositorio, de modo que AVANCE.md nunca
contradiga a las specs, al código ni a las pruebas:

- agente/specs/US-*.md ........... frontmatter (estado_spec, sprint, release, ★) y casillas de la §13
- agente/tests/ .................. funciones de prueba por historia y por regla
- agente/rules/innosoft/*.yaml ... reglas declaradas y evaluador asociado
- agente/app/rules/evaluators/ ... evaluadores registrados (@registry.register)
- agente/app/api/ ................ endpoints implementados vs. los canónicos de 00-producto §8.3
- agente/catalogo_requisitos_innosoft.md ... total de reglas RE del catálogo
- agente/priorizacion_rice_sprint1.xlsx .... calendario de sprints (hoja "Replan 29-sep")
- Tesis-Doc/capitulos/*.tex y anexos/*.tex ... cabecera (% titulo / % estado / % actualizado) y marcas \\pendiente{}
- git log ................. commits por historia (si git está disponible)

Uso (PowerShell, desde la raíz del repositorio, con el entorno de agente/ activo o `pip install pyyaml openpyxl`):
    python scripts/avance.py          # reescribe el bloque AUTO de AVANCE.md
    python scripts/avance.py --check  # sale con código 1 si AVANCE.md está desactualizado

Solo modifica lo que hay entre los marcadores AUTO:INICIO y AUTO:FIN; el resto de AVANCE.md se
edita a mano.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AGENTE = ROOT / "agente"
TESIS = ROOT / "Tesis-Doc"
AVANCE = ROOT / "AVANCE.md"
START = "<!-- AUTO:INICIO (generado por scripts/avance.py; no editar a mano) -->"
END = "<!-- AUTO:FIN -->"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
SDD_PHASES = ["Especificar", "Revisar", "Planificar", "Implementar", "Verificar", "Cerrar"]


def fmt(d: dt.date) -> str:
    return f"{d.day:02d}-{MESES[d.month - 1]}"


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        # Algunas specs tienen comillas sin escapar en el título: se lee línea a línea.
        data: dict = {}
        for line in m.group(1).splitlines():
            km = re.match(r"(\w+):\s*(.*)$", line)
            if km:
                value = re.sub(r"\s+#.*$", "", km.group(2)).strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                data[km.group(1)] = {"true": True, "false": False}.get(value, value)
        return data


def sdd_phase(text: str) -> str:
    done = [p for p in SDD_PHASES if re.search(rf"- \[x\] \*\*{p}\*\*", text, re.I)]
    return done[-1] if done else "—"


def count_tests(path: Path) -> int:
    if not path.exists():
        return 0
    return len(re.findall(r"^\s*(?:async\s+)?def test_", path.read_text(encoding="utf-8"), re.M))


def git_commits() -> dict[str, int]:
    try:
        out = subprocess.run(
            ["git", "log", "--pretty=%s"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    counts: dict[str, int] = {}
    for line in out.splitlines():
        m = re.match(r"(US-\d{2})\b", line)
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return counts


def epic_code(epica: object) -> str:
    code = str(epica).split(".")[0].strip()
    return code if len(code) <= 2 else "T"  # T = transversal


def stories() -> list[dict]:
    commits = git_commits()
    rows = []
    for path in sorted((AGENTE / "specs").glob("US-*.md")):
        fm = frontmatter(path)
        text = path.read_text(encoding="utf-8-sig")
        sid = fm.get("id", path.stem)
        nn = sid.split("-")[1]
        rows.append(
            {
                "id": sid,
                "titulo": fm.get("titulo", ""),
                "epica": epic_code(fm.get("epica", "")),
                "release": fm.get("release", ""),
                "sprint": fm.get("sprint_previsto") if isinstance(fm.get("sprint_previsto"), int) or str(fm.get("sprint_previsto", "")).isdigit() else "—",
                "ws": "★" if fm.get("walking_skeleton") else "",
                "estado": str(fm.get("estado_spec", "")).strip(),
                "fase": sdd_phase(text),
                "tests": count_tests(AGENTE / "tests" / f"test_us_{nn}.py"),
                "commits": commits.get(sid, 0),
            }
        )
    return rows


def registered_evaluators() -> set[str]:
    names: set[str] = set()
    for path in (AGENTE / "app" / "rules" / "evaluators").glob("*.py"):
        names |= set(re.findall(r"register\(\s*[\"'](\w+)[\"']", path.read_text(encoding="utf-8")))
    return names


def rules() -> list[dict]:
    evaluators = registered_evaluators()
    rows = []
    for path in sorted((AGENTE / "rules" / "innosoft").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for r in data.get("reglas", []):
            ev = (r.get("condicion") or {}).get("evaluador", "")
            rows.append(
                {
                    "id": r["id"],
                    "archivo": path.name,
                    "descripcion": r.get("descripcion", ""),
                    "evaluador": ev,
                    "implementada": ev in evaluators,
                    "tests": count_tests(AGENTE / "tests" / "rules" / f"test_{r['id']}.py"),
                }
            )
    return rows


def catalog_rule_count() -> int:
    path = AGENTE / "catalogo_requisitos_innosoft.md"
    if not path.exists():
        return 0
    return len(set(re.findall(r"RE-\d{2}", path.read_text(encoding="utf-8"))))


def endpoints() -> tuple[list[str], list[str]]:
    implemented: set[str] = set()
    for path in (AGENTE / "app" / "api").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        pm = re.search(r"APIRouter\([^)]*prefix=[\"']([^\"']*)", text)
        prefix = pm.group(1) if pm else ""
        for method, route in re.findall(r"@router\.(get|post|put|patch|delete)\(\s*[\"']([^\"']*)", text):
            implemented.add(f"{method.upper()} {prefix}{route}")
    canonical: list[str] = []
    spec = (AGENTE / "specs" / "00-producto.md").read_text(encoding="utf-8")
    section = spec.split("### 8.3", 1)[1].split("###", 1)[0]
    for method, route in re.findall(r"\|\s*`(GET|POST|PUT|PATCH|DELETE) ([^`]+)`", section):
        canonical.append(f"{method} {route.split('?')[0]}")
    norm = {re.sub(r"\{[^}]+\}", "{id}", e) for e in implemented}
    done = [e for e in canonical if re.sub(r"\{[^}]+\}", "{id}", e) in norm]
    return canonical, done


def sprints() -> list[dict]:
    path = AGENTE / "priorizacion_rice_sprint1.xlsx"
    try:
        import openpyxl

        ws = openpyxl.load_workbook(path, data_only=True)["Replan 29-sep"]
    except Exception:  # noqa: BLE001 - el calendario es opcional
        return []
    rows, cols = [], {}
    for r in ws.iter_rows(values_only=True):
        if r and r[0] == "Sprint":
            cols = {name: i for i, name in enumerate(r) if name}
            continue
        if cols and isinstance(r[0], int) and isinstance(r[cols["Inicio"]], dt.datetime):
            rows.append(
                {
                    "n": r[0],
                    "inicio": r[cols["Inicio"]].date(),
                    "fin": r[cols["Fin"]].date(),
                    "historias": r[cols["Historias"]] or "",
                    "meta": r[cols["Meta"]] or "",
                }
            )
    return rows


def tex_header(path: Path) -> dict:
    """Cabecera de un .tex de la tesis: líneas `% clave: valor` al inicio del archivo."""
    data: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:12]:
        m = re.match(r"%\s*(titulo|estado|actualizado):\s*(.*)$", line)
        if m:
            data[m.group(1)] = m.group(2).strip()
    return data


def thesis() -> list[dict]:
    rows = []
    files = sorted((TESIS / "capitulos").glob("*.tex")) + sorted((TESIS / "anexos").glob("*.tex"))
    for path in files:
        fm = tex_header(path)
        text = path.read_text(encoding="utf-8")
        body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("%"))
        rows.append(
            {
                "archivo": path.relative_to(ROOT).as_posix(),
                "titulo": fm.get("titulo", path.stem),
                "estado": fm.get("estado", "—"),
                "actualizado": fm.get("actualizado", "—"),
                "pendientes": len(re.findall(r"\\pendiente\{", body)),
            }
        )
    return rows


def render(today: dt.date) -> str:
    us = stories()
    rs = rules()
    canonical, done = endpoints()
    sp = sprints()
    th = thesis()

    by_state: dict[str, list[str]] = {}
    for s in us:
        by_state.setdefault(s["estado"], []).append(s["id"])
    ws_total = [s for s in us if s["ws"]]
    ws_done = [s for s in ws_total if s["estado"] in ("Implementada", "Verificada")]
    impl_rules = [r for r in rs if r["implementada"]]
    total_tests = sum(count_tests(p) for p in (AGENTE / "tests").rglob("test_*.py"))
    current = next((s for s in sp if s["inicio"] <= today <= s["fin"]), None)

    out = [START, "", f"_Generado el {today.isoformat()}._", "", "### Tablero", "", "| Indicador | Valor |", "|---|---|"]
    if current:
        out.append(
            f"| Sprint en curso | **Sprint {current['n']}** ({fmt(current['inicio'])} → {fmt(current['fin'])}): {current['meta']} |"
        )
    for state in ["Verificada", "Implementada", "Aprobada", "En revisión", "Borrador"]:
        ids = by_state.get(state, [])
        if ids:
            label = {"Verificada": "verificadas", "Implementada": "implementadas", "Aprobada": "aprobadas", "En revisión": "en revisión", "Borrador": "en borrador"}[state]
            listed = " — " + ", ".join(ids) if len(ids) <= 12 else ""
            out.append(f"| Historias {label} | {len(ids)} / {len(us)}{listed} |")
    out.append(f"| Walking skeleton ★ | {len(ws_done)} / {len(ws_total)} implementadas |")
    out.append(
        f"| Reglas con evaluador | {len(impl_rules)} de {len(rs)} declaradas en YAML · {catalog_rule_count()} en el catálogo — {', '.join(r['id'] for r in impl_rules)} |"
    )
    out.append(f"| Endpoints canónicos (§8.3) | {len(done)} / {len(canonical)} — {', '.join(f'`{e}`' for e in done)} |")
    out.append(f"| Funciones de prueba | {total_tests} en `tests/` |")
    if th:
        listos = sum(1 for t in th if t["estado"] in ("revisado", "final"))
        out.append(f"| Tesis: archivos revisados | {listos} / {len(th)} · marcas \\pendiente abiertas: {sum(t['pendientes'] for t in th)} |")

    if current:
        out += ["", f"### Sprint {current['n']} — historias comprometidas", "", "| ID | Historia | Estado spec | Fase SDD |", "|---|---|---|---|"]
        planned = {x.strip(" *") for x in re.split(r"[,+]", current["historias"] or "") if x.strip().startswith("US-")}
        for s in us:
            if s["id"] in planned:
                out.append(f"| [{s['id']}](agente/specs/{s['id']}.md) | {s['titulo']} | {s['estado']} | {s['fase']} |")

    out += [
        "",
        "### Historias",
        "",
        "| ID | Historia | Ép. | Rel. | Sprint | ★ | Estado spec | Fase SDD | Pruebas | Commits |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in us:
        out.append(
            f"| [{s['id']}](agente/specs/{s['id']}.md) | {s['titulo']} | {s['epica']} | {s['release']} | {s['sprint']} | {s['ws']} | {s['estado']} | {s['fase']} | {s['tests'] or ''} | {s['commits'] or ''} |"
        )

    out += ["", "### Reglas declaradas en YAML", "", "| Regla | Archivo | Descripción | Evaluador | Implementada | Pruebas |", "|---|---|---|---|---|---|"]
    for r in rs:
        out.append(
            f"| {r['id']} | `{r['archivo']}` | {r['descripcion']} | `{r['evaluador']}` | {'sí' if r['implementada'] else 'no'} | {r['tests'] or ''} |"
        )

    if sp:
        out += ["", "### Calendario de sprints (fuente: Excel RICE, hoja *Replan 29-sep*)", "", "| Sprint | Fechas | Historias | Meta |", "|---|---|---|---|"]
        for s in sp:
            mark = " ◀ en curso" if s is current else ""
            out.append(f"| {s['n']}{mark} | {fmt(s['inicio'])} → {fmt(s['fin'])} | {s['historias']} | {s['meta']} |")

    if th:
        out += ["", "### Tesis (Tesis-Doc/)", "", "| Parte | Archivo | Estado | Actualizado | \\pendiente |", "|---|---|---|---|---|"]
        for t in th:
            out.append(f"| {t['titulo']} | [{t['archivo']}]({t['archivo']}) | {t['estado']} | {t['actualizado']} | {t['pendientes'] or ''} |")

    out += ["", END]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="no escribe; falla si AVANCE.md está desactualizado")
    parser.add_argument("--fecha", help="fecha de corte AAAA-MM-DD (por defecto, hoy)")
    args = parser.parse_args()
    today = dt.date.fromisoformat(args.fecha) if args.fecha else dt.date.today()

    current = AVANCE.read_text(encoding="utf-8")
    if START not in current or END not in current:
        print(f"AVANCE.md no tiene los marcadores {START!r} y {END!r}", file=sys.stderr)
        return 2
    head, rest = current.split(START, 1)
    tail = rest.split(END, 1)[1]
    old_block = START + rest.split(END, 1)[0] + END

    # --check compara contra la fecha de corte del archivo: el bloque no caduca solo por cambiar de sprint.
    if args.check and not args.fecha:
        stamp = re.search(r"_Generado el (\d{4}-\d{2}-\d{2})\._", old_block)
        if stamp:
            today = dt.date.fromisoformat(stamp.group(1))
    new_block = render(today)

    strip_date = lambda s: re.sub(r"_Generado el .*?_", "", s)  # noqa: E731
    if args.check:
        if strip_date(old_block) != strip_date(new_block):
            print("AVANCE.md está desactualizado: ejecuta python scripts/avance.py", file=sys.stderr)
            return 1
        print("AVANCE.md al día.")
        return 0
    AVANCE.write_text(head + new_block + tail, encoding="utf-8", newline="\n")
    print(f"AVANCE.md actualizado ({today.isoformat()}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
