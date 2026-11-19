"""Independent check of every generated PDF and ground truth at PDF level.

The images stored in each PDF are read with pypdf, straight from the `/Width` and `/Height` of the image
objects. pypdf is a different library from the one the agent uses (PyMuPDF), so the ground truth does not
inherit the agent's reading of the file.

Why this step exists: LaTeX embeds the source image untouched, but Word resamples images to about 200 ppi
when it exports to PDF. The agent receives the PDF, so the rules are judged on what the PDF contains
(`truth`); what the author embedded is kept as `truth_source` to measure the effect of the conversion.
"""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from tools.eval_dataset.design import DocPlan, FigurePlan, truth

WORD_EXPORT_PPI = 200  # usual result of Word's PDF export; only breaks ties between figures on the same page
ASPECT_TOLERANCE = 0.01  # resampling rounds to whole pixels, so the aspect ratio moves slightly


def _images(resources, seen: set[int]) -> list[tuple[int, int]]:
    """Images of a page, including those nested in form XObjects (pdfTeX wraps clipped images in a form)."""
    found: list[tuple[int, int]] = []
    xobjects = (resources or {}).get("/XObject") or {}
    for name in xobjects:
        obj = xobjects[name].get_object()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        if obj.get("/Subtype") == "/Image":
            found.append((int(obj["/Width"]), int(obj["/Height"])))
        elif obj.get("/Subtype") == "/Form":
            found += _images(obj.get("/Resources"), seen)
    return found


def embedded_images(pdf: Path) -> dict[int, list[tuple[int, int]]]:
    reader = PdfReader(str(pdf))
    return {number: _images(page.get("/Resources"), set()) for number, page in enumerate(reader.pages, start=1)}


def _resampled_match(fig: FigurePlan, pool: list[tuple[int, int]]) -> tuple[int, int] | None:
    """A smaller image with the aspect ratio of the source. If several qualify, the one nearest to 200 ppi."""
    ratio = fig.source_w_px / fig.source_h_px
    same_shape = [img for img in pool if img[0] < fig.source_w_px and abs(img[0] / img[1] - ratio) <= ASPECT_TOLERANCE * ratio]
    expected_w = fig.print_w_in * WORD_EXPORT_PPI
    return min(same_shape, key=lambda img: abs(img[0] - expected_w), default=None)


def verify_document(doc: DocPlan, pdf: Path, thresholds: dict) -> None:
    """Fill `embedded_*`, `verified`, and the PDF-level `truth` of every figure of the document."""
    images = embedded_images(pdf)
    raster = [f for f in doc.figures if f.kind == "raster"]
    for fig in doc.figures:
        if fig.kind != "raster":
            fig.verified, fig.truth = True, truth(fig, thresholds)
    # Two passes, so an untouched image is never taken by a neighbour of almost the same size: first the images
    # stored exactly as the source, then the resampled ones.
    matches: dict[int, tuple[int, int]] = {}
    for fig in raster:
        pool = images.get(fig.page, [])
        source = (fig.source_w_px, fig.source_h_px)
        if source in pool:
            pool.remove(source)
            matches[fig.order] = source
    for fig in raster:
        if fig.order not in matches:
            pool = images.get(fig.page, [])
            match = _resampled_match(fig, pool)
            if match is not None:
                pool.remove(match)
                matches[fig.order] = match
    for fig in raster:
        match = matches.get(fig.order)
        if match is None:
            fig.verified, fig.truth = False, {}
            continue
        fig.embedded_w_px, fig.embedded_h_px = match
        fig.verified = True
        # LaTeX stores the source image untouched, so the plan (visible pixels after crop or rotation) holds.
        # A resampled image only happens in Word documents, which carry no cropped or rotated figures.
        resampled = match != (fig.source_w_px, fig.source_h_px)
        fig.truth = truth(fig, thresholds, resampled_px=match if resampled else None)
