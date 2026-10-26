from __future__ import annotations

from fastapi.testclient import TestClient

SERVICE_TOKEN = "test-service-token"


def test_info_requires_a_service_token(client: TestClient) -> None:
    response = client.get("/api/v1/info")

    assert response.status_code == 401


def test_info_rejects_a_wrong_service_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/info",
        headers={"X-Service-Token": "not-the-token"},
    )

    assert response.status_code == 401


def test_info_returns_service_metadata(client: TestClient) -> None:
    response = client.get(
        "/api/v1/info",
        headers={"X-Service-Token": SERVICE_TOKEN},
    )

    assert response.status_code == 200
    assert response.json() == {
        "service": "backend",
        "version": "0.1.0",
        "environment": "development",
    }
