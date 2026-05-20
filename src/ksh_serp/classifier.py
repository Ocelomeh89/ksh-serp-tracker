"""Domain classification: is it KSH, is it an OTA."""
from __future__ import annotations

from urllib.parse import urlparse

from ksh_serp.config import KSH_DOMAINS


def extract_domain(url: str) -> str:
    """Return registrable domain in lowercase. Strips subdomains like www, m, secure."""
    if not url:
        return ""
    try:
        netloc = urlparse(url).netloc.lower()
    except ValueError:
        return ""
    if not netloc:
        return ""
    netloc = netloc.split(":")[0]
    parts = netloc.split(".")
    if len(parts) < 2:
        return ""
    return ".".join(parts[-2:])


def is_ksh(url: str) -> bool:
    return extract_domain(url) in KSH_DOMAINS


def is_ota(url: str, ota_domains: frozenset[str]) -> bool:
    return extract_domain(url) in ota_domains
