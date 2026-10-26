from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from app.api import ApiError, BackendClient


def _ok_handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/api/v1/info"
    assert request.headers["x-service-token"] == "test-service-token"
    return httpx.Response(
        200,
        json={"service": "backend", "version": "0.1.0", "environment": "development"},
    )


def test_info_returns_the_backend_payload(
    backend_factory: Callable[[Callable[[httpx.Request], httpx.Response]], BackendClient],
) -> None:
    client = backend_factory(_ok_handler)

    payload = client.info()

    assert payload["service"] == "backend"
    client.close()


def test_timeout_becomes_a_controlled_error(
    backend_factory: Callable[[Callable[[httpx.Request], httpx.Response]], BackendClient],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    client = backend_factory(handler)

    with pytest.raises(ApiError, match="unreachable"):
        client.info()
    client.close()


def test_upstream_error_status_becomes_a_controlled_error(
    backend_factory: Callable[[Callable[[httpx.Request], httpx.Response]], BackendClient],
) -> None:
    client = backend_factory(lambda _request: httpx.Response(503, json={"detail": "nope"}))

    with pytest.raises(ApiError, match="503"):
        client.info()
    client.close()


def test_invalid_payload_becomes_a_controlled_error(
    backend_factory: Callable[[Callable[[httpx.Request], httpx.Response]], BackendClient],
) -> None:
    client = backend_factory(
        lambda _request: httpx.Response(
            200, content=b"not json", headers={"content-type": "text/plain"}
        )
    )

    with pytest.raises(ApiError, match="invalid payload"):
        client.info()
    client.close()
