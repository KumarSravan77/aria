from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


class ConfluenceClient:
    """Small Confluence connector.

    For local demos, read pages from examples/confluence/*.json.
    For enterprise use, set CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, and
    CONFLUENCE_API_TOKEN, then call fetch_pages_from_space().
    """

    def __init__(self, base_url: str | None = None, email: str | None = None, api_token: str | None = None):
        self.base_url = (base_url or os.getenv("CONFLUENCE_BASE_URL") or "").rstrip("/")
        self.email = email or os.getenv("CONFLUENCE_EMAIL")
        self.api_token = api_token or os.getenv("CONFLUENCE_API_TOKEN")

    def load_local_pages(self, path: str | Path) -> list[dict[str, Any]]:
        data = json.loads(Path(path).read_text())
        return data.get("pages", data if isinstance(data, list) else [])

    def fetch_pages_from_space(self, space_key: str, limit: int = 25) -> list[dict[str, Any]]:
        if not self.base_url or not self.email or not self.api_token:
            raise RuntimeError("Confluence API credentials are not configured")
        url = f"{self.base_url}/wiki/rest/api/content"
        params = {"spaceKey": space_key, "type": "page", "expand": "body.storage,metadata.labels,version", "limit": limit}
        response = requests.get(url, params=params, auth=(self.email, self.api_token), timeout=30)
        response.raise_for_status()
        pages = []
        for item in response.json().get("results", []):
            labels = [label.get("name") for label in item.get("metadata", {}).get("labels", {}).get("results", [])]
            pages.append({
                "page_id": item.get("id"),
                "title": item.get("title"),
                "space": space_key,
                "labels": labels,
                "last_updated": item.get("version", {}).get("when"),
                "body": item.get("body", {}).get("storage", {}).get("value", ""),
            })
        return pages
