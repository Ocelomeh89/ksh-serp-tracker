import pytest

from ksh_serp.db import init_db, insert_row, fetch_latest_run_date, fetch_all_rows


@pytest.fixture
def tmp_db(tmp_path):
    p = tmp_path / "test.db"
    init_db(p)
    return p


def sample_row(**overrides):
    row = {
        "run_date": "2026-05-20",
        "query": "kauai shores hotel",
        "query_type": "brand",
        "device": "desktop",
        "aio_present": 1,
        "aio_sources": [{"domain": "tripadvisor.com", "url": "x", "title": "y"}],
        "ksh_cited_in_aio": 0,
        "ads_count": 3,
        "ota_ads": [{"domain": "booking.com", "position": 1, "title": "Z"}],
        "hotel_pack_present": 1,
        "ksh_in_hotel_pack": 1,
        "ksh_organic_pos": 4,
        "top_3_organic_domains": ["booking.com", "expedia.com", "kauaishoreshotel.com"],
        "screenshot_url": "https://x",
    }
    row.update(overrides)
    return row


def test_init_creates_runs_table(tmp_db):
    assert fetch_all_rows(tmp_db) == []


def test_insert_and_fetch_roundtrip(tmp_db):
    insert_row(tmp_db, sample_row())
    rows = fetch_all_rows(tmp_db)
    assert len(rows) == 1
    assert rows[0]["query"] == "kauai shores hotel"
    assert isinstance(rows[0]["aio_sources"], list)
    assert rows[0]["aio_sources"][0]["domain"] == "tripadvisor.com"


def test_fetch_latest_run_date(tmp_db):
    insert_row(tmp_db, sample_row(run_date="2026-05-13"))
    insert_row(tmp_db, sample_row(run_date="2026-05-20", device="mobile"))
    assert fetch_latest_run_date(tmp_db) == "2026-05-20"


def test_idempotent_insert_same_key(tmp_db):
    """Re-running same (date, query, device) should replace, not duplicate."""
    insert_row(tmp_db, sample_row(ads_count=3))
    insert_row(tmp_db, sample_row(ads_count=5))
    rows = fetch_all_rows(tmp_db)
    assert len(rows) == 1
    assert rows[0]["ads_count"] == 5


def test_device_distinct_keys(tmp_db):
    insert_row(tmp_db, sample_row(device="desktop"))
    insert_row(tmp_db, sample_row(device="mobile"))
    rows = fetch_all_rows(tmp_db)
    assert len(rows) == 2


def test_null_ksh_organic_pos(tmp_db):
    insert_row(tmp_db, sample_row(ksh_organic_pos=None))
    rows = fetch_all_rows(tmp_db)
    assert rows[0]["ksh_organic_pos"] is None
