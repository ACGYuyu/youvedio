"""Tests for Mikanani parser with mock HTML."""

from youvedio.sources.sites.mikan import MikanParser

_HTML = """<table><tbody>
<tr class="js-search-results-row">
<td><input type="checkbox" class="js-episode-select" data-magnet="magnet:?xt=urn:btih:abc123"></td>
<td><a href="/Home/Episode/abc">[SubGroup] Show S01 1080p HEVC</a></td>
<td>1.4 GiB</td>
<td>2026-01-01</td>
</tr>
</tbody></table>"""


class TestMikanParser:
    def test_parse_title(self):
        p = MikanParser()
        results = p.parse(_HTML)
        assert len(results) == 1
        assert "[SubGroup] Show S01 1080p HEVC" in results[0].title

    def test_parse_magnet(self):
        p = MikanParser()
        results = p.parse(_HTML)
        assert "btih:abc123" in results[0].magnet

    def test_parse_empty(self):
        p = MikanParser()
        assert p.parse("") == []
