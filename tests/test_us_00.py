"""US-00 · Entorno base: salud de la API, conexión a BD, corpus de fixtures y JSON Schema."""
import json
import re
from pathlib import Path

import fitz
import jsonschema

from tests.conftest import ROOT

REQUIRED_PDFS = ["figuras_pequenas.pdf", "figuras_baja_dpi.pdf", "sin_figuras.pdf", "escaneado.pdf", "correcto.pdf"]
ORCID_RE = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b")


def test_t01_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_t02_database_select_1():
    from app.db import check_connection

    assert check_connection() is True


def test_ac04_corpus_has_five_pdfs(pdf_dir: Path):
    for name in REQUIRED_PDFS:
        assert (pdf_dir / name).exists(), name
    assert (pdf_dir / "README.md").exists()


def test_t04_no_emails_or_orcid_in_fixtures(pdf_dir: Path):
    for pdf in pdf_dir.glob("*.pdf"):
        if pdf.name == "corrupto.pdf":
            continue
        with fitz.open(pdf) as doc:
            text = "".join(page.get_text() for page in doc)
        assert "@" not in text, pdf.name
        assert not ORCID_RE.search(text), pdf.name


def test_rule_schema_is_valid_json_schema():
    schema = json.loads((ROOT / "rules" / "schema" / "rule.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


def test_repo_layout_matches_spec_section_13():
    for rel in [
        "app/api", "app/extraction", "app/models", "app/rules/evaluators", "app/suggestion",
        "app/review", "app/ojs", "app/workers", "rules/innosoft", "rules/schema",
        "prompts/sugerencia", "specs", "tests/fixtures/pdfs", "docs", "alembic",
        "docker-compose.yml", ".github/workflows/ci.yml", ".env.example",
    ]:
        assert (ROOT / rel).exists(), rel
