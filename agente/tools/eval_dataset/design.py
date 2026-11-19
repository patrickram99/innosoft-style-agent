"""Experimental design of the synthetic dataset: which documents exist and which defects each one carries.

Everything here is pure Python driven by a seed, so the ground truth is known by construction and the same
seed always yields the same plan. Nothing in this module reads a PDF or imports `app/`: the ground truth is
defined from what the author of the document did (image size, printed size, crop, rotation), not from what
the agent extracts.
"""
from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field

import yaml

from tools.eval_dataset import RULES_FILE

SEED = 20261118
MAX_PRINT_W_IN = 7.0  # text width of the journal template is 7.24 in
MAX_PRINT_H_IN = 5.5

# (width_px, height_px) of the VISIBLE image and printed resolution. The lists include values on both sides of
# the thresholds of RE-20 (531 x 1328 px) and RE-21 (300 dpi); the ground truth is not taken from these labels
# but recomputed from the values with the thresholds of the YAML (see `truth`).
PX_OK = [(2000, 800), (1600, 640), (1400, 600), (2400, 1200), (1328, 531), (1330, 532), (1800, 900), (1500, 1000)]
PX_SMALL = [(600, 300), (1000, 400), (1200, 500), (1327, 531), (1328, 530), (1300, 700), (900, 900), (800, 600)]
PX_NARROW = [(1327, 531), (1300, 700), (1200, 640), (900, 900)]  # tall enough, too narrow: used for cropped figures
MIN_SOURCE_W_FOR_CROP = 1400  # a cropped "re20" figure embeds an image at least this wide (above the RE-20 width)
PX_TINY =[(500, 250), (600, 300), (1000, 400), (1200, 500), (800, 600)]
DPI_OK = [300, 300, 300, 301, 302, 305, 350, 400, 600]
DPI_LOW = [72, 96, 150, 200, 220, 250, 280, 295, 298, 299]

PROFILES = [("conforme", 0.20), ("un_defecto", 0.50), ("varios", 0.30)]
VARIANTS = {
    # variant: weight per generator. Word documents only carry plain raster figures: Word resamples and re-encodes
    # cropped images on export in a way that cannot be traced back to the source pixels.
    "latex": [("png", 0.52), ("jpeg", 0.14), ("png_alfa", 0.08), ("recortada", 0.09), ("rotada", 0.09), ("vectorial", 0.08)],
    "word": [("png", 0.68), ("jpeg", 0.22), ("png_alfa", 0.10)],
}
CAPTION_DEFECTS = ["sin_pie", "pie_arriba", "prefijo_fig"]  # RE-23, not evaluated by the agent yet


@dataclass
class FigurePlan:
    order: int  # position among the figures of the document (1..n)
    printed_number: int | None  # number shown in the caption; None when the figure has no caption
    variant: str  # png | jpeg | png_alfa | recortada | rotada | vectorial
    kind: str  # raster | vector
    title: str = ""
    visible_w_px: int | None = None  # what the reader sees (after crop and rotation)
    visible_h_px: int | None = None
    source_w_px: int | None = None  # the image file embedded in the document
    source_h_px: int | None = None
    crop_right_px: int = 0
    rotated: bool = False
    dpi: float | None = None  # resolution the author chose: visible pixels / printed inches
    print_w_in: float | None = None
    print_h_in: float | None = None
    caption_defect: str | None = None
    referenced: bool = True
    page: int | None = None  # filled by the generator from LaTeX (.aux) or Word (COM), never from the agent
    truth_source: dict = field(default_factory=dict)  # by construction, from the image the author embedded
    embedded_w_px: int | None = None  # image stored in the PDF, read with pypdf (see verify.py)
    embedded_h_px: int | None = None
    verified: bool | None = None  # the embedded image was located in the PDF on the expected page
    truth: dict = field(default_factory=dict)  # at PDF level: {"RE-20": True|False|None, ...}; None = not applicable


@dataclass
class DocPlan:
    doc_id: str
    generator: str  # latex | word
    profile: str
    article_type: str
    article_index: int  # index in the Gemini text bank
    body_blocks: int  # extra paragraphs, controls the number of pages
    figures: list[FigurePlan]
    numbering_skip: bool = False  # RE-24, not evaluated yet
    pages: int | None = None
    pdf: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def doc_from_dict(data: dict) -> DocPlan:
    """Inverse of `DocPlan.to_dict`, used to resume an interrupted generation."""
    return DocPlan(**{**data, "figures": [FigurePlan(**f) for f in data["figures"]]})


def load_thresholds() -> dict:
    """Thresholds of RE-20 and RE-21 from the rules YAML (RNF-05: no editorial number lives in code)."""
    rules = {r["id"]: r for r in yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))["reglas"]}
    p20 = rules["RE-20"]["condicion"]["parametros"]
    return {
        "min_height_px": p20["min_height_px"],
        "min_width_px": p20["min_width_px"],
        "min_dpi": rules["RE-21"]["condicion"]["parametros"]["min_dpi"],
    }


def truth(fig: FigurePlan, th: dict, *, resampled_px: tuple[int, int] | None = None) -> dict:
    """Ground truth of one figure: True = the figure violates the rule, None = the rule does not apply.

    `resampled_px` is the (width, height) of the image stored in the PDF when the converter resampled it (Word
    does). It replaces the pixels of the source image; the printed size does not change.
    """
    if fig.kind != "raster":
        return {"RE-20": None, "RE-21": None}
    if resampled_px is None:
        w, h, dpi = fig.visible_w_px, fig.visible_h_px, fig.dpi
    else:
        w, h = resampled_px
        dpi = min(w / fig.print_w_in, h / fig.print_h_in)
    return {"RE-20": h < th["min_height_px"] or w < th["min_width_px"], "RE-21": dpi < th["min_dpi"]}


def _weighted(rng: random.Random, options: list[tuple[str, float]]) -> str:
    return rng.choices([o for o, _ in options], weights=[w for _, w in options], k=1)[0]


def _fits(px: tuple[int, int], dpi: float) -> bool:
    return px[0] / dpi <= MAX_PRINT_W_IN and px[1] / dpi <= MAX_PRINT_H_IN


def _pick(rng: random.Random, sizes: list[tuple[int, int]], dpis: list[int]) -> tuple[tuple[int, int], int]:
    combos = [(px, d) for px in sizes for d in dpis if _fits(px, d)]
    return rng.choice(combos)


def _raster(rng: random.Random, cell: str, variant: str, order: int) -> FigurePlan:
    """`cell` says which rules the figure must violate: ok | re20 | re21 | ambas."""
    sizes, dpis = {
        "ok": (PX_OK, DPI_OK),
        "re20": (PX_SMALL, DPI_OK),
        "re21": (PX_OK, DPI_LOW),
        "ambas": (PX_TINY, DPI_LOW),
    }[cell]
    if variant == "recortada" and cell == "re20":
        sizes = PX_NARROW  # the crop itself must be what makes the figure too narrow
    (w, h), dpi = _pick(rng, sizes, dpis)
    fig = FigurePlan(order=order, printed_number=order, variant=variant, kind="raster", visible_w_px=w, visible_h_px=h, dpi=float(dpi))
    fig.print_w_in, fig.print_h_in = round(w / dpi, 4), round(h / dpi, 4)
    fig.source_w_px, fig.source_h_px = w, h
    if variant == "recortada":
        # The author embedded a wider image and cropped its right side: only the visible part counts.
        crops = [150, 300, 450, 600]
        if cell == "re20":  # the embedded image is wide enough; only the visible part is not
            crops = [c for c in crops if w + c >= MIN_SOURCE_W_FOR_CROP]
        fig.crop_right_px = rng.choice(crops)
        fig.source_w_px = w + fig.crop_right_px
    elif variant == "rotada":
        # The image file is stored sideways and rotated 90 degrees in the document.
        fig.rotated = True
        fig.source_w_px, fig.source_h_px = h, w
    return fig


def _cells_for(rng: random.Random, profile: str, n: int) -> list[str]:
    if profile == "conforme":
        return ["ok"] * n
    if profile == "un_defecto":
        cells = ["ok"] * n
        cells[rng.randrange(n)] = rng.choice(["re20", "re21"])
        return cells
    cells = [rng.choice(["re20", "re21", "ambas", "ambas", "ok"]) for _ in range(n)]
    if sum(c != "ok" for c in cells) < 2:  # "varios" means at least two defective figures or one with both rules
        cells[rng.randrange(n)] = "ambas"
    return cells


def plan_document(rng: random.Random, doc_id: str, generator: str, n_articles: int, th: dict) -> DocPlan:
    profile = _weighted(rng, PROFILES)
    if profile == "conforme" and rng.random() < 0.10:
        n_figs = 0  # ALT-03: a manuscript without figures must produce no finding
    else:
        n_figs = rng.choice([1, 2, 2, 3, 3, 4]) if profile != "varios" else rng.choice([2, 3, 3, 4, 5])
    figures: list[FigurePlan] = []
    for order, cell in enumerate(_cells_for(rng, profile, n_figs) if n_figs else [], start=1):
        variant = _weighted(rng, VARIANTS[generator])
        if variant == "vectorial":
            fig = FigurePlan(order=order, printed_number=order, variant=variant, kind="vector")
        else:
            fig = _raster(rng, cell, variant, order)
        if profile != "conforme":
            if rng.random() < 0.10:
                fig.caption_defect = rng.choice(CAPTION_DEFECTS)
                if fig.caption_defect == "sin_pie":
                    fig.printed_number = None
            fig.referenced = rng.random() >= 0.10
        fig.truth_source = truth(fig, th)
        figures.append(fig)

    doc = DocPlan(
        doc_id=doc_id,
        generator=generator,
        profile=profile,
        article_type=rng.choice(["corto", "original", "original", "revision"]),
        article_index=rng.randrange(n_articles),
        body_blocks=rng.choice([0, 3, 8, 14, 22, 32, 44, 58]),
        figures=figures,
    )
    numbered = [f for f in figures if f.printed_number is not None]
    if profile != "conforme" and len(numbered) >= 2 and rng.random() < 0.06:
        doc.numbering_skip = True  # the last numbered figure jumps one number (RE-24)
        numbered[-1].printed_number += 1
    return doc


def build_plan(n_latex: int, n_word: int, n_articles: int, seed: int = SEED) -> list[DocPlan]:
    rng = random.Random(seed)
    th = load_thresholds()
    docs = [plan_document(rng, f"L{i:03d}", "latex", n_articles, th) for i in range(1, n_latex + 1)]
    docs += [plan_document(rng, f"W{i:03d}", "word", n_articles, th) for i in range(1, n_word + 1)]
    return docs
