"""US-04 · Text extraction with PyMuPDF: `extract_text(pdf) -> ExtractionResult`.

Coordinates are PDF points (1/72 in), origin top-left (PyMuPDF convention).
Reading order is the one PyMuPDF yields; columns are not re-ordered here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import fitz
from pydantic import BaseModel, Field

FLAG_ITALIC = 1 << 1
FLAG_BOLD = 1 << 4
EXTRACTOR_VERSION = f"pymupdf-{fitz.VersionBind}"

UnreadableReason = Literal["no_text_layer", "corrupt", "encrypted"]


class Block(BaseModel):
    bbox: list[float]
    text: str
    font: str
    size: float
    bold: bool
    italic: bool


class Page(BaseModel):
    page: int
    width: float
    height: float
    blocks: list[Block] = Field(default_factory=list)
    page_text: str = ""


class DocumentData(BaseModel):
    pages: list[Page] = Field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self.pages)


class ExtractionResult(BaseModel):
    status: Literal["extracted", "unreadable"]
    reason: UnreadableReason | None = None
    document: DocumentData | None = None
    detail: str | None = None


def _is_bold(font: str, flags: int) -> bool:
    return bool(flags & FLAG_BOLD) or "bold" in font.lower() or "black" in font.lower()


def _is_italic(font: str, flags: int) -> bool:
    return bool(flags & FLAG_ITALIC) or "italic" in font.lower() or "oblique" in font.lower()


def _block_from_dict(raw: dict) -> Block | None:
    """Flatten a PyMuPDF text block: text of all lines, style of the dominant span (most characters)."""
    spans = [s for line in raw.get("lines", []) for s in line.get("spans", []) if s.get("text")]
    if not spans:
        return None
    text = "\n".join("".join(s["text"] for s in line.get("spans", [])) for line in raw["lines"]).strip()
    if not text:
        return None
    dominant = max(spans, key=lambda s: len(s["text"]))
    font = dominant.get("font", "")
    flags = int(dominant.get("flags", 0))
    return Block(
        bbox=[round(v, 2) for v in raw["bbox"]],
        text=text,
        font=font,
        size=round(float(dominant.get("size", 0.0)), 2),
        bold=_is_bold(font, flags),
        italic=_is_italic(font, flags),
    )


def _extract_page(page: fitz.Page, number: int) -> Page:
    raw = page.get_text("dict")
    blocks = [b for b in (_block_from_dict(rb) for rb in raw.get("blocks", []) if rb.get("type") == 0) if b]
    return Page(
        page=number,
        width=round(page.rect.width, 2),
        height=round(page.rect.height, 2),
        blocks=blocks,
        page_text=page.get_text("text"),
    )


def extract_text(pdf: Path | str | bytes, *, min_chars_per_page: int = 50) -> ExtractionResult:
    """Extract pages and text blocks. Never raises for bad input: returns `unreadable` with a reason."""
    fitz.TOOLS.mupdf_warnings(reset=True)
    try:
        doc = fitz.open(stream=pdf, filetype="pdf") if isinstance(pdf, bytes) else fitz.open(str(pdf))
    except Exception as exc:  # fitz raises several exception types for broken files
        return ExtractionResult(status="unreadable", reason="corrupt", detail=str(exc))

    with doc:
        if doc.needs_pass or doc.is_encrypted:
            return ExtractionResult(status="unreadable", reason="encrypted", detail="El PDF está cifrado")
        if doc.page_count == 0:
            return ExtractionResult(status="unreadable", reason="corrupt", detail="El PDF no tiene páginas")

        pages: list[Page] = []
        failed_pages = 0
        for index in range(doc.page_count):
            try:
                pages.append(_extract_page(doc[index], index + 1))
            except Exception:  # a broken page is kept as empty; the document decides below
                failed_pages += 1
                pages.append(Page(page=index + 1, width=0.0, height=0.0))

        warnings = fitz.TOOLS.mupdf_warnings(reset=True)
        format_errors = "format error" in warnings
        empty_pages = sum(1 for p in pages if not p.page_text.strip())
        if doc.is_repaired and (failed_pages or format_errors or empty_pages * 2 > len(pages)):
            return ExtractionResult(status="unreadable", reason="corrupt", detail="El PDF está dañado o truncado")

        total_chars = sum(len(p.page_text.strip()) for p in pages)
        if total_chars / len(pages) < min_chars_per_page:
            return ExtractionResult(
                status="unreadable",
                reason="no_text_layer",
                detail=f"Promedio de {total_chars / len(pages):.0f} caracteres por página (mínimo {min_chars_per_page})",
            )

    return ExtractionResult(status="extracted", document=DocumentData(pages=pages))
