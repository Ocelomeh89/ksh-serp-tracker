from ksh_serp.classifier import extract_domain, is_ksh, is_ota


class TestExtractDomain:
    def test_strips_protocol_and_path(self):
        assert extract_domain("https://www.booking.com/hotel/us/kauai") == "booking.com"

    def test_lowercases(self):
        assert extract_domain("https://Booking.COM/x") == "booking.com"

    def test_handles_subdomain_www(self):
        assert extract_domain("https://www.kauaishoreshotel.com/") == "kauaishoreshotel.com"

    def test_handles_non_www_subdomain(self):
        assert extract_domain("https://m.booking.com/x") == "booking.com"

    def test_returns_empty_for_invalid(self):
        assert extract_domain("") == ""
        assert extract_domain("not a url") == ""


class TestIsKsh:
    def test_main_domain(self):
        assert is_ksh("https://kauaishoreshotel.com/rooms") is True

    def test_redirect_domain(self):
        assert is_ksh("https://kauaishores.com/") is True

    def test_other_domain(self):
        assert is_ksh("https://booking.com/hotel/us/kauai-shores") is False


class TestIsOta:
    def test_booking(self):
        otas = frozenset({"booking.com", "expedia.com"})
        assert is_ota("https://www.booking.com/x", otas) is True

    def test_unknown_domain(self):
        otas = frozenset({"booking.com"})
        assert is_ota("https://example.com/x", otas) is False

    def test_subdomain_of_ota(self):
        otas = frozenset({"booking.com"})
        assert is_ota("https://secure.booking.com/x", otas) is True
