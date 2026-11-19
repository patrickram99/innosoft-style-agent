"""LaTeX generator: writes each manuscript with the journal class (`innosoft.cls`) and compiles it with pdfLaTeX.

The page of every figure is read from the `.aux` file that LaTeX itself writes, so the ground truth never
depends on the PDF library used by the agent.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tools.eval_dataset import TEMPLATES
from tools.eval_dataset.design import DocPlan, FigurePlan
from tools.eval_dataset.images import image_seed, write_image
from tools.eval_dataset.layout import AFFILIATION, Block, compose

CLASS_DIR = TEMPLATES / "Plantilla_Final_InnoSoft"


def prepare_build_dir(build: Path) -> None:
    """Copy the journal class next to the sources, adapted to pdfLaTeX and UTF-8 (the original is not modified).

    The official class targets latex + dvips with EPS figures and Windows-1252 sources; authors who compile
    with pdfLaTeX and PNG/JPEG figures need exactly these two changes.
    """
    (build / "IEEEtran").mkdir(parents=True, exist_ok=True)
    (build / "img").mkdir(exist_ok=True)
    cls = (CLASS_DIR / "innosoft.cls").read_text(encoding="cp1252")
    cls = cls.replace(r"\RequirePackage[dvips]{graphicx}", r"\RequirePackage{graphicx}")
    cls = cls.replace(r"\RequirePackage[ansinew]{inputenc}", r"\RequirePackage[utf8]{inputenc}")
    (build / "innosoft.cls").write_text(cls, encoding="utf-8", newline="\n")
    shutil.copy(CLASS_DIR / "license.png", build / "license.png")
    shutil.copy(CLASS_DIR / "IEEEtran" / "IEEEtran.sty", build / "IEEEtran" / "IEEEtran.sty")


def _graphic(fig: FigurePlan, file: str) -> str:
    w, h = fig.print_w_in, fig.print_h_in
    if fig.variant == "rotada":
        return rf"\rotatebox{{90}}{{\includegraphics[width={h}in,height={w}in]{{img/{file}}}}}"
    if fig.variant == "recortada":
        return rf"\includegraphics[trim=0 0 {fig.crop_right_px}bp 0,clip,width={w}in,height={h}in]{{img/{file}}}"
    return rf"\includegraphics[width={w}in,height={h}in]{{img/{file}}}"


def _tikz(fig: FigurePlan) -> str:
    bars = " ".join(rf"\fill[blue!{30 + 10 * i}] ({1 + 1.6 * i},0) rectangle ({2 + 1.6 * i},{1 + (i * 7 + fig.order * 3) % 4});" for i in range(6))
    return rf"\begin{{tikzpicture}}\draw (0,0) -- (11,0); \draw (0,0) -- (0,5); {bars}\end{{tikzpicture}}"


def _figure(fig: FigurePlan, file: str | None) -> str:
    body = _tikz(fig) if fig.kind == "vector" else _graphic(fig, file)
    number = fig.printed_number
    if fig.caption_defect == "sin_pie":
        caption_below = caption_above = ""
    elif fig.caption_defect == "prefijo_fig":
        caption_above, caption_below = "", rf"\par\vspace{{6pt}}{{\small Fig. {number}: {fig.title}}}\par"
    else:
        caption = rf"\setcounter{{figure}}{{{number - 1}}}\caption{{{fig.title}.}}"
        caption_above, caption_below = (caption, "") if fig.caption_defect == "pie_arriba" else ("", caption)
    return "\n".join([r"\begin{figure}[H]", r"\centering", caption_above, body, caption_below, rf"\label{{figpos:{fig.order}}}", r"\end{figure}"])


def render_tex(doc: DocPlan, header: dict, blocks: list[Block], images: dict[int, str]) -> str:
    out = [
        r"\RequirePackage{tikz}",  # before the class: it redefines \year, which pgf reads while loading
        r"\documentclass{innosoft}",
        r"\usepackage{mathptmx}",
        r"\usepackage{float}",
        r"\begin{document}",
        rf"\def\tipoarticulo{{{header['type_label']}}}",
        r"\def\tematica{Ingeniería de software}",
        r"\def\doi{10.0000/ejemplo}\def\ark{ark:/00000/ejemplo}",
        r"\setcounter{page}{1}",
        rf"\title{{{header['title']}}}",
        rf"\def\englistitle{{{header['title_en']}}}",
        r"\author[1*]{\bf Autor Uno}\author[1]{\bf Autora Dos}\author[1]{\bf Autor Tres}",
        rf"\affil[1]{{{AFFILIATION}}}",
        r"\def\authormail{autor@example.org}",
        r"\maketitle",
        r"\begin{abstract}\par\noindent\vskip -1em",
        header["abstract"],
        rf"\vskip 1em\keywords{{{header['keywords']}}}",
        r"\end{abstract}",
        r"\onehalfspacing\parskip=12pt",
    ]
    for block in blocks:
        if block.kind == "heading":
            out.append(rf"\section*{{{block.text}}}")
        elif block.kind == "figure":
            out.append(_figure(block.figure, images.get(block.figure.order)))
        else:
            out.append(block.text + "\n")
    out.append(r"\end{document}")
    return "\n".join(out) + "\n"


def _aux_pages(aux: str) -> dict[int, int]:
    r"""`\newlabel{figpos:N}{{label}{page}...}` → {N: page}. The first group may contain nested braces."""
    pages: dict[int, int] = {}
    for m in re.finditer(r"\\newlabel\{figpos:(\d+)\}\{", aux):
        i, depth = m.end(), 0
        while True:  # skip the first balanced group
            depth += {"{": 1, "}": -1}.get(aux[i], 0)
            i += 1
            if depth == 0:
                break
        page = re.match(r"\{(\d+)\}", aux[i:])
        if page:
            pages[int(m.group(1))] = int(page.group(1))
    return pages


def _compile(build: Path, doc_id: str) -> tuple[str, str]:
    # No -halt-on-error: the official class raises a harmless "There's no line here to end" inside its title
    # block, exactly as it does for an author. A document counts as failed only if no PDF comes out.
    pdf = build / f"{doc_id}.pdf"
    pdf.unlink(missing_ok=True)
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", f"-jobname={doc_id}", f"{doc_id}.tex"],
        cwd=build, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return doc_id, "" if pdf.exists() else result.stdout


def generate(docs: list[DocPlan], bank: list[dict], build: Path, pdf_dir: Path, workers: int = 4) -> None:
    prepare_build_dir(build)
    for doc in docs:
        header, blocks = compose(doc, bank)
        images = {
            fig.order: write_image(fig, build / "img", f"{doc.doc_id}-f{fig.order}", seed=image_seed(doc.doc_id, fig.order)).name
            for fig in doc.figures if fig.kind == "raster"
        }
        (build / f"{doc.doc_id}.tex").write_text(render_tex(doc, header, blocks, images), encoding="utf-8", newline="\n")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        failures = [(d, log) for d, log in pool.map(lambda d: _compile(build, d.doc_id), docs) if log]
    if failures:
        doc_id, log = failures[0]
        raise RuntimeError(f"pdflatex falló en {len(failures)} documentos; {doc_id}:\n{log[-1500:]}")

    for doc in docs:
        pages = _aux_pages((build / f"{doc.doc_id}.aux").read_text(encoding="utf-8", errors="replace"))
        for fig in doc.figures:
            fig.page = pages[fig.order]
        log = (build / f"{doc.doc_id}.log").read_text(encoding="utf-8", errors="replace")
        doc.pages = int(re.search(r"Output written on .*?\((\d+) pages?", log, re.S).group(1))
        target = pdf_dir / f"{doc.doc_id}.pdf"
        shutil.copy(build / f"{doc.doc_id}.pdf", target)
        doc.pdf = target.name
