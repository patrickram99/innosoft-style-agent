"""FastAPI application factory. Rules are loaded at startup; an invalid rule file stops the API."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health, manuscripts, rules
from app.config import get_settings
from app.rules import load_rules

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    rule_set = load_rules(settings.rules_dir, settings.rules_schema)  # raises RuleLoadError → no startup
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
    app.include_router(rules.router)
    return app


app = create_app()
