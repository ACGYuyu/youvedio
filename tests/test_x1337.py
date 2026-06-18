"""Tests for 1337x parser with mock HTML."""

from youvedio.sources.sites.x1337 import X1337Parser

_HTML = """<table class="table-list"><tbody>
<tr>
<td class="coll-1"><a href="/torrent/123">[FBI] Show S01 1080p</a></td>
<td class="coll-2">100</td>
<td class="coll-3">10</td>
<td class="coll-4">1.4 GiB</td>
</tr>
</tbody></table>"""


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

    def test_parse_size(self):
        p = X1337Parser()
        results = p.parse(_HTML)
        assert results[0].size == "1.4 GiB"

    def test_parse_empty(self):
        p = X1337Parser()
        assert p.parse("") == []
