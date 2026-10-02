"""Shared fixtures. Tests run on SQLite (no Docker needed)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIXTURES_DIR = ROOT / "tests" / "fixtures"
PDF_DIR = FIXTURES_DIR / "pdfs"
MUESTRAS_DIR = ROOT / "muestras"
EXPECTED_PDFS = [
    "figuras_pequenas.pdf", "figuras_baja_dpi.pdf", "sin_figuras.pdf", "escaneado.pdf",
    "correcto.pdf", "vectorial.pdf", "corrupto.pdf", "treinta_paginas.pdf",
]


def pytest_configure(config: pytest.Config) -> None:
    """Point the app at a throwaway SQLite database before anything imports app.config."""
    scratch = ROOT / ".pytest_cache"
    scratch.mkdir(parents=True, exist_ok=True)
    db = scratch / "agent-test.sqlite"
    if db.exists():
        db.unlink()
    os.environ["DATABASE_URL"] = f"sqlite:///{db.as_posix()}"
    os.environ["AGENT_SERVICE_TOKEN"] = "test-token"
    os.environ["STORAGE_DIR"] = str(scratch / "storage")

    from tests.fixtures.generate_pdfs import generate_all

    if not all((PDF_DIR / name).exists() for name in EXPECTED_PDFS):
        generate_all(PDF_DIR)


@pytest.fixture(scope="session")
def pdf_dir() -> Path:
    return PDF_DIR


@pytest.fixture(scope="session")
def muestras_dir() -> Path:
    pdfs = MUESTRAS_DIR / "pdf"
    if not pdfs.exists() or not any(pdfs.glob("*.pdf")):
        pytest.skip("muestras/pdf/ no existe en este entorno")
    return pdfs


@pytest.fixture(scope="session")
def service_token() -> str:
    return os.environ["AGENT_SERVICE_TOKEN"]


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
