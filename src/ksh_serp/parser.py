"""Parse a SerpAPI Google response into a flat row dict.

SerpAPI shapes vary slightly across queries. We handle the documented variants:
- AI overview lives at `ai_overview` or `inline_ai_overview`, with references in
  `references` or nested in `text_blocks[].references`.
- Hotel pack lives at `inline_hotels.hotels`, `hotels_results.properties`,
  or `local_results.places`.
"""
from __future__ import annotations

from typing import Any

from ksh_serp.classifier import extract_domain, is_ksh, is_ota


def parse_serpapi_response(
    response: dict[str, Any],
    *,
    query: str,
    query_type: str,
    device: str,
    run_date: str,
    ota_domains: frozenset[str],
) -> dict[str, Any]:
    """Flatten one SerpAPI response into a row ready for DB insert."""
    aio = response.get("ai_overview") or response.get("inline_ai_overview") or {}
    aio_present = 1 if aio else 0
    aio_sources = _extract_aio_sources(aio)
    ksh_cited = 1 if any(is_ksh(s.get("url", "")) for s in aio_sources) else 0

    ads = response.get("ads") or []
    ota_ads = [
        {
            "domain": extract_domain(a.get("link", "")),
            "position": a.get("position"),
            "title": a.get("title", ""),
        }
        for a in ads
        if is_ota(a.get("link", ""), ota_domains)
    ]

    hotel_results = _extract_hotel_pack(response)
    hotel_pack_present = 1 if hotel_results else 0
    ksh_in_hotel_pack = 1 if any(
        "kauai shores" in (h.get("name", "") or "").lower()
        for h in hotel_results
    ) else 0

    organic = response.get("organic_results") or []
    ksh_pos: int | None = None
    for r in organic:
        if is_ksh(r.get("link", "")):
            ksh_pos = r.get("position")
            break
    top_3 = [extract_domain(r.get("link", "")) for r in organic[:3]]

    screenshot = (
        response.get("serpapi_pagination", {}).get("serpapi_screenshot")
        or response.get("search_metadata", {}).get("google_url")
        or ""
    )

    return {
        "run_date": run_date,
        "query": query,
        "query_type": query_type,
        "device": device,
        "aio_present": aio_present,
        "aio_sources": aio_sources,
        "ksh_cited_in_aio": ksh_cited,
        "ads_count": len(ads),
        "ota_ads": ota_ads,
        "hotel_pack_present": hotel_pack_present,
        "ksh_in_hotel_pack": ksh_in_hotel_pack,
        "ksh_organic_pos": ksh_pos,
        "top_3_organic_domains": top_3,
        "screenshot_url": screenshot,
    }


def _extract_aio_sources(aio: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, Any]] = list(aio.get("references") or [])
    if not refs:
        for block in aio.get("text_blocks", []) or []:
            for ref in block.get("references", []) or []:
                refs.append(ref)
    sources: list[dict[str, str]] = []
    for r in refs:
        url = r.get("link") or r.get("url", "")
        sources.append({
            "url": url,
            "domain": extract_domain(url),
            "title": r.get("title", ""),
        })
    return sources


def _extract_hotel_pack(response: dict[str, Any]) -> list[dict[str, Any]]:
    inline = response.get("inline_hotels") or {}
    if isinstance(inline, dict) and inline.get("hotels"):
        return inline["hotels"]
    hr = response.get("hotels_results") or {}
    if isinstance(hr, dict) and hr.get("properties"):
        return hr["properties"]
    lr = response.get("local_results") or {}
    if isinstance(lr, dict) and lr.get("places"):
        return lr["places"]
    return []
