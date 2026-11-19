"""Synthetic evaluation dataset (D-09).

Usage (PowerShell, from agente/):
    python -m tools.eval_dataset contenido             # text bank with Gemini on Vertex AI (once; versioned)
    python -m tools.eval_dataset generar               # PDFs with LaTeX and Word + evaluacion/manifest.json
    python -m tools.eval_dataset evaluar               # runs the agent through its API → resultados/*.csv
    python -m tools.eval_dataset informe [--tesis]     # resumen.json and charts; --tesis copies them to Tesis-Doc
    python -m tools.eval_dataset todo                  # generar + evaluar + informe
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys

from tools.eval_dataset import CONTENT_BANK, DATASET_DIR, MANIFEST


def cmd_generate(args: argparse.Namespace) -> None:
    from tools.eval_dataset import design, gen_latex, gen_word, verify
    from tools.eval_dataset.content import load_bank

    bank = load_bank()
    docs = design.build_plan(args.latex, args.word, len(bank), seed=args.semilla)
    if args.limpiar:
        shutil.rmtree(DATASET_DIR, ignore_errors=True)
    pdf_dir, meta_dir = DATASET_DIR / "pdf", DATASET_DIR / "meta"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(exist_ok=True)
    thresholds = design.load_thresholds()

    # Resumable: every finished document leaves a sidecar with its plan fingerprint. A rerun skips the documents
    # whose plan has not changed and whose PDF is still there, so the run can be stopped at any time.
    bank_hash = hashlib.sha256(CONTENT_BANK.read_bytes()).hexdigest()
    fingerprint = {d.doc_id: hashlib.sha256((json.dumps(d.to_dict(), sort_keys=True) + bank_hash).encode()).hexdigest() for d in docs}
    pending = []
    for i, doc in enumerate(docs):
        sidecar = meta_dir / f"{doc.doc_id}.json"
        saved = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
        if saved.get("huella") == fingerprint[doc.doc_id] and (pdf_dir / f"{doc.doc_id}.pdf").exists():
            docs[i] = design.doc_from_dict(saved["documento"])
        else:
            pending.append(i)
    print(f"{len(docs) - len(pending)} documentos ya generados; {len(pending)} pendientes, en tandas de {args.lote}.")

    generators = {"latex": (gen_latex.generate, DATASET_DIR / "latex"), "word": (gen_word.generate, DATASET_DIR / "word")}
    done = 0
    for kind, (generate, build) in generators.items():
        indexes = [i for i in pending if docs[i].generator == kind]
        for start in range(0, len(indexes), args.lote):
            batch = [docs[i] for i in indexes[start : start + args.lote]]
            generate(batch, bank, build, pdf_dir)
            for doc in batch:
                sidecar = {"huella": fingerprint[doc.doc_id], "documento": doc.to_dict()}
                (meta_dir / f"{doc.doc_id}.json").write_text(json.dumps(sidecar, ensure_ascii=False), encoding="utf-8")
            done += len(batch)
            print(f"  {kind}: tanda lista, {done}/{len(pending)} pendientes generados", flush=True)
    for doc in docs:  # cheap, so it always runs over every PDF, including those kept from a previous run
        verify.verify_document(doc, pdf_dir / doc.pdf, thresholds)
    figures = [f for d in docs for f in d.figures]
    manifest = {
        "fecha": dt.date.today().isoformat(),
        "semilla": args.semilla,
        "umbrales": thresholds,
        "documentos": [d.to_dict() for d in docs],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    unverified = sum(1 for f in figures if not f.verified)
    print(f"{len(docs)} documentos, {len(figures)} figuras ({unverified} sin verificar) → {MANIFEST}")


def cmd_evaluate(args: argparse.Namespace) -> None:
    from tools.eval_dataset.evaluate import run

    detail, documents = run(repeats=args.repeticiones, fresh=args.limpiar)
    print(f"Resultados en {detail} y {documents}")


def cmd_report(args: argparse.Namespace) -> None:
    from tools.eval_dataset import report

    summary = report.summarize()
    files = report.charts(summary)
    if args.tesis:
        report.copy_to_thesis(files)
    for rule, m in summary["por_regla"].items():
        print(f"{rule}: VP {m['vp']} FP {m['fp']} FN {m['fn']} VN {m['vn']} · precisión {m['precision']:.3f} · recall {m['recall']:.3f} · F1 {m['f1']:.3f}")
    t = summary["tiempo_s"]["global"]
    print(f"Tiempo: mediana {t['mediana']:.3f} s, p95 {t['p95']:.3f} s, máximo {t['max']:.3f} s")


def main() -> int:
    from tools.eval_dataset.design import SEED

    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Dataset sintético de evaluación (D-09)")
    parser.add_argument("accion", choices=["contenido", "generar", "evaluar", "informe", "todo"])
    parser.add_argument("--latex", type=int, default=140, help="documentos generados con LaTeX")
    parser.add_argument("--word", type=int, default=60, help="documentos generados con Word")
    parser.add_argument("--semilla", type=int, default=SEED)
    parser.add_argument("--repeticiones", type=int, default=3, help="envíos por documento para medir el tiempo (mediana)")
    parser.add_argument("--lote", type=int, default=20, help="documentos por tanda al generar; el avance se guarda al cerrar cada tanda")
    parser.add_argument("--limpiar", action="store_true", help="descarta el avance guardado y empieza de cero")
    parser.add_argument("--tesis", action="store_true", help="copia los gráficos a Tesis-Doc/figuras/resultados")
    args = parser.parse_args()
    if args.accion == "contenido":
        from tools.eval_dataset.content import build_bank

        build_bank()
        return 0
    try:
        if args.accion in ("generar", "todo"):
            cmd_generate(args)
        if args.accion in ("evaluar", "todo"):
            cmd_evaluate(args)
        if args.accion in ("informe", "todo"):
            cmd_report(args)
    except KeyboardInterrupt:
        print("\nInterrumpido. El avance quedó guardado: vuelve a ejecutar el mismo comando para continuar.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
