"""Run a full pass: every keyword × every device → DB."""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

from ksh_serp.config import (
    DB_PATH, KEYWORDS_CSV, Device, load_ota_domains,
)
from ksh_serp.db import init_db, insert_row
from ksh_serp.parser import parse_serpapi_response
from ksh_serp.serpapi_client import SerpAPIClient


def load_keywords(path: Path = KEYWORDS_CSV) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def run(run_date: str | None = None) -> int:
    rd = run_date or date.today().isoformat()
    init_db(DB_PATH)
    ota_domains = load_ota_domains()
    client = SerpAPIClient()
    keywords = load_keywords()
    devices = [Device.DESKTOP.value, Device.MOBILE.value]

    total = len(keywords) * len(devices)
    done = 0
    failures: list[tuple[str, str, str]] = []

    for kw in keywords:
        for device in devices:
            done += 1
            try:
                resp = client.fetch(kw["query"], device)
                row = parse_serpapi_response(
                    response=resp,
                    query=kw["query"],
                    query_type=kw["type"],
                    device=device,
                    run_date=rd,
                    ota_domains=ota_domains,
                )
                insert_row(DB_PATH, row)
                print(f"[{done}/{total}] OK  {device:7s}  {kw['query']}")
            except Exception as exc:  # noqa: BLE001
                failures.append((kw["query"], device, str(exc)))
                print(f"[{done}/{total}] ERR {device:7s}  {kw['query']}: {exc}")

    if failures:
        print("\nFailures:")
        for q, d, e in failures:
            print(f"  {d:7s} {q}: {e}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(run())
