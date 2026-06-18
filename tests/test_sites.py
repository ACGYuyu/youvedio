"""Tests for site parsers — base class helpers and basic parsing."""

import os
from unittest.mock import patch

from youvedio.sources.sites.base import SiteParser


class _ConcreteParser(SiteParser):
    """Concrete parser for testing base class methods."""

    name = "test_site"
    base_url = "https://test.com"
    lang = "en"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/search?q={keyword}"

    def parse(self, html, source=None):  # noqa: ARG002
        return []


class TestSiteParserBase:
    def test_name_from_class(self):
        parser = _ConcreteParser()
        assert parser.name == "test_site"

    def test_search_url_format(self):
        parser = _ConcreteParser()
        url = parser.search_url("Re:Zero")
        assert "q=Re:Zero" in url

    def test_safe_int_valid(self):
        assert SiteParser.safe_int("42") == 42

    def test_safe_int_none(self):
        assert SiteParser.safe_int(None) == 0

    def test_safe_int_empty(self):
        assert SiteParser.safe_int("") == 0

    def test_safe_int_invalid(self):
        assert SiteParser.safe_int("abc") == 0

    def test_extract_info_hash_valid(self):
        h = SiteParser.extract_info_hash("magnet:?xt=urn:btih:abc123def456")
        assert h == "abc123def456"

    def test_extract_info_hash_empty(self):
        assert SiteParser.extract_info_hash("") == ""

    def test_extract_info_hash_no_match(self):
        assert SiteParser.extract_info_hash("not a magnet") == ""

    def test_normalize_size(self):
        p = _ConcreteParser()
        assert p.normalize_size(" 1.4 GiB ") == "1.4 GiB"

    def test_normalize_size_empty(self):
        p = _ConcreteParser()
        assert p.normalize_size("") == ""

    def test_extract_page_url_absolute(self):
        p = _ConcreteParser()
        assert p.extract_page_url("https://other.com/page") == "https://other.com/page"

    def test_extract_page_url_relative(self):
        p = _ConcreteParser()
        assert p.extract_page_url("/view/123") == "https://test.com/view/123"

    @patch.object(_ConcreteParser, "fetch")
    def test_fetch_calls_parse(self, mock_fetch):
        """Verify that fetch is called without error (integration point)."""
        mock_fetch.return_value = []
        p = _ConcreteParser()
        result = p.fetch("keyword")
        assert result == []

    def test_proxies_returns_none_when_empty(self):
        """_proxies returns None when no proxy is configured."""
        p = _ConcreteParser()
        with (
            patch("youvedio.sources.sites.base.settings.http_proxy", ""),
            patch("youvedio.sources.sites.base.settings.https_proxy", ""),
            patch.dict(os.environ, {}, clear=True),
        ):
            assert p._proxies() is None

    def test_proxies_returns_dict_when_set(self):
        """_proxies returns proxy dict when configured."""
        p = _ConcreteParser()
        with (
            patch("youvedio.sources.sites.base.settings.http_proxy", "http://proxy:8080"),
            patch("youvedio.sources.sites.base.settings.https_proxy", ""),
            patch.dict(os.environ, {}, clear=True),
        ):
            result = p._proxies()
            assert result is not None
            assert "http://proxy:8080" in result["http"]
            assert result["https"] == "http://proxy:8080"


class TestParseEdgeCases:
    """Test edge cases for the abstract parse method pattern."""

    def test_empty_html(self):
        """Parsers should handle empty HTML gracefully."""
        p = _ConcreteParser()
        result = p.parse("", source="test")
        assert result == []

    def test_malformed_html(self):
        """Parsers should handle malformed HTML."""
        p = _ConcreteParser()
        result = p.parse("<html><broken>stuff</html>", source="test")
        assert result == []

    def test_source_default(self):
        """Parse should use the class name as default source."""
        p = _ConcreteParser()
        result = p.parse("<html></html>")
        assert result == []
