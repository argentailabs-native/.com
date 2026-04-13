from __future__ import annotations

import os
from typing import Any

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class MetaApiError(Exception):
    """Raised for Meta API failures."""


class MetaAdsClient:
    def __init__(self) -> None:
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.api_version = os.getenv("META_API_VERSION", "v20.0")
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        if not self.access_token:
            raise MetaApiError("META_ACCESS_TOKEN is missing")

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type((requests.RequestException, MetaApiError)),
    )
    def get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = {**params, "access_token": self.access_token}
        response = requests.get(f"{self.base_url}/{endpoint}", params=payload, timeout=45)
        if response.status_code == 429:
            raise MetaApiError("Rate limited by Meta API")
        if response.status_code >= 400:
            raise MetaApiError(f"Meta GET error {response.status_code}: {response.text}")

        body = response.json()
        if "error" in body:
            raise MetaApiError(f"Meta API returned error: {body['error']}")
        return body

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type((requests.RequestException, MetaApiError)),
    )
    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = {**data, "access_token": self.access_token}
        response = requests.post(f"{self.base_url}/{endpoint}", data=payload, timeout=45)
        if response.status_code == 429:
            raise MetaApiError("Rate limited by Meta API")
        if response.status_code >= 400:
            raise MetaApiError(f"Meta POST error {response.status_code}: {response.text}")

        body = response.json()
        if "error" in body:
            raise MetaApiError(f"Meta API returned error: {body['error']}")
        return body
