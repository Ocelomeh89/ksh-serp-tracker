"""Thin wrapper around the SerpAPI SDK with raw-response archiving."""
from __future__ import annotations

import gzip
import json
import time
from datetime import datetime, timezone
from typing import Any

import serpapi

from ksh_serp.config import GL, HL, GOOGLE_DOMAIN, RAW_DIR, SERPAPI_API_KEY


class SerpAPIClient:
    def __init__(self, api_key: str | None = None, max_retries: int = 3) -> None:
        self.client = serpapi.Client(api_key=api_key or SERPAPI_API_KEY)
        self.max_retries = max_retries

    def fetch(self, query: str, device: str) -> dict[str, Any]:
        params = {
            "engine": "google",
            "q": query,
            "gl": GL,
            "hl": HL,
            "google_domain": GOOGLE_DOMAIN,
            "device": device,
        }
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                res = self.client.search(params)
                data = res.as_dict()
                self._archive(query, device, data)
                return data
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(2 ** attempt)
        raise RuntimeError(f"SerpAPI failed after retries for {query!r}: {last_err}")

    @staticmethod
    def _archive(query: str, device: str, data: dict[str, Any]) -> None:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        safe = "".join(c if c.isalnum() else "_" for c in query)[:60]
        out = RAW_DIR / f"{ts}__{device}__{safe}.json.gz"
        with gzip.open(out, "wt") as f:
            json.dump(data, f)
