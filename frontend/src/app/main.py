"""Flask application factory."""

from __future__ import annotations

from flask import Flask

from app import health, views
from app.api import BackendClient
from app.config import Settings, get_settings


def create_app(
    settings: Settings | None = None,
    *,
    backend_client: BackendClient | None = None,
) -> Flask:
    resolved = settings or get_settings()

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=resolved.secret_key,
        APP_ENV=resolved.app_env,
        SERVICE_TOKEN=resolved.service_token,
        BACKEND_URL=resolved.backend_url,
        REQUEST_TIMEOUT=resolved.request_timeout,
    )

    app.extensions["backend_client"] = backend_client or BackendClient(
        base_url=resolved.backend_url,
        service_token=resolved.service_token,
        timeout=resolved.request_timeout,
    )

    app.register_blueprint(views.bp)
    app.register_blueprint(health.bp)

    return app
