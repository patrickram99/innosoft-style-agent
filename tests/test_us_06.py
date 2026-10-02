"""US-06 · Extraer figuras: posición, tamaño y pie."""
from __future__ import annotations

import json
from pathlib import Path

import fitz
import pytest

from app.extraction.figures import effective_dpi, extract_figures, parse_caption_number
from app.extraction.text import extract_text
from app.models import Document


def _figures(pdf: Path, thumbnails_dir: Path | None = None):
    result = extract_text(pdf)
    assert result.status == "extracted"
    return extract_figures(pdf, result.document, thumbnails_dir=thumbnails_dir)


def test_t01_effective_dpi_known_values():
    assert effective_dpi(1200, 6.0) == 200.0
    assert effective_dpi(600, 2.0) == 300.0
    assert effective_dpi(2000, 2000 / 300) == 300.0
    assert effective_dpi(100, 0) is None


def test_ac02_1200px_at_six_inches_is_200_dpi(tmp_path: Path):
    doc = fitz.open()
    page = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 1200, 640), False)
    pix.set_rect(pix.irect, (10, 10, 10))
    page.insert_image(fitz.Rect(90, 200, 90 + 6 * 72, 200 + 3.2 * 72), stream=pix.tobytes("png"))
    page.insert_textbox(fitz.Rect(90, 640, 522, 664), "Figura 1. Arquitectura", fontsize=10)
    page.insert_text((72, 100), "Texto introductorio suficientemente largo para la pagina de prueba. " * 2)
    path = tmp_path / "dpi.pdf"
    doc.save(path)
    (fig,) = _figures(path)
    assert fig.width_px == 1200 and fig.height_px == 640
    assert abs(fig.dpi_x - 200) <= 1
    assert abs(fig.dpi_y - 200) <= 1


def test_ac01_three_raster_figures_with_caption(pdf_dir: Path):
    figures = _figures(pdf_dir / "figuras_pequenas.pdf")
    assert len(figures) == 3
    assert [f.order for f in figures] == [1, 2, 3]
    assert [f.page for f in figures] == [1, 1, 2]
    for n, fig in enumerate(figures, start=1):
        assert fig.kind == "raster"
        assert len(fig.bbox) == 4
        assert fig.width_px and fig.height_px and fig.dpi_x and fig.dpi_y
        assert fig.caption is not None
        assert fig.caption.number == n
        assert fig.caption.position == "below"
        assert fig.caption.text.startswith(f"Figura {n}.")
        assert fig.label == f"Figura {n}"


def test_t02_small_figure_pixels_and_dpi(pdf_dir: Path):
    fig = _figures(pdf_dir / "figuras_pequenas.pdf")[0]
    assert (fig.height_px, fig.width_px) == (300, 600)
    assert abs(fig.dpi_x - 300) <= 1 and abs(fig.dpi_y - 300) <= 1
    assert abs(fig.print_width_in - 2.0) < 0.01


def test_t03_figure_without_caption(pdf_dir: Path):
    figures = _figures(pdf_dir / "figuras_baja_dpi.pdf")
    assert len(figures) == 2
    first, second = figures
    assert first.caption is not None and first.caption.number == 1
    assert abs(first.dpi_x - 200) <= 1
    assert second.caption is None
    assert second.label == "figura en la posición 2"
    assert (second.height_px, second.width_px) == (400, 1000)


def test_t04_vector_figure_has_kind_vector_and_no_dpi(pdf_dir: Path):
    figures = _figures(pdf_dir / "vectorial.pdf")
    assert len(figures) == 1
    fig = figures[0]
    assert fig.kind == "vector"
    assert fig.dpi_x is None and fig.dpi_y is None
    assert fig.width_px is None and fig.height_px is None
    assert fig.caption is not None and fig.caption.number == 1


def test_t05_no_figures_returns_empty_list(pdf_dir: Path):
    assert _figures(pdf_dir / "sin_figuras.pdf") == []


def test_decorative_logo_is_ignored(pdf_dir: Path):
    figures = _figures(pdf_dir / "correcto.pdf")
    assert len(figures) == 2
    assert all(f.width_px == 2000 and f.height_px == 800 for f in figures)
    assert all(abs(f.dpi_x - 300) <= 1 for f in figures)


def test_caption_above_is_detected(tmp_path: Path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Texto de relleno para que la pagina tenga capa de texto suficiente. " * 2)
    page.insert_textbox(fitz.Rect(90, 176, 522, 200), "Fig. 7: Pie encima de la imagen", fontsize=10)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 800, 400), False)
    pix.set_rect(pix.irect, (0, 0, 0))
    page.insert_image(fitz.Rect(90, 205, 490, 405), stream=pix.tobytes("png"))
    path = tmp_path / "arriba.pdf"
    doc.save(path)
    (fig,) = _figures(path)
    assert fig.caption is not None
    assert fig.caption.position == "above"
    assert fig.caption.number == 7


def test_caption_number_regex_is_tolerant():
    assert parse_caption_number("Figura 3. Titulo") == 3
    assert parse_caption_number("Fig. 3: Titulo") == 3
    assert parse_caption_number("FIGURA 3 - Titulo") == 3
    assert parse_caption_number("Figura3.") == 3
    assert parse_caption_number("Tabla 3. Titulo") is None


def test_mosaic_tiles_sharing_caption_are_merged(tmp_path: Path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Texto de relleno para que la pagina tenga capa de texto suficiente. " * 2)
    for i, color in enumerate([(200, 0, 0), (0, 0, 200)]):
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 500, 400), False)
        pix.set_rect(pix.irect, color)
        x0 = 90 + i * 200
        page.insert_image(fitz.Rect(x0, 200, x0 + 200, 360), stream=pix.tobytes("png"))
    page.insert_textbox(fitz.Rect(90, 366, 522, 390), "Figura 1. Mosaico de dos paneles", fontsize=10)
    path = tmp_path / "mosaico.pdf"
    doc.save(path)
    (fig,) = _figures(path)
    assert fig.tiles == 2
    assert fig.width_px == 1000 and fig.height_px == 400
    assert fig.bbox[0] == 90 and fig.bbox[2] == 490


def test_thumbnails_are_written(pdf_dir: Path, tmp_path: Path):
    figures = _figures(pdf_dir / "figuras_pequenas.pdf", thumbnails_dir=tmp_path / "thumbs")
    for fig in figures:
        assert fig.thumbnail is not None
        assert Path(fig.thumbnail).exists()
        assert Path(fig.thumbnail).name == f"fig-{fig.order}.png"


def test_figures_persisted_via_api(client, auth_headers, db_session, storage_dir: Path, pdf_dir: Path):
    pdf = (pdf_dir / "figuras_pequenas.pdf").read_bytes()
    r = client.post(
        "/manuscripts",
        files={"file": ("figuras_pequenas.pdf", pdf, "application/pdf")},
        data={"metadata": json.dumps({"submission_id": 6001})},
        headers=auth_headers,
    )
    assert r.status_code == 202
    mid = r.json()["manuscript_id"]
    document = db_session.get(Document, mid)
    assert document is not None
    assert len(document.figures) == 3
    assert document.figures[2]["caption"]["number"] == 3
    assert (storage_dir / mid / "fig-1.png").exists()
