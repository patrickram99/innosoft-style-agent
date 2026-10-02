"""FastAPI application factory. Rules are loaded at startup; an invalid rule file stops the API."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import findings, health, manuscripts, rules
from app.rules import get_rule_set, reset_rule_set_cache

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    reset_rule_set_cache()
    rule_set = get_rule_set()  # raises RuleLoadError → the API does not start
    app.state.rules = rule_set
    logger.info("API lista con %d reglas (hash %s)", len(rule_set.rules), rule_set.rules_hash[:12])
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agente de sugerencias estilísticas · Innosoft",
        version="0.1.0",
        description="Analiza manuscritos PDF enviados a la revista Innovación y Software.",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(manuscripts.router)
    app.include_router(findings.router)
    app.include_router(rules.router)
    return app


app = create_app()
