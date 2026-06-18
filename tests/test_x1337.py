"""Tests for 1337x parser with mock HTML."""

from unittest.mock import patch

from youvedio.sources.sites.x1337 import X1337Parser

_HTML = """<table class="table-list"><tbody>
<tr>
<td class="coll-1"><a href="/torrent/123">[FBI] Show S01 1080p</a></td>
<td class="coll-2">100</td>
<td class="coll-3">10</td>
<td class="coll-4">1.4 GiB</td>
</tr>
</tbody></table>"""

_DETAIL_HTML = """<html><body>
<div class="torrent-detail">
<h1>[FBI] Show S01 1080p</h1>
<ul class="list">
<li><strong>Magnet Link:</strong> <a href="magnet:?xt=urn:btih:abc123def456">Magnet</a></li>
</ul>
</div>
</body></html>"""


class TestX1337Parser:
    def test_parse_title(self):
        p = X1337Parser()
        results = p.parse(_HTML)
        assert len(results) == 1
        assert "Show S01" in results[0].title

    def test_parse_seeders(self):
        p = X1337Parser()
        results = p.parse(_HTML)
        assert results[0].seeders == 100

    def test_parse_leechers(self):
        p = X1337Parser()
        results = p.parse(_HTML)
        assert results[0].leechers == 10

    def test_parse_size(self):
        p = X1337Parser()
        results = p.parse(_HTML)
        assert results[0].size == "1.4 GiB"

    def test_parse_detail_page_magnet(self):
        p = X1337Parser()
        magnet = p.parse_detail_page(_DETAIL_HTML)
        assert magnet == "magnet:?xt=urn:btih:abc123def456"

    def test_parse_detail_page_empty(self):
        p = X1337Parser()
        assert p.parse_detail_page("") == ""

    def test_parse_empty(self):
        p = X1337Parser()
        assert p.parse("") == []

    def test_search_url(self):
        p = X1337Parser()
        url = p.search_url("Frieren")
        assert "1337x.to" in url
        assert "/search/Frieren/1/" in url

    def test_fetch_fallback_to_parent(self):
        """Verify fallback to parent fetch when StealthyFetcher is unavailable."""
        with patch("youvedio.sources.sites.base.SiteParser.fetch", return_value=[]):
            p = X1337Parser()
            results = p.fetch("test")
            assert results == []
