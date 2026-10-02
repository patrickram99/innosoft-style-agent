"""Generate the synthetic PDF corpus used by the test suite.

Every PDF is built with PyMuPDF so figure sizes and DPI are known exactly.
No real personal data: authors, emails and ORCID are fictitious or absent.

Run:  python tests/fixtures/generate_pdfs.py  [out_dir]
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz  # PyMuPDF

PDF_DIR = Path(__file__).resolve().parent / "pdfs"
PAGE_W, PAGE_H = 612, 792  # carta, puntos
MARGIN_L, MARGIN_R, MARGIN_T = 56.7, 34.0, 108.0  # 2 cm, 1,2 cm, 3,81 cm
TEXT_W = PAGE_W - MARGIN_L - MARGIN_R

LOREM = (
    "Se presenta un enfoque para la deteccion automatica de incumplimientos de estilo en "
    "manuscritos cientificos. El metodo combina extraccion documental con un motor de reglas "
    "declarativas. Los resultados muestran que la mayoria de las observaciones editoriales "
    "pueden identificarse de forma deterministica antes de la revision por pares. "
)


def _png(width_px: int, height_px: int, color: tuple[int, int, int]) -> bytes:
    """Solid raster image of exactly width_px x height_px with a lighter inner box."""
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width_px, height_px), False)
    pix.set_rect(fitz.IRect(0, 0, width_px, height_px), color)
    inner = fitz.IRect(width_px // 10, height_px // 10, width_px * 9 // 10, height_px * 9 // 10)
    pix.set_rect(inner, (255, 255, 255))
    return pix.tobytes("png")


def _save(doc: fitz.Document, path: Path) -> None:
    doc.save(path, garbage=3, deflate=True, deflate_images=True)


def _header(page: fitz.Page, title: str, *, with_logo: bool = False) -> float:
    page.insert_text((MARGIN_L, MARGIN_T), title, fontsize=18, fontname="hebo")
    page.insert_text((MARGIN_L, MARGIN_T + 22), "Autor Uno, Autora Dos", fontsize=11, fontname="hebo")
    page.insert_text(
        (MARGIN_L, MARGIN_T + 36),
        "Universidad Ficticia, Facultad de Ingenieria, Arequipa, Peru",
        fontsize=10,
        fontname="helv",
    )
    if with_logo:
        # Logo decorativo de 50 x 50 px a 0,3 in: debe ignorarse (< 1 % del area de pagina).
        rect = fitz.Rect(PAGE_W - MARGIN_R - 22, 30, PAGE_W - MARGIN_R, 52)
        page.insert_image(rect, stream=_png(50, 50, (120, 120, 120)))
    return MARGIN_T + 60


def _paragraphs(page: fitz.Page, y: float, n: int = 4, size: float = 11) -> float:
    rect = fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, PAGE_H - MARGIN_T)
    text = "\n\n".join(LOREM * 2 for _ in range(n))
    page.insert_textbox(rect, text, fontsize=size, fontname="tiro", lineheight=1.5)
    return y + n * 140


def _figure(
    page: fitz.Page,
    y: float,
    number: int,
    *,
    width_px: int,
    height_px: int,
    print_w_in: float,
    print_h_in: float,
    caption: bool = True,
    color: tuple[int, int, int] = (40, 90, 160),
) -> float:
    w_pt, h_pt = print_w_in * 72, print_h_in * 72
    x0 = MARGIN_L + (TEXT_W - w_pt) / 2
    rect = fitz.Rect(x0, y, x0 + w_pt, y + h_pt)
    page.insert_image(rect, stream=_png(width_px, height_px, color))
    if caption:
        cap = f"Figura {number}. Diagrama de ejemplo numero {number}"
        page.insert_textbox(
            fitz.Rect(MARGIN_L, rect.y1 + 6, PAGE_W - MARGIN_R, rect.y1 + 30),
            cap,
            fontsize=10,
            fontname="tiro",
            align=fitz.TEXT_ALIGN_CENTER,
        )
    return rect.y1 + 40


def _vector_figure(page: fitz.Page, y: float, number: int) -> float:
    """A bar chart drawn with vector primitives (no raster image)."""
    x0, w, h = MARGIN_L + 60, 360, 160
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(x0, y, x0 + w, y + h))
    for i, bar_h in enumerate([40, 90, 130, 70, 110]):
        bx = x0 + 20 + i * 68
        shape.draw_rect(fitz.Rect(bx, y + h - bar_h, bx + 40, y + h))
    shape.draw_line(fitz.Point(x0, y + h), fitz.Point(x0 + w, y + h))
    shape.finish(color=(0, 0, 0), fill=(0.6, 0.6, 0.9), width=1)
    shape.commit()
    page.insert_textbox(
        fitz.Rect(MARGIN_L, y + h + 6, PAGE_W - MARGIN_R, y + h + 30),
        f"Figura {number}. Grafico vectorial de barras",
        fontsize=10,
        fontname="tiro",
        align=fitz.TEXT_ALIGN_CENTER,
    )
    return y + h + 40


def _text_pages(doc: fitz.Document, n: int) -> None:
    for _ in range(n):
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_text((MARGIN_L, MARGIN_T - 40), "2. Materiales y metodos", fontsize=12, fontname="hebo")
        _paragraphs(page, MARGIN_T - 20, n=4)


def build_figuras_pequenas(path: Path) -> None:
    """3 figuras raster de 300 x 600 px (alto x ancho) a 300 dpi: fallan RE-20, pasan RE-21."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = _header(page, "Deteccion de estilo con figuras pequenas")
    y = _paragraphs(page, y, n=1)
    y = _figure(page, y, 1, width_px=600, height_px=300, print_w_in=2.0, print_h_in=1.0, color=(200, 60, 60))
    y = _paragraphs(page, y, n=1)
    _figure(page, y, 2, width_px=600, height_px=300, print_w_in=2.0, print_h_in=1.0, color=(60, 160, 60))
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = _paragraphs(page, MARGIN_T, n=1)
    _figure(page, y, 3, width_px=600, height_px=300, print_w_in=2.0, print_h_in=1.0, color=(60, 60, 200))
    _text_pages(doc, 1)
    _save(doc, path)
    doc.close()


def build_figuras_baja_dpi(path: Path) -> None:
    """Figura 1: 600 x 1400 px a 200 dpi (pasa RE-20, falla RE-21).
    Figura 2: 400 x 1000 px a 200 dpi, sin pie (falla RE-20 y RE-21)."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = _header(page, "Resolucion insuficiente en figuras")
    y = _paragraphs(page, y, n=1)
    _figure(page, y, 1, width_px=1400, height_px=600, print_w_in=7.0, print_h_in=3.0, color=(160, 90, 40))
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = _paragraphs(page, MARGIN_T, n=1)
    _figure(
        page, y, 2, width_px=1000, height_px=400, print_w_in=5.0, print_h_in=2.0,
        caption=False, color=(90, 40, 160),
    )
    _save(doc, path)
    doc.close()


def build_sin_figuras(path: Path, pages: int = 15) -> None:
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = _header(page, "Articulo sin figuras")
    page.insert_text((MARGIN_L, y), "Resumen", fontsize=11, fontname="hebo")
    _paragraphs(page, y + 10, n=3)
    _text_pages(doc, pages - 1)
    _save(doc, path)
    doc.close()


def build_correcto(path: Path) -> None:
    """2 figuras de 800 x 2000 px (alto x ancho) a 300 dpi: sin hallazgos RE-20/RE-21."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = _header(page, "Manuscrito conforme a las directrices", with_logo=True)
    y = _paragraphs(page, y, n=1)
    y = _figure(page, y, 1, width_px=2000, height_px=800, print_w_in=2000 / 300, print_h_in=800 / 300, color=(30, 120, 120))
    _paragraphs(page, y, n=1)
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = _paragraphs(page, MARGIN_T, n=1)
    _figure(page, y, 2, width_px=2000, height_px=800, print_w_in=2000 / 300, print_h_in=800 / 300, color=(120, 30, 120))
    _text_pages(doc, 8)
    _save(doc, path)
    doc.close()


def build_vectorial(path: Path) -> None:
    """Una figura vectorial (sin imagen raster) con pie: kind=vector, sin DPI."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = _header(page, "Figura vectorial generada desde LaTeX")
    y = _paragraphs(page, y, n=1)
    _vector_figure(page, y, 1)
    _save(doc, path)
    doc.close()


def build_escaneado(path: Path, source: Path, pages: int = 3) -> None:
    """Paginas rasterizadas de un PDF correcto: solo imagen, sin capa de texto."""
    src = fitz.open(source)
    doc = fitz.open()
    for i in range(min(pages, len(src))):
        pix = src[i].get_pixmap(dpi=150)
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_image(page.rect, stream=pix.tobytes("png"))
    _save(doc, path)
    doc.close()
    src.close()


def build_corrupto(path: Path, source: Path) -> None:
    data = source.read_bytes()
    path.write_bytes(data[: len(data) // 3])


def build_treinta_paginas(path: Path) -> None:
    build_sin_figuras(path, pages=30)


def generate_all(out_dir: Path = PDF_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    build_figuras_pequenas(out_dir / "figuras_pequenas.pdf")
    build_figuras_baja_dpi(out_dir / "figuras_baja_dpi.pdf")
    build_sin_figuras(out_dir / "sin_figuras.pdf")
    build_correcto(out_dir / "correcto.pdf")
    build_vectorial(out_dir / "vectorial.pdf")
    build_escaneado(out_dir / "escaneado.pdf", out_dir / "sin_figuras.pdf")
    build_corrupto(out_dir / "corrupto.pdf", out_dir / "correcto.pdf")
    build_treinta_paginas(out_dir / "treinta_paginas.pdf")
    return sorted(out_dir.glob("*.pdf"))


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_DIR
    for p in generate_all(target):
        print(p.name, p.stat().st_size, "bytes")
