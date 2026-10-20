"""Shared fixtures. Tests run on SQLite (no Docker needed); the schema comes from the Alembic migrations."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIXTURES_DIR = ROOT / "tests" / "fixtures"
PDF_DIR = FIXTURES_DIR / "pdfs"
MUESTRAS_DIR = ROOT / "muestras"
SCRATCH = ROOT / ".pytest_cache"
EXPECTED_PDFS = [
    "figuras_pequenas.pdf", "figuras_baja_dpi.pdf", "sin_figuras.pdf", "escaneado.pdf",
    "correcto.pdf", "vectorial.pdf", "corrupto.pdf", "treinta_paginas.pdf",
]


def pytest_configure(config: pytest.Config) -> None:
    """Point the app at a throwaway SQLite database before anything imports app.config."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    db = SCRATCH / "agent-test.sqlite"
    if db.exists():
        db.unlink()
    storage = SCRATCH / "storage"
    shutil.rmtree(storage, ignore_errors=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{db.as_posix()}"
    os.environ["AGENT_SERVICE_TOKEN"] = "test-token"
    os.environ["STORAGE_DIR"] = str(storage)

    from tests.fixtures.generate_pdfs import generate_all

    if not all((PDF_DIR / name).exists() for name in EXPECTED_PDFS):
        generate_all(PDF_DIR)

    _migrate()


def _migrate() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    command.upgrade(cfg, "head")


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


@pytest.fixture(scope="session")
def auth_headers(service_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {service_token}"}


@pytest.fixture(scope="session")
def storage_dir() -> Path:
    return Path(os.environ["STORAGE_DIR"])


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    from app.db import get_session_factory

    with get_session_factory()() as session:
        yield session
