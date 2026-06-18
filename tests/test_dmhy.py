"""Tests for Dmhy (动漫花园) parser with mock HTML."""

from youvedio.sources.sites.dmhy import DmhyParser

_DMHY_HTML = """<table><tbody>
<tr>
<td>cat</td>
<td><a href="/topics/view/123">[FBI] Show S01 1080p</a></td>
<td>type</td>
<td>1.4 GiB</td>
<td class="text-center">100</td>
<td><a href="magnet:?xt=urn:btih:abc123">DL</a></td>
</tr>
</tbody></table>"""


class TestDmhyParser:
    def test_parse_extracts_title(self):
        p = DmhyParser()
        results = p.parse(_DMHY_HTML)
        assert len(results) == 1
        assert "[FBI] Show S01 1080p" in results[0].title

    def test_parse_magnet(self):
        p = DmhyParser()
        results = p.parse(_DMHY_HTML)
        assert "btih:abc123" in results[0].magnet

    def test_parse_seeders(self):
        p = DmhyParser()
        results = p.parse(_DMHY_HTML)
        assert results[0].seeders == 100

    def test_parse_empty(self):
        p = DmhyParser()
        assert p.parse("") == []
