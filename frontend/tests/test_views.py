from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.api import BackendClient
from app.config import Settings
from app.main import create_app

Handler = Callable[[httpx.Request], httpx.Response]


def _success(request: httpx.Request) -> httpx.Response:
    assert request.headers["x-service-token"] == "test-service-token"
    return httpx.Response(
        200,
        json={"service": "backend", "version": "0.1.0", "environment": "development"},
    )


def _failure(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(503, json={"detail": "unavailable"})


@pytest.fixture
def app_factory(
    settings: Settings,
) -> Callable[[Handler], Flask]:
    def build(handler: Handler) -> Flask:
        backend = BackendClient(
            base_url="http://backend.test",
            service_token=settings.service_token,
            timeout=settings.request_timeout,
            transport=httpx.MockTransport(handler),
        )
        return create_app(settings, backend_client=backend)

    return build


@pytest.fixture
def client(app_factory: Callable[[Handler], Flask]) -> FlaskClient:
    return app_factory(_success).test_client()


def test_index_renders_backend_metadata(client: FlaskClient) -> None:
    response = client.get("/")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Service status" in body
    assert "<dd>backend</dd>" in body
    assert "Refresh status" in body


def test_index_renders_a_controlled_error_state(
    app_factory: Callable[[Handler], Flask],
) -> None:
    response = app_factory(_failure).test_client().get("/")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Backend unavailable" in body
    assert "503" in body


def test_status_fragment_is_a_fragment(client: FlaskClient) -> None:
    response = client.get("/partials/status")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<html" not in body
    assert "backend" in body


def test_healthz_does_not_touch_the_backend(
    app_factory: Callable[[Handler], Flask],
) -> None:
    response = app_factory(_failure).test_client().get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readyz_reports_backend_up(client: FlaskClient) -> None:
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "backend": "up"}


def test_readyz_reports_backend_down(
    app_factory: Callable[[Handler], Flask],
) -> None:
    response = app_factory(_failure).test_client().get("/readyz")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable", "backend": "down"}


def test_assets_are_served_locally(client: FlaskClient) -> None:
    body = client.get("/").get_data(as_text=True)

    assert 'src="/static/htmx.min.js"' in body
    assert "https://" not in body
    assert "http://" not in body
