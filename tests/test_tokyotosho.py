"""Tests for TokyoTosho parser with mock RSS XML."""

from __future__ import annotations

from youvedio.sources.sites.tokyotosho import TokyoToshoParser

_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Search - Tokyo Toshokan</title>
<link>https://www.tokyotosho.info</link>
<description>Torrent Listing</description>
<language>en</language>
<item>
<category>Batch</category>
<title>[FBI] Show S01 1080p</title>
<link>https://nyaa.si/view/123/torrent</link>
<description><![CDATA[<a href="https://nyaa.si/view/123/torrent">Torrent Link</a><br />
<a href="magnet:?xt=urn:btih:abc">Magnet Link</a><br />
<a href="https://www.tokyotosho.info/details.php?id=123">Tokyo Tosho</a><br />
Size: 1.4 GiB<br />
Authorized: Yes<br />
Submitter: test]]></description>
<guid>https://www.tokyotosho.info/details.php?id=123</guid>
<pubDate>Fri, 19 Jun 2026 12:00:00 GMT</pubDate>
</item>
</channel>
</rss>"""


class TestTokyoToshoParser:
    def test_parse_title(self) -> None:
        p = TokyoToshoParser()
        results = p.parse(_RSS)
        assert len(results) == 1
        assert "[FBI] Show S01 1080p" in results[0].title

    def test_parse_magnet(self) -> None:
        p = TokyoToshoParser()
        results = p.parse(_RSS)
        assert "btih:abc" in results[0].magnet

    def test_parse_seeders_default(self) -> None:
        """RSS has no seeder/leecher data — defaults to 0."""
        p = TokyoToshoParser()
        results = p.parse(_RSS)
        assert results[0].seeders == 0

    def test_parse_leechers_default(self) -> None:
        p = TokyoToshoParser()
        results = p.parse(_RSS)
        assert results[0].leechers == 0

    def test_parse_size(self) -> None:
        p = TokyoToshoParser()
        results = p.parse(_RSS)
        assert results[0].size == "1.4 GiB"

    def test_parse_page_url(self) -> None:
        p = TokyoToshoParser()
        results = p.parse(_RSS)
        assert "details.php?id=123" in results[0].page_url

    def test_parse_empty(self) -> None:
        p = TokyoToshoParser()
        assert p.parse("") == []

    def test_parse_no_results(self) -> None:
        p = TokyoToshoParser()
        doc = '<rss version="2.0"><channel><title>No results</title></channel></rss>'
        assert p.parse(doc) == []
