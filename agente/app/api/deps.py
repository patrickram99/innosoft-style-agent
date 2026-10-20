"""Shared FastAPI dependencies: database session and service-token authentication."""
from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, status

from app.config import Settings, get_settings
from app.db import get_db  # noqa: F401  (re-exported for routers)


def require_service_token(request: Request, settings: Settings = Depends(get_settings)) -> None:
    """Validate `Authorization: Bearer <token>` against AGENT_SERVICE_TOKEN."""
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token or not secrets.compare_digest(token, settings.agent_service_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "unauthorized"})
