"""Run once to capture a SerpAPI response as a test fixture.

Usage:
    python scripts/capture_fixture.py "kauai shores hotel" desktop brand_aio_desktop
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import serpapi

from ksh_serp.config import GL, HL, GOOGLE_DOMAIN, SERPAPI_API_KEY


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: capture_fixture.py <query> <desktop|mobile> <fixture_name>")
        return 1

    query, device, name = sys.argv[1], sys.argv[2], sys.argv[3]
    if not SERPAPI_API_KEY:
        print("ERROR: SERPAPI_API_KEY not set in .env")
        return 2

    client = serpapi.Client(api_key=SERPAPI_API_KEY)
    res = client.search({
        "engine": "google",
        "q": query,
        "gl": GL,
        "hl": HL,
        "google_domain": GOOGLE_DOMAIN,
        "device": device,
    })
    out = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res.as_dict(), indent=2))
    print(f"Saved {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
