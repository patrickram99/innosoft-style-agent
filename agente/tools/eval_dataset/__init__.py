"""Synthetic evaluation dataset (D-09): generator, evaluator and statistics. Process tool, not part of the product."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # agente/
TOOL_DIR = Path(__file__).resolve().parent
EVAL_DIR = ROOT / "evaluacion"
DATASET_DIR = EVAL_DIR / "dataset"  # PDFs and build files (git-ignored, reproducible from the seed)
RESULTS_DIR = EVAL_DIR / "resultados"  # versioned: CSV, summary and charts
MANIFEST = EVAL_DIR / "manifest.json"  # versioned ground truth
CONTENT_BANK = TOOL_DIR / "contenido.json"  # versioned text bank written by Gemini
TEMPLATES = ROOT / "docs" / "plantillas"
RULES_FILE = ROOT / "rules" / "innosoft" / "figuras.yaml"
