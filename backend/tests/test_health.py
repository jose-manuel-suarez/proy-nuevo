from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import get_session
from app.main import create_app


class _FakeSession:
    def __init__(self, *, fail: bool) -> None:
        self._fail = fail

    async def execute(self, _statement: object) -> None:
        if self._fail:
            raise RuntimeError("database is down")


def test_healthz_does_not_require_a_database(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_reports_ok_when_the_database_answers(app: FastAPI, client: TestClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession(fail=False)

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_readyz_reports_unavailable_when_the_database_fails(
    app: FastAPI, client: TestClient
) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession(fail=True)

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down"}


@pytest.mark.integration
def test_readyz_against_a_real_database() -> None:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")

    settings = Settings(_env_file=None, database_url=url, service_token="token")
    application = create_app(settings)

    with TestClient(application) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["database"] == "up"
