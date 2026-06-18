"""Tests for ACG.RIP parser with mock HTML."""

from youvedio.sources.sites.acgrip import AcgRipParser

_HTML = """<table class="ui table table-hover table-condensed">
<tbody>
<tr>
<td><a href="/team/1">GroupA</a></td>
<td><a href="/t/100">[FBI] Show S01 1080p BDRip</a></td>
<td><a href="magnet:?xt=urn:btih:abc">torrent</a></td>
<td>1.4 GiB</td>
</tr>
</tbody>
</table>"""


class TestAcgRipParser:
    def test_parse_title(self):
        p = AcgRipParser()
        results = p.parse(_HTML)
        assert len(results) == 1
        assert "[FBI] Show S01 1080p BDRip" in results[0].title

    def test_parse_magnet(self):
        p = AcgRipParser()
        results = p.parse(_HTML)
        assert "btih:abc" in results[0].magnet

    def test_parse_empty(self):
        p = AcgRipParser()
        assert p.parse("") == []
