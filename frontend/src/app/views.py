"""Page and fragment routes."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, current_app, render_template

from app.api import ApiError, BackendClient

bp = Blueprint("views", __name__)


def _backend() -> BackendClient:
    client: BackendClient = current_app.extensions["backend_client"]
    return client


def _load_status() -> tuple[dict[str, Any] | None, str | None]:
    try:
        return _backend().info(), None
    except ApiError as error:
        return None, str(error)


@bp.get("/")
def index() -> str:
    info, error = _load_status()
    return render_template("index.html", info=info, error=error)


@bp.get("/partials/status")
def status_partial() -> str:
    info, error = _load_status()
    return render_template("partials/status.html", info=info, error=error)
