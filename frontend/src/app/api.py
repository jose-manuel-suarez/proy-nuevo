"""HTTP client for the backend API.

Failures are converted into a single `ApiError` so views can render a
controlled error state instead of leaking transport details into templates.
"""

from __future__ import annotations

from typing import Any

import httpx


class ApiError(RuntimeError):
    """Raised when the backend cannot produce a usable response."""


class BackendClient:
    def __init__(
        self,
        *,
        base_url: str,
        service_token: str,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
            headers={"X-Service-Token": service_token},
        )

    def info(self) -> dict[str, Any]:
        try:
            response = self._client.get("/api/v1/info")
        except httpx.HTTPError as error:
            raise ApiError("backend is unreachable") from error

        if response.status_code != httpx.codes.OK:
            raise ApiError(f"backend responded with status {response.status_code}")

        try:
            payload = response.json()
        except ValueError as error:
            raise ApiError("backend returned an invalid payload") from error

        if not isinstance(payload, dict):
            raise ApiError("backend returned an unexpected payload shape")

        return payload

    def close(self) -> None:
        self._client.close()
