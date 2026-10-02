"""FastAPI application factory."""
from fastapi import FastAPI

from app.api import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agente de sugerencias estilísticas · Innosoft",
        version="0.1.0",
        description="Analiza manuscritos PDF enviados a la revista Innovación y Software.",
    )
    app.include_router(health.router)
    return app


app = create_app()
