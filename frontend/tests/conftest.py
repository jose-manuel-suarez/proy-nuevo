from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from app.api import BackendClient
from app.config import Settings

SERVICE_TOKEN = "test-service-token"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        secret_key="test-secret",
        service_token=SERVICE_TOKEN,
        backend_url="http://backend.test",
        request_timeout=1.0,
    )


@pytest.fixture
def backend_factory() -> Callable[[Callable[[httpx.Request], httpx.Response]], BackendClient]:
    def build(handler: Callable[[httpx.Request], httpx.Response]) -> BackendClient:
        return BackendClient(
            base_url="http://backend.test",
            service_token=SERVICE_TOKEN,
            timeout=1.0,
            transport=httpx.MockTransport(handler),
        )

    return build
