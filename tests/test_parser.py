import json
from pathlib import Path

import pytest

from ksh_serp.parser import parse_serpapi_response

FIXTURES = Path(__file__).parent / "fixtures"
OTA_DOMAINS = frozenset({"booking.com", "expedia.com", "hotels.com", "guestreservations.com"})


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def parse(fixture: str, query: str, query_type: str, device: str = "desktop") -> dict:
    return parse_serpapi_response(
        response=load(fixture),
        query=query,
        query_type=query_type,
        device=device,
        run_date="2026-05-20",
        ota_domains=OTA_DOMAINS,
    )


class TestBrandAioDesktop:
    @pytest.fixture
    def parsed(self):
        return parse("brand_aio_desktop", "kauai shores hotel", "brand")

    def test_required_keys(self, parsed):
        required = {
            "run_date", "query", "query_type", "device",
            "aio_present", "aio_sources", "ksh_cited_in_aio",
            "ads_count", "ota_ads", "hotel_pack_present",
            "ksh_in_hotel_pack", "ksh_organic_pos",
            "top_3_organic_domains", "screenshot_url",
        }
        assert required.issubset(parsed.keys())

    def test_aio_detected(self, parsed):
        assert parsed["aio_present"] == 1

    def test_aio_sources_extracted(self, parsed):
        domains = {s["domain"] for s in parsed["aio_sources"]}
        assert "kauaishoreshotel.com" in domains
        assert "tripadvisor.com" in domains

    def test_ksh_cited_in_aio(self, parsed):
        assert parsed["ksh_cited_in_aio"] == 1

    def test_ads_count(self, parsed):
        assert parsed["ads_count"] == 4

    def test_ota_ads_filtered(self, parsed):
        domains = {a["domain"] for a in parsed["ota_ads"]}
        assert domains == {"booking.com", "expedia.com", "hotels.com"}

    def test_hotel_pack_present(self, parsed):
        assert parsed["hotel_pack_present"] == 1

    def test_ksh_in_hotel_pack(self, parsed):
        assert parsed["ksh_in_hotel_pack"] == 1

    def test_ksh_organic_pos(self, parsed):
        assert parsed["ksh_organic_pos"] == 1

    def test_top_3_organic(self, parsed):
        assert parsed["top_3_organic_domains"] == [
            "kauaishoreshotel.com", "booking.com", "tripadvisor.com",
        ]

    def test_screenshot(self, parsed):
        assert "screenshot" in parsed["screenshot_url"]


class TestBrandAioMobile:
    @pytest.fixture
    def parsed(self):
        return parse("brand_aio_mobile", "kauai shores hotel", "brand", "mobile")

    def test_device_recorded(self, parsed):
        assert parsed["device"] == "mobile"

    def test_ksh_not_cited_when_absent_from_refs(self, parsed):
        assert parsed["ksh_cited_in_aio"] == 0

    def test_ksh_organic_pos_2(self, parsed):
        assert parsed["ksh_organic_pos"] == 2


class TestNonbrandAioDesktop:
    @pytest.fixture
    def parsed(self):
        return parse("nonbrand_aio_desktop", "best kauai hotel dining", "nonbrand")

    def test_query_type(self, parsed):
        assert parsed["query_type"] == "nonbrand"

    def test_no_ads(self, parsed):
        assert parsed["ads_count"] == 0
        assert parsed["ota_ads"] == []

    def test_ksh_not_in_organic(self, parsed):
        assert parsed["ksh_organic_pos"] is None

    def test_no_hotel_pack(self, parsed):
        assert parsed["hotel_pack_present"] == 0


class TestNonbrandHotelPack:
    @pytest.fixture
    def parsed(self):
        return parse("nonbrand_hotelpack_desktop", "kauai oceanfront hotel", "nonbrand")

    def test_no_aio(self, parsed):
        assert parsed["aio_present"] == 0

    def test_hotel_pack(self, parsed):
        assert parsed["hotel_pack_present"] == 1

    def test_ksh_in_hotel_pack(self, parsed):
        assert parsed["ksh_in_hotel_pack"] == 1
