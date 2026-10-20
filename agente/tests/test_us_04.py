"""US-04 · Extraer texto y páginas."""
from __future__ import annotations

import json
import time
from pathlib import Path

import fitz
import pytest

from app.extraction.text import extract_text
from app.models import Document, Manuscript, ManuscriptStatus

CORPUS = ["figuras_pequenas.pdf", "figuras_baja_dpi.pdf", "sin_figuras.pdf", "escaneado.pdf", "correcto.pdf"]


def test_t01_corpus_four_extracted_one_unreadable(pdf_dir: Path):
    statuses = {name: extract_text(pdf_dir / name).status for name in CORPUS}
    assert sum(s == "extracted" for s in statuses.values()) == 4, statuses
    assert statuses["escaneado.pdf"] == "unreadable"


def test_ac01_fifteen_pages_with_blocks_font_size_bbox(pdf_dir: Path):
    result = extract_text(pdf_dir / "sin_figuras.pdf")
    assert result.status == "extracted"
    doc = result.document
    assert doc.page_count == 15
    first = doc.pages[0]
    assert first.page == 1 and first.width == 612 and first.height == 792
    assert first.blocks, "la primera página debe tener bloques"
    for block in first.blocks:
        assert len(block.bbox) == 4
        assert block.text and block.font and block.size > 0
    assert all(p.blocks for p in doc.pages), "ninguna página de texto debe quedar vacía"


def test_t02_bold_block_flagged(pdf_dir: Path):
    doc = extract_text(pdf_dir / "sin_figuras.pdf").document
    title = next(b for b in doc.pages[0].blocks if b.text.startswith("Articulo sin figuras"))
    assert title.bold is True
    assert title.size == 18.0
    body = next(b for b in doc.pages[1].blocks if b.text.startswith("Se presenta"))
    assert body.bold is False and body.italic is False


def test_ac02_scanned_pdf_is_unreadable_no_text_layer(pdf_dir: Path):
    result = extract_text(pdf_dir / "escaneado.pdf")
    assert result.status == "unreadable"
    assert result.reason == "no_text_layer"
    assert result.document is None


def test_t04_truncated_pdf_is_unreadable_corrupt(pdf_dir: Path):
    result = extract_text(pdf_dir / "corrupto.pdf")
    assert result.status == "unreadable"
    assert result.reason == "corrupt"


def test_garbage_bytes_are_unreadable_corrupt():
    result = extract_text(b"%PDF-1.4\nesto no es un pdf")
    assert result.status == "unreadable"
    assert result.reason == "corrupt"


def test_encrypted_pdf_is_unreadable_encrypted(pdf_dir: Path):
    with fitz.open(pdf_dir / "sin_figuras.pdf") as src:
        data = src.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="propietario", user_pw="usuario")
    result = extract_text(data)
    assert result.status == "unreadable"
    assert result.reason == "encrypted"


def test_empty_intermediate_page_is_kept_with_no_blocks(tmp_path: Path):
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page()
        if i != 1:
            page.insert_text((72, 100), "Texto suficiente para superar el umbral de caracteres por pagina " * 3)
    path = tmp_path / "hueco.pdf"
    doc.save(path)
    result = extract_text(path)
    assert result.status == "extracted"
    assert [p.page for p in result.document.pages] == [1, 2, 3]
    assert result.document.pages[1].blocks == []


def test_t03_thirty_pages_under_ten_seconds(pdf_dir: Path):
    start = time.perf_counter()
    result = extract_text(pdf_dir / "treinta_paginas.pdf")
    elapsed = time.perf_counter() - start
    assert result.status == "extracted" and result.document.page_count == 30
    assert elapsed < 10, f"extracción en {elapsed:.2f} s"


def test_ac04_document_persisted_via_api(client, auth_headers, db_session, pdf_dir: Path):
    pdf = (pdf_dir / "sin_figuras.pdf").read_bytes()
    r = client.post(
        "/manuscripts",
        files={"file": ("sin_figuras.pdf", pdf, "application/pdf")},
        data={"metadata": json.dumps({"submission_id": 4001})},
        headers=auth_headers,
    )
    assert r.status_code == 202
    mid = r.json()["manuscript_id"]
    # TestClient runs BackgroundTasks before returning, so the pipeline has already run.
    manuscript = db_session.get(Manuscript, mid)
    assert manuscript.status in (ManuscriptStatus.EXTRACTED, ManuscriptStatus.VALIDATED, ManuscriptStatus.READY_FOR_REVIEW)
    document = db_session.get(Document, mid)
    assert document is not None
    assert document.page_count == 15
    assert document.pages[0]["blocks"][0]["font"]


def test_scanned_upload_ends_unreadable_with_reason(client, auth_headers, db_session, pdf_dir: Path):
    pdf = (pdf_dir / "escaneado.pdf").read_bytes()
    r = client.post(
        "/manuscripts",
        files={"file": ("escaneado.pdf", pdf, "application/pdf")},
        data={"metadata": json.dumps({"submission_id": 4002})},
        headers=auth_headers,
    )
    assert r.status_code == 202
    manuscript = db_session.get(Manuscript, r.json()["manuscript_id"])
    assert manuscript.status == ManuscriptStatus.UNREADABLE
    assert manuscript.status_reason == "no_text_layer"
    assert db_session.get(Document, manuscript.id) is None
