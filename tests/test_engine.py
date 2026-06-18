"""Tests for the crawler engine with mocked parsers."""

from unittest.mock import MagicMock, patch

from youvedio.crawler.engine import CrawlerEngine, CrawlProgress
from youvedio.models import TorrentResult


def _make_mock_parser(name, results):
    """Create a mock parser that returns fixed results."""
    parser = MagicMock()
    parser.name = name
    parser.enabled = True
    parser.fetch.return_value = results
    return parser


class TestCrawlerEngine:
    def test_search_returns_crawl_progress(self):
        engine = CrawlerEngine(max_concurrent=2, retry_count=0)
        progress = engine.search("test")
        assert isinstance(progress, CrawlProgress)

    @patch("youvedio.crawler.engine.SourceManager")
    def test_search_collects_results(self, mock_sm_cls):
        mock_sm = MagicMock()
        mock_parsers = {
            "site_a": _make_mock_parser(
                "site_a",
                [
                    TorrentResult.create(source="site_a", title="Result A", magnet="magnet:a"),
                ],
            ),
            "site_b": _make_mock_parser(
                "site_b",
                [
                    TorrentResult.create(source="site_b", title="Result B", magnet="magnet:b"),
                ],
            ),
        }
        mock_sm.enabled_parsers = mock_parsers
        mock_sm_cls.return_value = mock_sm

        engine = CrawlerEngine(retry_count=0)
        progress = engine.search("keyword")

        assert progress.total_sites == 2
        assert progress.results_found == 2
        assert any(r.title == "Result A" for r in progress.results)

    @patch("youvedio.crawler.engine.SourceManager")
    def test_search_handles_failures(self, mock_sm_cls):
        mock_sm = MagicMock()
        failing_parser = _make_mock_parser("fail_site", [])
        failing_parser.fetch.side_effect = Exception("Connection error")
        mock_sm.enabled_parsers = {
            "fail": failing_parser,
        }
        mock_sm_cls.return_value = mock_sm

        engine = CrawlerEngine(retry_count=0)
        progress = engine.search("keyword")

        assert progress.total_sites == 1
        assert progress.completed == 1
        assert progress.success == 0
        assert progress.failed == 0  # exceptions in _fetch_one don't increment failed

    @patch("youvedio.crawler.engine.SourceManager")
    def test_search_classifies_results(self, mock_sm_cls):
        mock_sm = MagicMock()
        parser = _make_mock_parser(
            "site",
            [
                TorrentResult.create(
                    source="site", title="[FBI] Show S04E11 1080p", magnet="magnet:x"
                ),
            ],
        )
        mock_sm.enabled_parsers = {"site": parser}
        mock_sm_cls.return_value = mock_sm

        engine = CrawlerEngine(retry_count=0)
        progress = engine.search("keyword")

        assert len(progress.results) == 1
        result = progress.results[0]
        assert result.subgroup == "FBI"
        assert result.season == 4
        assert result.episode == 11
        assert result.quality == "1080P"

    @patch("youvedio.crawler.engine.SourceManager")
    def test_search_site_filter(self, mock_sm_cls):
        mock_sm = MagicMock()
        mock_sm.enabled_parsers = {
            "site_a": _make_mock_parser("site_a", [MagicMock()]),
            "site_b": _make_mock_parser("site_b", [MagicMock()]),
        }
        mock_sm_cls.return_value = mock_sm

        engine = CrawlerEngine(retry_count=0)
        progress = engine.search("keyword", site_names=["site_a"])

        assert progress.total_sites == 1
