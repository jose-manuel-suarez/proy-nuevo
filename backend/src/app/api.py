"""Versioned API routes.

The API is reachable only from the frontend container, but the service token
keeps the boundary explicit so a misconfigured network does not silently
expose an unauthenticated API on the host.
"""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

router = APIRouter(tags=["api"])


def require_service_token(request: Request) -> None:
    expected: str = request.app.state.settings.service_token
    provided = request.headers.get("x-service-token", "")
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid service token",
        )


ServiceAuth = Annotated[None, Depends(require_service_token)]


@router.get("/info")
async def info(request: Request, _: ServiceAuth) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "service": "backend",
        "version": "0.1.0",
        "environment": settings.app_env,
    }
