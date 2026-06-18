"""Tests for AniDEX parser with mock HTML."""

from youvedio.sources.sites.anidex import AnidexParser

_HTML = """<table><tbody>
<tr>
<td>cat</td>
<td>lang</td>
<td><a href="/torrent/123">[FBI] Show S01 1080p</a></td>
<td>group</td>
<td>1.4 GiB</td>
<td class="text-center">100</td>
<td class="text-center">10</td>
</tr>
</tbody></table>"""


class TestAnidexParser:
    def test_parse_title(self):
        p = AnidexParser()
        results = p.parse(_HTML)
        assert len(results) == 1
        assert "[FBI] Show S01 1080p" in results[0].title

    def test_parse_empty(self):
        p = AnidexParser()
        assert p.parse("") == []
