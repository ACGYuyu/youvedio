"""Tests for TokyoTosho parser with mock HTML."""

from youvedio.sources.sites.tokyotosho import TokyoToshoParser

_HTML = """<div class="list-topic">
<div class="name"><a href="/view/123">[FBI] Show S01 1080p</a></div>
<div class="files"><a href="magnet:?xt=urn:btih:abc">DL</a></div>
<span class="size">1.4 GiB</span>
</div>"""


class TestTokyoToshoParser:
    def test_parse_title(self):
        p = TokyoToshoParser()
        results = p.parse(_HTML)
        assert len(results) == 1
        assert "[FBI] Show S01 1080p" in results[0].title

    def test_parse_empty(self):
        p = TokyoToshoParser()
        assert p.parse("") == []
