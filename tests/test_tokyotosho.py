"""Tests for TokyoTosho parser with mock RSS XML."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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

    def test_search_url(self) -> None:
        p = TokyoToshoParser()
        assert "rss.php" in p.search_url("Frieren")
        assert "Frieren" in p.search_url("Frieren")

    def test_parse_whitespace_title(self) -> None:
        rss = '<rss version="2.0"><channel>'
        rss += "<item><title>   </title><description>x</description></item>"
        rss += "<item><title>Real Title</title><description>y</description></item>"
        rss += "</channel></rss>"
        p = TokyoToshoParser()
        results = p.parse(rss)
        assert len(results) == 1
        assert results[0].title == "Real Title"

    @patch("curl_cffi.requests.Session")
    def test_fetch_curl_cffi_success(self, mock_session_cls) -> None:
        mock_sess = MagicMock()
        mock_session_cls.return_value = mock_sess
        mock_sess.__enter__.return_value = mock_sess
        mock_sess.get.return_value = MagicMock(status_code=200, text=_RSS)

        p = TokyoToshoParser()
        results = p.fetch("test")
        assert len(results) == 1
        assert "[FBI] Show S01 1080p" in results[0].title

    @patch("httpx.Client")
    @patch("curl_cffi.requests.Session")
    def test_fetch_httpx_fallback(self, mock_session_cls, mock_httpx) -> None:
        mock_session_cls.side_effect = Exception("curl fail")

        mock_client = MagicMock()
        mock_httpx.return_value = mock_client
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = MagicMock(status_code=200, text=_RSS)

        p = TokyoToshoParser()
        results = p.fetch("test")
        assert len(results) == 1
        assert "[FBI] Show S01 1080p" in results[0].title
