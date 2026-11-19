"""Summary of the evaluation: metrics per rule with confidence intervals and tests, timings and charts."""
from __future__ import annotations

import csv
import json
from collections import defaultdict

from tools.eval_dataset import MANIFEST, RESULTS_DIR, ROOT
from tools.eval_dataset.evaluate import RULES
from tools.eval_dataset.stats import Confusion, binom_test_greater, describe, fisher_exact, linear_fit, spearman, wilson

TARGETS = {"precision": 0.85, "recall": 0.75}  # 00-producto.md §1, deterministic rules


def _read(name: str) -> list[dict]:
    with (RESULTS_DIR / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _metrics(c: Confusion) -> dict:
    out = {"vp": c.tp, "fp": c.fp, "fn": c.fn, "vn": c.tn, "precision": c.precision, "recall": c.recall, "f1": c.f1,
           "especificidad": c.specificity, "exactitud": c.accuracy}
    out["ic95_precision"] = wilson(c.tp, c.tp + c.fp)
    out["ic95_recall"] = wilson(c.tp, c.tp + c.fn)
    out["p_precision_mayor_meta"] = binom_test_greater(c.tp, c.tp + c.fp, TARGETS["precision"])
    out["p_recall_mayor_meta"] = binom_test_greater(c.tp, c.tp + c.fn, TARGETS["recall"])
    return out


def _confusions(rows: list[dict], key) -> dict[str, Confusion]:
    table: dict[str, Confusion] = defaultdict(Confusion)
    for row in rows:
        table[key(row)].add(row["resultado"])
    return table


def summarize() -> dict:
    detail, documents = _read("detalle.csv"), _read("documentos.csv")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    figures = [f for d in manifest["documentos"] for f in d["figures"]]
    raster = [f for f in figures if f["kind"] == "raster"]

    by_rule = {rule: _metrics(c) for rule, c in sorted(_confusions(detail, lambda r: r["regla"]).items())}
    overall = Confusion()
    for row in detail:
        overall.add(row["resultado"])
    by_generator = {
        rule: {gen: _metrics(c) for gen, c in sorted(_confusions([r for r in detail if r["regla"] == rule], lambda r: r["generador"]).items())}
        for rule in RULES
    }
    by_variant = {
        rule: {
            var: {"vp": c.tp, "fp": c.fp, "fn": c.fn, "vn": c.tn, "errores": c.fp + c.fn, "n": c.tp + c.fp + c.fn + c.tn}
            for var, c in sorted(_confusions([r for r in detail if r["regla"] == rule], lambda r: r["variante"]).items())
        }
        for rule in RULES
    }

    # Is the error rate different between generators? (Fisher exact test on correct vs. wrong decisions)
    generator_test = {}
    for rule in RULES:
        cells = {gen: _confusions([r for r in detail if r["regla"] == rule and r["generador"] == gen], lambda r: "x").get("x", Confusion()) for gen in ("latex", "word")}
        a, b = cells["latex"].fp + cells["latex"].fn, cells["latex"].tp + cells["latex"].tn
        c, d = cells["word"].fp + cells["word"].fn, cells["word"].tp + cells["word"].tn
        generator_test[rule] = {"latex_errores": a, "latex_aciertos": b, "word_errores": c, "word_aciertos": d, "p_fisher": fisher_exact(a, b, c, d)}

    # Effect of the conversion to PDF: figures that comply at the source but not in the PDF.
    conversion = {}
    for gen in ("latex", "word"):
        figs = [f for d in manifest["documentos"] if d["generator"] == gen for f in d["figures"] if f["kind"] == "raster" and f["verified"]]
        conversion[gen] = {
            "figuras": len(figs),
            "remuestreadas": sum(1 for f in figs if f["embedded_w_px"] < f["source_w_px"] and not f["crop_right_px"]),
            **{f"{rule}_cumple_fuente_incumple_pdf": sum(1 for f in figs if f["truth_source"][rule] is False and f["truth"][rule] is True) for rule in RULES},
            **{f"{rule}_cumple_fuente": sum(1 for f in figs if f["truth_source"][rule] is False) for rule in RULES},
        }

    seconds = [float(d["segundos"]) for d in documents]
    pages = [float(d["paginas"]) for d in documents]
    n_figs = [float(d["figuras"]) for d in documents]
    summary = {
        "fecha": manifest["fecha"],
        "semilla": manifest["semilla"],
        "umbrales": manifest["umbrales"],
        "metas": TARGETS,
        "dataset": {
            "documentos": len(documents),
            "por_generador": {g: sum(1 for d in documents if d["generador"] == g) for g in ("latex", "word")},
            "por_perfil": {p: sum(1 for d in documents if d["perfil"] == p) for p in ("conforme", "un_defecto", "varios")},
            "por_tipo": {t: sum(1 for d in documents if d["tipo"] == t) for t in ("corto", "original", "revision")},
            "paginas": describe(pages),
            "figuras": len(figures),
            "figuras_raster": len(raster),
            "figuras_vectoriales": len(figures) - len(raster),
            "figuras_sin_verificar": sum(1 for f in figures if not f["verified"]),
            "figuras_por_variante": {v: sum(1 for f in figures if f["variant"] == v) for v in sorted({f["variant"] for f in figures})},
            "figuras_por_documento": describe(n_figs),
            "incumplimientos_pdf": {rule: sum(1 for f in raster if f["verified"] and f["truth"][rule]) for rule in RULES},
            "incumplimientos_fuente": {rule: sum(1 for f in raster if f["truth_source"][rule]) for rule in RULES},
            "defectos_no_evaluados": {
                "RE-23_pie": sum(1 for f in figures if f["caption_defect"]),
                "RE-24_numeracion": sum(1 for d in manifest["documentos"] if d["numbering_skip"]),
                "RE-25_sin_mencion": sum(1 for f in figures if not f["referenced"]),
            },
        },
        "estados": {s: sum(1 for d in documents if d["estado"] == s) for s in sorted({d["estado"] for d in documents})},
        "por_regla": by_rule,
        "global": _metrics(overall),
        "por_generador": by_generator,
        "por_variante": by_variant,
        "prueba_generador": generator_test,
        "conversion_pdf": conversion,
        "tiempo_s": {
            "global": describe(seconds),
            "por_generador": {g: describe([float(d["segundos"]) for d in documents if d["generador"] == g]) for g in ("latex", "word")},
            "spearman_paginas": spearman(pages, seconds),
            "spearman_figuras": spearman(n_figs, seconds),
            "ajuste_lineal_paginas": linear_fit(pages, seconds),
            "ajuste_lineal_figuras": linear_fit(n_figs, seconds),
        },
        "errores": [r for r in detail if r["resultado"] in ("FP", "FN")],
    }
    (RESULTS_DIR / "resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return summary


def charts(summary: dict) -> list[str]:
    """PNG charts for the thesis (300 dpi, wide enough to satisfy the journal's own figure rules)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    out_dir = RESULTS_DIR / "figuras"
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "serif", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    files: list[str] = []
    comma = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ","))  # decimal comma (Spanish)

    def save(fig, name: str) -> None:
        fig.tight_layout()
        fig.savefig(out_dir / name, dpi=300)
        plt.close(fig)
        files.append(name)

    # 1. Precision and recall per rule with 95 % Wilson intervals and the targets.
    fig, ax = plt.subplots(figsize=(7, 3.6))
    rules = list(summary["por_regla"])
    for offset, (metric, label, color) in enumerate([("precision", "Precisión", "#1f77b4"), ("recall", "Recall", "#ff7f0e")]):
        values = [summary["por_regla"][r][metric] or 0 for r in rules]
        cis = [summary["por_regla"][r][f"ic95_{metric}"] or (0, 0) for r in rules]
        xs = [i + (offset - 0.5) * 0.36 for i in range(len(rules))]
        errs = [[max(0.0, v - lo) for v, (lo, _) in zip(values, cis)], [max(0.0, hi - v) for v, (_, hi) in zip(values, cis)]]
        ax.bar(xs, values, width=0.34, color=color, label=label, yerr=errs, capsize=4)
        for x, v in zip(xs, values):
            ax.text(x, 0.03, f"{v:.3f}".replace(".", ","), ha="center", color="white", fontsize=10)
    ax.axhline(TARGETS["precision"], color="#1f77b4", ls="--", lw=1, label="Meta de precisión (0,85)")
    ax.axhline(TARGETS["recall"], color="#ff7f0e", ls="--", lw=1, label="Meta de recall (0,75)")
    ax.set_xticks(range(len(rules)), rules)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Proporción")
    ax.yaxis.set_major_formatter(comma)
    ax.legend(loc="lower left", ncols=2, frameon=False, fontsize=9, bbox_to_anchor=(0, 1.0))
    save(fig, "metricas-por-regla.png")

    # 2. Errors per figure variant.
    fig, axes = plt.subplots(1, len(RULES), figsize=(7, 3.4), sharey=True)
    for ax, rule in zip(axes, RULES):
        data = summary["por_variante"][rule]
        names = list(data)
        ax.barh(names, [data[n]["vp"] + data[n]["vn"] for n in names], color="#9ecae1", label="Aciertos")
        ax.barh(names, [data[n]["fp"] for n in names], left=[data[n]["vp"] + data[n]["vn"] for n in names], color="#d62728", label="Falsos positivos")
        ax.barh(names, [data[n]["fn"] for n in names], left=[data[n]["vp"] + data[n]["vn"] + data[n]["fp"] for n in names], color="#ff7f0e", label="Falsos negativos")
        ax.set_title(rule, fontsize=11)
        ax.set_xlabel("Decisiones (figura, regla)")
    axes[0].legend(loc="lower right", fontsize=8, frameon=False)
    save(fig, "errores-por-variante.png")

    # 3. Analysis time against pages.
    documents = _read("documentos.csv")
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for gen, color, label in [("latex", "#1f77b4", "LaTeX"), ("word", "#2ca02c", "Word")]:
        rows = [d for d in documents if d["generador"] == gen]
        ax.scatter([int(d["paginas"]) for d in rows], [float(d["segundos"]) for d in rows], s=14, color=color, label=label, alpha=0.7)
    fit = summary["tiempo_s"]["ajuste_lineal_paginas"]
    xs = [min(int(d["paginas"]) for d in documents), max(int(d["paginas"]) for d in documents)]
    ax.plot(xs, [fit["intercepto"] + fit["pendiente"] * x for x in xs], color="black", lw=1, ls="--", label="Ajuste lineal")
    ax.set_xlabel("Páginas del manuscrito")
    ax.set_ylabel("Tiempo de análisis (s)")
    ax.yaxis.set_major_formatter(comma)
    ax.legend(frameon=False, fontsize=9)
    save(fig, "tiempo-por-paginas.png")
    return files


def copy_to_thesis(files: list[str]) -> None:
    """The thesis keeps copies of the charts, like it does with the diagrams of docs/diagramas/."""
    import shutil

    target = ROOT.parent / "Tesis-Doc" / "figuras" / "resultados"
    target.mkdir(parents=True, exist_ok=True)
    for name in files:
        shutil.copy(RESULTS_DIR / "figuras" / name, target / name)
