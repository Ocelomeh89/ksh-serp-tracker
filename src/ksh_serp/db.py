"""SQLite storage. One row per (run_date, query, device)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

JSON_FIELDS = {"aio_sources", "ota_ads", "top_3_organic_domains"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS serp_runs (
    run_date TEXT NOT NULL,
    query TEXT NOT NULL,
    query_type TEXT NOT NULL,
    device TEXT NOT NULL,
    aio_present INTEGER NOT NULL,
    aio_sources TEXT NOT NULL,
    ksh_cited_in_aio INTEGER NOT NULL,
    ads_count INTEGER NOT NULL,
    ota_ads TEXT NOT NULL,
    hotel_pack_present INTEGER NOT NULL,
    ksh_in_hotel_pack INTEGER NOT NULL,
    ksh_organic_pos INTEGER,
    top_3_organic_domains TEXT NOT NULL,
    screenshot_url TEXT,
    PRIMARY KEY (run_date, query, device)
);

CREATE INDEX IF NOT EXISTS idx_query_type ON serp_runs(query_type);
CREATE INDEX IF NOT EXISTS idx_run_date ON serp_runs(run_date);
"""


def init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.executescript(SCHEMA)


def insert_row(path: Path, row: dict[str, Any]) -> None:
    payload = {**row}
    for f in JSON_FIELDS:
        payload[f] = json.dumps(payload[f])
    cols = ",".join(payload.keys())
    placeholders = ",".join(["?"] * len(payload))
    sql = f"INSERT OR REPLACE INTO serp_runs ({cols}) VALUES ({placeholders})"
    with sqlite3.connect(path) as con:
        con.execute(sql, tuple(payload.values()))


def fetch_all_rows(path: Path) -> list[dict[str, Any]]:
    with sqlite3.connect(path) as con:
        con.row_factory = sqlite3.Row
        cur = con.execute("SELECT * FROM serp_runs ORDER BY run_date, query, device")
        rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        for f in JSON_FIELDS:
            r[f] = json.loads(r[f])
    return rows


def fetch_latest_run_date(path: Path) -> str | None:
    with sqlite3.connect(path) as con:
        cur = con.execute("SELECT MAX(run_date) FROM serp_runs")
        return cur.fetchone()[0]
