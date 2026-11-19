"""Run the agent over the dataset through its API and compare its findings with the ground truth.

The agent is exercised as a black box: `POST /manuscripts`, then `GET /manuscripts/{id}/findings`. A scratch
SQLite database and storage folder are used, so the evaluation never touches development data.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

from tools.eval_dataset import DATASET_DIR, MANIFEST, RESULTS_DIR, ROOT, RULES_FILE
from tools.eval_dataset.layout import SECTION_ID
from tools.eval_dataset.stats import outcome

RULES = ["RE-20", "RE-21"]  # rules with an evaluator today; extend as new evaluators land
TOKEN = "eval-token"
DETAIL_FIELDS = [
    "doc_id", "generador", "figura", "pagina", "variante", "regla", "verdad", "prediccion", "resultado",
    "verdad_fuente", "px_visible", "dpi_autor", "px_pdf", "valor_agente",
]
DOC_FIELDS = ["doc_id", "generador", "perfil", "tipo", "paginas", "figuras", "kb", "estado", "hallazgos", "segundos"]


def _client(scratch: Path):
    """In-process API client on a throwaway database (same approach as tests/conftest.py)."""
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{(scratch / 'eval.sqlite').as_posix()}"
    os.environ["AGENT_SERVICE_TOKEN"] = TOKEN
    os.environ["STORAGE_DIR"] = str(scratch / "storage")

    from alembic import command
    from alembic.config import Config
    from fastapi.testclient import TestClient

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    command.upgrade(cfg, "head")

    from app.main import app

    return TestClient(app)


def match_findings(figures: list[dict], findings: list[dict]) -> tuple[dict[tuple[int, str], dict], list[dict]]:
    """Assign each finding to a planned figure. Returns ({(figure order, rule): finding}, unmatched findings).

    A finding is matched by page and caption number; a finding without number goes to the first free figure of
    that page without a caption, then to any free figure of that page. What is left over is a spurious finding.
    """
    matched: dict[tuple[int, str], dict] = {}
    spurious: list[dict] = []
    for finding in sorted(findings, key=lambda f: (f["pagina"] or 0, (f["ubicacion"] or {}).get("posicion") or 0)):
        rule, page = finding["rule_id"], finding["pagina"]
        number = (finding.get("ubicacion") or {}).get("numero")
        on_page = [f for f in figures if f["page"] == page and (f["order"], rule) not in matched]
        target = None
        if number is not None:
            target = next((f for f in on_page if f["printed_number"] == number), None)
        if target is None:
            target = next((f for f in on_page if f["printed_number"] is None), None)
        if target is None and number is None and on_page:
            target = on_page[0]
        if target is None:
            spurious.append(finding)
        else:
            matched[(target["order"], rule)] = finding
    return matched, spurious


def evaluate_document(doc: dict, findings: list[dict], rules: list[str] = RULES) -> list[dict]:
    """One row per (figure, rule) where the rule applies, plus one FP row per spurious finding."""
    relevant = [f for f in findings if f["rule_id"] in rules]
    matched, spurious = match_findings(doc["figures"], relevant)
    rows: list[dict] = []
    for fig in doc["figures"]:
        for rule in rules:
            finding = matched.get((fig["order"], rule))
            truth = (fig.get("truth") or {}).get(rule)
            if not fig.get("verified"):
                continue  # the stored image could not be located: no ground truth for this figure
            if truth is None and finding is None:
                continue  # rule not applicable (vector figure) and the agent agreed
            rows.append(
                {
                    "doc_id": doc["doc_id"], "generador": doc["generator"], "figura": fig["order"], "pagina": fig["page"],
                    "variante": fig["variant"], "regla": rule, "verdad": int(bool(truth)), "prediccion": int(finding is not None),
                    "resultado": outcome(bool(truth), finding is not None),
                    "verdad_fuente": "" if fig["truth_source"].get(rule) is None else int(fig["truth_source"][rule]),
                    "px_visible": f"{fig['visible_h_px']}x{fig['visible_w_px']}" if fig["kind"] == "raster" else "",
                    "dpi_autor": fig["dpi"] or "",
                    "px_pdf": f"{fig['embedded_h_px']}x{fig['embedded_w_px']}" if fig.get("embedded_w_px") else "",
                    "valor_agente": finding["valor_encontrado"] if finding else "",
                }
            )
    for finding in spurious:
        rows.append(
            {
                "doc_id": doc["doc_id"], "generador": doc["generator"], "figura": "", "pagina": finding["pagina"],
                "variante": "espurio", "regla": finding["rule_id"], "verdad": 0, "prediccion": 1, "resultado": "FP",
                "verdad_fuente": "", "px_visible": "", "dpi_autor": "", "px_pdf": "", "valor_agente": finding["valor_encontrado"],
            }
        )
    return rows


def run(repeats: int = 3, fresh: bool = False) -> tuple[Path, Path]:
    """Evaluate every document of the manifest. Resumable: each evaluated document is cached on disk, keyed by
    its PDF, its ground truth, the rules file and the number of repetitions, so a rerun only does what is missing."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pdf_dir, cache_dir = DATASET_DIR / "pdf", DATASET_DIR / "eval"
    if fresh:
        shutil.rmtree(cache_dir, ignore_errors=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # The cache is tied to the rules and to the agent's code: after any change in app/ everything is re-evaluated.
    agent = hashlib.sha256(RULES_FILE.read_bytes())
    for source in sorted((ROOT / "app").rglob("*.py")):
        agent.update(source.read_bytes())
    rules_hash = agent.hexdigest()
    detail: list[dict] = []
    documents: list[dict] = []
    headers = {"Authorization": f"Bearer {TOKEN}"}
    todo = len(manifest["documentos"])
    with _client(DATASET_DIR / "scratch") as client:
        submission = 0
        for index, doc in enumerate(manifest["documentos"], start=1):
            content = (pdf_dir / doc["pdf"]).read_bytes()
            key = hashlib.sha256(content + json.dumps(doc, sort_keys=True).encode() + f"{rules_hash}{repeats}".encode()).hexdigest()
            cache = cache_dir / f"{doc['doc_id']}.json"
            saved = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
            if saved.get("clave") == key:
                detail += saved["detalle"]
                documents.append(saved["documento"])
                continue
            seconds: list[float] = []
            body = None
            for _ in range(repeats):  # each repetition is a new submission, so the analysis really runs again
                submission += 1
                meta = {"submission_id": submission, "section_id": SECTION_ID[doc["article_type"]], "title": doc["doc_id"], "locale": "es_ES"}
                start = time.perf_counter()
                # The in-process client returns after the background analysis has finished.
                response = client.post("/manuscripts", headers=headers, files={"file": (doc["pdf"], content, "application/pdf")}, data={"metadata": json.dumps(meta)})
                seconds.append(time.perf_counter() - start)
                response.raise_for_status()
                body = client.get(f"/manuscripts/{response.json()['manuscript_id']}/findings", headers=headers).json()
            rows = evaluate_document(doc, body["findings"])
            row = {
                "doc_id": doc["doc_id"], "generador": doc["generator"], "perfil": doc["profile"], "tipo": doc["article_type"],
                "paginas": doc["pages"], "figuras": len(doc["figures"]), "kb": round(len(content) / 1024, 1),
                "estado": body["status"], "hallazgos": body["total"], "segundos": round(sorted(seconds)[len(seconds) // 2], 4),
            }
            cache.write_text(json.dumps({"clave": key, "detalle": rows, "documento": row}, ensure_ascii=False), encoding="utf-8")
            detail += rows
            documents.append(row)
            if index % 20 == 0 or index == todo:
                print(f"  evaluados {index}/{todo}", flush=True)
    detail_csv, docs_csv = RESULTS_DIR / "detalle.csv", RESULTS_DIR / "documentos.csv"
    for path, fields, rows in [(detail_csv, DETAIL_FIELDS, detail), (docs_csv, DOC_FIELDS, documents)]:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return detail_csv, docs_csv
