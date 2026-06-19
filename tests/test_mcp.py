"""Tests for MCP server — tool definitions and core logic."""

from unittest.mock import MagicMock, patch

from youvedio.mcp_server import _build_quality_summary, _seasons_to_json, _to_dict
from youvedio.models import TorrentResult


class TestHelpers:
    def test_to_dict_includes_all_fields(self):
        r = TorrentResult.create(
            source="nyaa.si",
            title="[FBI] Show S01 1080p",
            magnet="magnet:?xt=urn:btih:abc",
            seeders=100,
            leechers=10,
            season=1,
            episode=5,
            quality="1080P",
            source_type="WEB-DL",
            subgroup="FBI",
            page_url="https://nyaa.si/view/123",
        )
        d = _to_dict(r)
        assert d["source"] == "nyaa.si"
        assert d["seeders"] == 100
        assert d["quality"] == "1080P"
        assert d["subgroup"] == "FBI"

    def test_to_dict_defaults_empty_strings(self):
        r = TorrentResult.create(source="test", title="Test", magnet="")
        d = _to_dict(r)
        assert d["info_hash"] == ""
        assert d["size"] == ""
        assert d["quality"] == ""
        assert d["subgroup"] == ""

    def test_seasons_to_json(self):
        r = TorrentResult.create(source="test", title="[A] Show S01 1080p", magnet="")
        seasons = {"S01": {"1080P": [r]}}
        result = _seasons_to_json(seasons)
        assert "S01" in result
        assert "1080P" in result["S01"]
        assert len(result["S01"]["1080P"]) == 1

    def test_quality_summary(self):
        r1 = TorrentResult.create(
            source="test",
            title="[A] Show S01 1080p",
            magnet="",
            season=1,
            subgroup="A",
        )
        r2 = TorrentResult.create(
            source="test",
            title="[B] Show S01 1080p",
            magnet="",
            season=1,
            subgroup="B",
            episode=1,
        )
        seasons_dict = {"S01": {"1080P": [_to_dict(r1), _to_dict(r2)]}}
        summary = _build_quality_summary(seasons_dict)
        assert "S01" in summary
        assert "1080P" in summary["S01"]
        assert summary["S01"]["1080P"]["total"] == 2
        assert "A" in summary["S01"]["1080P"]["subgroups"]
        assert "B" in summary["S01"]["1080P"]["subgroups"]

    def test_quality_summary_includes_unclassified(self):
        seasons_dict = {"_unclassified": {"All": [{"title": "x", "quality": "1080P"}]}}
        summary = _build_quality_summary(seasons_dict)
        assert "_unclassified" in summary
        assert summary["_unclassified"]["1080P"]["total"] == 1


def _mock_search(mock_get, mock_engine_cls, cache_value=None, results=None):
    """Helper to set up mocks for search_torrents tests."""
    mock_get.return_value = cache_value
    mock_get.return_value = cache_value
    mock_progress = MagicMock()
    mock_progress.results = results or []
    mock_progress.success = len(results) if results else 0
    mock_progress.failed = 0
    mock_engine = MagicMock()
    mock_engine.search.return_value = mock_progress
    mock_engine_cls.return_value = mock_engine


@patch("youvedio.mcp_server.CrawlerEngine")
@patch("youvedio.mcp_server.cache_get")
@patch("youvedio.mcp_server.cache_set")
def test_search_torrents_calls_engine(_mock_set, mock_get, mock_engine_cls):
    _mock_search(mock_get, mock_engine_cls)
    from youvedio.mcp_server import search_torrents

    result = search_torrents("test")
    assert result["keyword"] == "test"
    assert "seasons" in result
    assert "quality_summary" in result


@patch("youvedio.mcp_server.CrawlerEngine")
@patch("youvedio.mcp_server.cache_get")
@patch("youvedio.mcp_server.cache_set")
def test_search_torrents_uses_cache(_mock_set, mock_get, mock_engine_cls):
    cached = {"keyword": "cached", "total": 0, "seasons": {}, "quality_summary": {}}
    _mock_search(mock_get, mock_engine_cls, cache_value=cached)
    from youvedio.mcp_server import search_torrents

    result = search_torrents("test")
    assert result["keyword"] == "cached"
    mock_engine_cls.assert_not_called()


@patch("youvedio.mcp_server.CrawlerEngine")
@patch("youvedio.mcp_server.cache_get")
@patch("youvedio.mcp_server.cache_set")
def test_search_torrents_includes_quality_summary(_mock_set, mock_get, mock_engine_cls):
    r = TorrentResult.create(
        source="nyaa",
        title="[FBI] Show S04E11 1080p",
        magnet="m:",
        seeders=50,
        season=4,
        episode=11,
        quality="1080P",
        subgroup="FBI",
    )
    _mock_search(mock_get, mock_engine_cls, results=[r])
    from youvedio.mcp_server import search_torrents

    result = search_torrents("Show")
    assert result["total"] == 1
    assert "S04" in result["quality_summary"]
    assert result["quality_summary"]["S04"]["1080P"]["total"] == 1
