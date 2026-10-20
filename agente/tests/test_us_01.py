"""US-01 · Recibir PDF por API."""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.models import Manuscript, ManuscriptStatus


@pytest.fixture(autouse=True)
def no_pipeline(monkeypatch):
    """US-01 ends at `received`; the analysis stages belong to US-04+ and are tested there."""
    from app.api import manuscripts as mod

    launched: list[str] = []
    monkeypatch.setattr(mod, "run_analysis", launched.append)
    return launched


def _upload(client, headers, content: bytes, metadata: dict | None, filename: str = "manuscrito.pdf"):
    files = {"file": (filename, content, "application/pdf")}
    data = {"metadata": json.dumps(metadata)} if metadata is not None else {}
    return client.post("/manuscripts", files=files, data=data, headers=headers)


def _count(db_session, submission_id: int) -> int:
    return db_session.scalar(select(func.count()).select_from(Manuscript).where(Manuscript.submission_id == submission_id))


@pytest.fixture(scope="module")
def valid_pdf(pdf_dir: Path) -> bytes:
    return (pdf_dir / "sin_figuras.pdf").read_bytes()


def test_t01_valid_pdf_returns_202_and_received(client, auth_headers, db_session, valid_pdf, no_pipeline):
    r = _upload(client, auth_headers, valid_pdf, {"submission_id": 1001, "section_id": 2, "title": "Prueba", "locale": "es_ES"})
    assert r.status_code == 202, r.text
    body = r.json()
    uuid.UUID(body["manuscript_id"])  # must be a UUID
    assert body["status"] == "received"
    assert no_pipeline == [body["manuscript_id"]], "el análisis debe encolarse una vez"

    row = db_session.get(Manuscript, body["manuscript_id"])
    assert row is not None
    assert row.status == ManuscriptStatus.RECEIVED
    assert row.submission_id == 1001
    assert row.section_id == 2
    assert row.title == "Prueba"
    assert row.size_bytes == len(valid_pdf)


def test_ac04_file_stored_with_matching_sha256(client, auth_headers, db_session, storage_dir, valid_pdf):
    r = _upload(client, auth_headers, valid_pdf, {"submission_id": 1002})
    assert r.status_code == 202
    mid = r.json()["manuscript_id"]
    stored = storage_dir / f"{mid}.pdf"
    assert stored.exists()
    assert hashlib.sha256(stored.read_bytes()).hexdigest() == db_session.get(Manuscript, mid).sha256


def test_t02_identical_resubmission_returns_200_duplicate(client, auth_headers, db_session, valid_pdf, no_pipeline):
    first = _upload(client, auth_headers, valid_pdf, {"submission_id": 1003})
    second = _upload(client, auth_headers, valid_pdf, {"submission_id": 1003})
    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["manuscript_id"] == first.json()["manuscript_id"]
    assert second.json()["duplicate"] is True
    assert _count(db_session, 1003) == 1
    assert len(no_pipeline) == 1, "un reenvío idéntico no se re-analiza (D-01)"


def test_t03_docx_renamed_as_pdf_returns_400(client, auth_headers, db_session, storage_dir):
    fake = b"PK\x03\x04" + b"\x00" * 2048  # firma ZIP (DOCX)
    before = {p.name for p in storage_dir.glob("*.pdf")} if storage_dir.exists() else set()
    r = _upload(client, auth_headers, fake, {"submission_id": 1004}, filename="trabajo.pdf")
    assert r.status_code == 400
    assert r.json()["detail"] == {"error": "not_pdf"}
    assert _count(db_session, 1004) == 0
    after = {p.name for p in storage_dir.glob("*.pdf")} if storage_dir.exists() else set()
    assert before == after


def test_t04_pdf_over_25mb_returns_413(client, auth_headers, db_session):
    big = b"%PDF-1.4\n" + b"\0" * (26 * 1024 * 1024)
    r = _upload(client, auth_headers, big, {"submission_id": 1005})
    assert r.status_code == 413
    assert _count(db_session, 1005) == 0


def test_t05_metadata_without_submission_id_returns_422(client, auth_headers, valid_pdf):
    r = _upload(client, auth_headers, valid_pdf, {"title": "sin id"})
    assert r.status_code == 422
    assert any("submission_id" in str(err.get("loc", "")) for err in r.json()["detail"])


def test_t05b_missing_metadata_returns_422(client, auth_headers, valid_pdf):
    r = _upload(client, auth_headers, valid_pdf, None)
    assert r.status_code == 422


def test_t06_pdf_signature_validator():
    from app.api.manuscripts import is_pdf_signature

    assert is_pdf_signature(b"%PDF-1.7\n%\xe2\xe3")
    assert not is_pdf_signature(b"PK\x03\x04")
    assert not is_pdf_signature(b"")


def test_t07_disk_failure_leaves_no_orphan_record(client, auth_headers, db_session, valid_pdf, monkeypatch):
    from app.api import manuscripts as mod

    def boom(path, content):
        raise OSError("disco lleno")

    monkeypatch.setattr(mod, "store_pdf", boom)
    r = _upload(client, auth_headers, valid_pdf, {"submission_id": 1007})
    assert r.status_code == 500
    assert _count(db_session, 1007) == 0


def test_missing_or_wrong_token_returns_401(client, valid_pdf):
    r = _upload(client, {}, valid_pdf, {"submission_id": 1008})
    assert r.status_code == 401
    r = _upload(client, {"Authorization": "Bearer incorrecto"}, valid_pdf, {"submission_id": 1008})
    assert r.status_code == 401


def test_migration_created_manuscripts_table(db_session):
    from sqlalchemy import inspect

    assert "manuscripts" in inspect(db_session.get_bind()).get_table_names()
