"""Paths, constants, env loading."""
from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw_responses"
DB_PATH = DATA_DIR / "serp.db"
KEYWORDS_CSV = DATA_DIR / "keywords.csv"
OTA_DOMAINS_FILE = DATA_DIR / "ota_domains.txt"

KSH_DOMAINS = frozenset({"kauaishoreshotel.com", "kauaishores.com"})

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

GL = "us"
HL = "en"
GOOGLE_DOMAIN = "google.com"


class QueryType(str, Enum):
    BRAND = "brand"
    NONBRAND = "nonbrand"


class Device(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"


def load_ota_domains() -> frozenset[str]:
    if not OTA_DOMAINS_FILE.exists():
        return frozenset()
    return frozenset(
        line.strip().lower()
        for line in OTA_DOMAINS_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    )
