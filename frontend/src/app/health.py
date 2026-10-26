"""Health and readiness endpoints for the frontend."""

from __future__ import annotations

from flask import Blueprint

from app.api import ApiError
from app.views import _backend

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def healthz() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@bp.get("/readyz")
def readyz() -> tuple[dict[str, str], int]:
    try:
        _backend().info()
    except ApiError:
        return {"status": "unavailable", "backend": "down"}, 503
    return {"status": "ok", "backend": "up"}, 200
