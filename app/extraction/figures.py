"""US-06 · Figure extraction: raster images (pixels, effective DPI), vector drawings and captions.

Output is the `figures` list of the Document (ordered by page, then y, then x). Thumbnails are
rendered to `storage/{manuscript_id}/fig-{n}.png` when `thumbnails_dir` is given.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import fitz
from pydantic import BaseModel, Field

from app.extraction.text import DocumentData, Page

CAPTION_RE = re.compile(r"^\s*(?:figura|fig\.?)\s*(\d+)\s*[.:\-–—]?", re.IGNORECASE)
MIN_AREA_RATIO = 0.01  # US-06 §6.2: ignore decorative images below 1 % of the page area
CAPTION_TOLERANCE_PT = 40.0  # US-06 §3: caption block within 40 pt of the figure
CAPTION_OVERLAP_PT = 20.0  # caption block may start slightly inside the image bbox (padding)
MIN_VECTOR_SIDE_PT = 40.0  # a vector region must be a real area, not a rule or underline
VECTOR_GAP_PT = 10.0  # drawings closer than this are grouped into one region
MOSAIC_GAP_PT = 2.0  # contiguous raster tiles sharing a caption are merged (US-06 §7)


class Caption(BaseModel):
    text: str
    number: int | None
    position: Literal["below", "above"]
    bbox: list[float]
    font: str
    size: float


class Figure(BaseModel):
    order: int = 0
    page: int
    kind: Literal["raster", "vector"]
    bbox: list[float]
    width_px: int | None = None
    height_px: int | None = None
    print_width_in: float
    print_height_in: float
    dpi_x: float | None = None
    dpi_y: float | None = None
    caption: Caption | None = None
    thumbnail: str | None = None
    xref: int | None = None
    tiles: int = Field(default=1, description="Raster tiles merged into this figure (mosaics)")

    @property
    def label(self) -> str:
        """`Figura n` from the caption, or the position when the caption has no number."""
        if self.caption and self.caption.number is not None:
            return f"Figura {self.caption.number}"
        return f"figura en la posición {self.order}"


def effective_dpi(pixels: int, printed_inches: float) -> float | None:
    """DPI = pixels / printed size in inches (US-06 §3). None if the printed size is zero."""
    if printed_inches <= 0:
        return None
    return round(pixels / printed_inches, 1)


def parse_caption_number(text: str) -> int | None:
    m = CAPTION_RE.match(text)
    return int(m.group(1)) if m else None


def _is_caption_block(text: str) -> bool:
    return CAPTION_RE.match(text) is not None


def _h_overlap(a: list[float], b: list[float]) -> bool:
    return a[0] < b[2] and b[0] < a[2]


def find_caption(bbox: list[float], page: Page, tolerance: float = CAPTION_TOLERANCE_PT) -> Caption | None:
    """First `Figura/Fig.` block ≤ tolerance below the bbox; if none, the nearest one above (US-06 §6.4)."""
    candidates = [b for b in page.blocks if _is_caption_block(b.text) and _h_overlap(b.bbox, bbox)]
    # Word/LaTeX exports often start the caption block a few points inside the image bbox
    # (the image carries white padding), so a small overlap is tolerated.
    below = [
        b for b in candidates
        if -CAPTION_OVERLAP_PT <= b.bbox[1] - bbox[3] <= tolerance and b.bbox[3] > bbox[3]
    ]
    if below:
        block = min(below, key=lambda b: b.bbox[1])
        position = "below"
    else:
        above = [
            b for b in candidates
            if -CAPTION_OVERLAP_PT <= bbox[1] - b.bbox[3] <= tolerance and b.bbox[1] < bbox[1]
        ]
        if not above:
            return None
        block = max(above, key=lambda b: b.bbox[3])
        position = "above"
    return Caption(
        text=block.text.split("\n")[0].strip(),
        number=parse_caption_number(block.text),
        position=position,
        bbox=block.bbox,
        font=block.font,
        size=block.size,
    )


def _raster_figures(page: fitz.Page, number: int, min_area: float) -> list[Figure]:
    figures: list[Figure] = []
    for info in page.get_image_info(xrefs=True):
        bbox = [round(v, 2) for v in info["bbox"]]
        w_pt, h_pt = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w_pt * h_pt < min_area:
            continue
        w_in, h_in = w_pt / 72.0, h_pt / 72.0
        figures.append(
            Figure(
                page=number,
                kind="raster",
                bbox=bbox,
                width_px=int(info["width"]),
                height_px=int(info["height"]),
                print_width_in=round(w_in, 3),
                print_height_in=round(h_in, 3),
                dpi_x=effective_dpi(int(info["width"]), w_in),
                dpi_y=effective_dpi(int(info["height"]), h_in),
                xref=info.get("xref"),
            )
        )
    return figures


def _group_rects(rects: list[fitz.Rect], gap: float) -> list[fitz.Rect]:
    """Union of rectangles that touch or lie within `gap` points of each other (transitively)."""
    groups: list[fitz.Rect] = []
    for rect in rects:
        merged = fitz.Rect(rect)
        remaining: list[fitz.Rect] = []
        for g in groups:
            if fitz.Rect(g.x0 - gap, g.y0 - gap, g.x1 + gap, g.y1 + gap).intersects(merged):
                merged |= g
            else:
                remaining.append(g)
        remaining.append(merged)
        groups = remaining
    return groups


def _vector_figures(page: fitz.Page, number: int, min_area: float, raster: list[Figure]) -> list[Figure]:
    rects = [fitz.Rect(d["rect"]) for d in page.get_drawings() if d.get("rect") is not None]
    rects = [r for r in rects if not r.is_empty]
    figures: list[Figure] = []
    for region in _group_rects(rects, VECTOR_GAP_PT):
        if region.width < MIN_VECTOR_SIDE_PT or region.height < MIN_VECTOR_SIDE_PT:
            continue
        if region.width * region.height < min_area:
            continue
        # A drawing that merely frames a raster image is not a separate figure.
        if any(region.intersects(fitz.Rect(f.bbox)) for f in raster):
            continue
        figures.append(
            Figure(
                page=number,
                kind="vector",
                bbox=[round(v, 2) for v in (region.x0, region.y0, region.x1, region.y1)],
                print_width_in=round(region.width / 72.0, 3),
                print_height_in=round(region.height / 72.0, 3),
            )
        )
    return figures


def _contiguous_groups(figures: list[Figure]) -> list[list[Figure]]:
    """Groups of raster tiles whose bboxes touch (gap ≤ MOSAIC_GAP_PT); non-raster figures stay alone."""
    groups: list[list[Figure]] = []
    for fig in figures:
        if fig.kind != "raster":
            groups.append([fig])
            continue
        b = fitz.Rect(fig.bbox)
        joined: list[list[Figure]] = []
        for group in groups:
            if group[0].kind != "raster":
                continue
            for tile in group:
                a = fitz.Rect(tile.bbox)
                if fitz.Rect(a.x0 - MOSAIC_GAP_PT, a.y0 - MOSAIC_GAP_PT, a.x1 + MOSAIC_GAP_PT, a.y1 + MOSAIC_GAP_PT).intersects(b):
                    joined.append(group)
                    break
        if not joined:
            groups.append([fig])
            continue
        merged = [fig]
        for group in joined:
            groups.remove(group)
            merged.extend(group)
        groups.append(merged)
    return groups


def _merge_tiles(tiles: list[Figure], caption: Caption) -> Figure:
    union = fitz.Rect(tiles[0].bbox)
    for t in tiles[1:]:
        union |= fitz.Rect(t.bbox)
    rows = len({round(t.bbox[1]) for t in tiles})
    cols = len({round(t.bbox[0]) for t in tiles})
    # Approximate pixel size of the composite: sum along the axis the tiles are laid out on.
    if cols >= rows:
        width_px = sum(t.width_px or 0 for t in tiles) // max(rows, 1)
        height_px = max(t.height_px or 0 for t in tiles) * rows
    else:
        width_px = max(t.width_px or 0 for t in tiles) * cols
        height_px = sum(t.height_px or 0 for t in tiles) // max(cols, 1)
    return Figure(
        page=tiles[0].page,
        kind="raster",
        bbox=[round(v, 2) for v in (union.x0, union.y0, union.x1, union.y1)],
        width_px=width_px,
        height_px=height_px,
        print_width_in=round(union.width / 72.0, 3),
        print_height_in=round(union.height / 72.0, 3),
        dpi_x=effective_dpi(width_px, union.width / 72.0),
        dpi_y=effective_dpi(height_px, union.height / 72.0),
        caption=caption,
        xref=tiles[0].xref,
        tiles=len(tiles),
    )


def _merge_mosaics(figures: list[Figure], text_page: Page | None) -> list[Figure]:
    """Contiguous raster tiles that share one caption become a single figure (US-06 §7)."""
    result: list[Figure] = []
    for group in _contiguous_groups(figures):
        if len(group) == 1 or text_page is None:
            result.extend(group)
            continue
        union = fitz.Rect(group[0].bbox)
        for t in group[1:]:
            union |= fitz.Rect(t.bbox)
        caption = find_caption([union.x0, union.y0, union.x1, union.y1], text_page)
        shared = caption is not None and all(t.caption is None or t.caption.bbox == caption.bbox for t in group)
        if shared:
            result.append(_merge_tiles(group, caption))
        else:
            result.extend(group)
    return result


def _render_thumbnail(page: fitz.Page, fig: Figure, out_dir: Path, dpi: int = 100) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"fig-{fig.order}.png"
    clip = fitz.Rect(fig.bbox) & page.rect
    pix = page.get_pixmap(clip=clip, dpi=dpi)
    pix.save(target)
    return str(target.as_posix())


def extract_figures(
    pdf: Path | str,
    document: DocumentData,
    *,
    thumbnails_dir: Path | None = None,
    min_area_ratio: float = MIN_AREA_RATIO,
) -> list[Figure]:
    """Figures of every page, ordered by appearance. A manuscript without figures yields [] (ALT-03)."""
    pages_by_number = {p.page: p for p in document.pages}
    figures: list[Figure] = []
    with fitz.open(str(pdf)) as doc:
        for index in range(doc.page_count):
            page = doc[index]
            number = index + 1
            min_area = page.rect.width * page.rect.height * min_area_ratio
            raster = _raster_figures(page, number, min_area)
            vector = _vector_figures(page, number, min_area, raster)
            page_figures = raster + vector
            text_page = pages_by_number.get(number)
            for fig in page_figures:
                if text_page is not None:
                    fig.caption = find_caption(fig.bbox, text_page)
            page_figures.sort(key=lambda f: (f.bbox[1], f.bbox[0]))
            figures.extend(_merge_mosaics(page_figures, text_page))

        figures.sort(key=lambda f: (f.page, f.bbox[1], f.bbox[0]))
        for order, fig in enumerate(figures, start=1):
            fig.order = order
            if thumbnails_dir is not None:
                fig.thumbnail = _render_thumbnail(doc[fig.page - 1], fig, thumbnails_dir)
    return figures
