"""Tests for Nyaa.si parser with mock HTML."""

from youvedio.sources.sites.nyaa import NyaaParser


_NYAA_HTML = """<table class="table table-bordered table-hover table-striped torrent-list">
<thead><tr><th>Category</th><th>Name</th><th>Size</th><th>Date</th><th>Seeders</th><th>Leechers</th></tr></thead>
<tbody>
<tr class="success">
<td><a href="/c/1_2">Anime</a></td>
<td><a href="/view/123456">[FBI] Show S04E11 1080p WEB-DL</a></td>
<td><a href="magnet:?xt=urn:btih:abc123def456">Magnet</a></td>
<td class="text-center">1.4 GiB</td>
<td>2026-06-18</td>
<td class="text-center">100</td>
<td class="text-center">10</td>
</tr>
<tr class="success">
<td><a href="/c/1_2">Anime</a></td>
<td><a href="/view/789012">[Erai] Show S04E11 720p HDTV</a></td>
<td><a href="magnet:?xt=urn:btih:789012abcdef">Magnet</a></td>
<td class="text-center">800 MiB</td>
<td>2026-06-18</td>
<td class="text-center">50</td>
<td class="text-center">5</td>
</tr>
</tbody>
</table>"""


class TestNyaaParser:
    def test_parse_returns_results(self):
        parser = NyaaParser()
        results = parser.parse(_NYAA_HTML)
        assert len(results) == 2

    def test_parse_extracts_title(self):
        parser = NyaaParser()
        results = parser.parse(_NYAA_HTML)
        assert "[FBI] Show S04E11 1080p WEB-DL" in results[0].title

    def test_parse_extracts_magnet(self):
        parser = NyaaParser()
        results = parser.parse(_NYAA_HTML)
        assert results[0].magnet.startswith("magnet:")
        assert "btih:abc123def456" in results[0].magnet

    def test_parse_extracts_seeders(self):
        parser = NyaaParser()
        results = parser.parse(_NYAA_HTML)
        assert results[0].seeders == 100
        assert results[1].seeders == 50

    def test_parse_extracts_leechers(self):
        parser = NyaaParser()
        results = parser.parse(_NYAA_HTML)
        assert results[0].leechers == 10

    def test_parse_extracts_size(self):
        parser = NyaaParser()
        results = parser.parse(_NYAA_HTML)
        assert results[0].size == "1.4 GiB"

    def test_parse_extracts_info_hash(self):
        parser = NyaaParser()
        results = parser.parse(_NYAA_HTML)
        assert results[0].info_hash == "abc123def456"

    def test_parse_extracts_page_url(self):
        parser = NyaaParser()
        results = parser.parse(_NYAA_HTML)
        assert "nyaa.si/view/123456" in results[0].page_url

    def test_parse_empty_html(self):
        parser = NyaaParser()
        assert parser.parse("") == []

    def test_parse_no_rows(self):
        parser = NyaaParser()
        html = "<table><tbody></tbody></table>"
        assert parser.parse(html) == []

    def test_parse_partial_row(self):
        """Parser should skip malformed rows without crashing."""
        parser = NyaaParser()
        html = "<table><tbody><tr><td>broken</td></tr></tbody></table>"
        results = parser.parse(html)
        assert len(results) == 0
