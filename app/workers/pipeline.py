"""Analysis pipeline launched with FastAPI BackgroundTasks (D-04).

US-01 only wires the hook; US-04, US-06 and US-10 add the stages.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_analysis(manuscript_id: str) -> None:
    """Entry point for the asynchronous analysis of a received manuscript."""
    logger.info("Análisis encolado para el manuscrito %s", manuscript_id)
