"""Thin HTTP client for the lead-hunter CLI to talk to the local FastAPI server."""

from __future__ import annotations

import os
from typing import Any

import httpx


class ApiError(RuntimeError):
    """Raised when the local API returns an error response."""


def default_base_url() -> str:
    return os.environ.get("LEAD_HUNTER_API_BASE", "http://127.0.0.1:8000")


class ApiClient:
    def __init__(
        self, base_url: str | None = None, token: str | None = None, timeout: float = 30.0
    ) -> None:
        self.base_url = (base_url or default_base_url()).rstrip("/")
        self.token = (
            token
            or os.environ.get("LEAD_HUNTER_API_TOKEN")
            or os.environ.get("API_ACCESS_TOKEN", "")
        )
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["x-api-key"] = self.token
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.request(
                method, url, headers=self._headers(), timeout=self._timeout, **kwargs
            )
        except httpx.ConnectError as exc:
            raise ApiError(
                f"Could not reach the lead-hunter API at {self.base_url}. "
                "Is the backend running? Start it with: uvicorn api.app:app --reload --port 8000"
            ) from exc
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(f"{method} {path} failed ({response.status_code}): {detail}")
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/health")

    def create_hunt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/hunts", json=payload)

    def get_hunt_status(self, hunt_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/hunts/{hunt_id}/status")

    def get_hunt_result(self, hunt_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/hunts/{hunt_id}/result")

    def list_hunts(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/hunts")
