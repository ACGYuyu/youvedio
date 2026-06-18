"""Tests for SourceManager — parser discovery and management."""

from unittest.mock import MagicMock, patch

from youvedio.models import TorrentResult
from youvedio.sources.manager import SourceManager


@patch("youvedio.sources.manager._SOURCES_FILE")
@patch("youvedio.sources.manager._load_parsers")
def test_manager_loads_parsers(mock_load, mock_cfg):
    p = MagicMock()
    p.name = "test_site"
    p.enabled = True
    mock_load.return_value = {"test_site": p}
    mock_cfg.exists.return_value = False
    mgr = SourceManager()
    assert "test_site" in mgr.all_parsers


@patch("youvedio.sources.manager._SOURCES_FILE")
@patch("youvedio.sources.manager._load_parsers")
def test_enabled_parsers_respects_config(mock_load, mock_cfg):
    a, b = MagicMock(), MagicMock()
    a.name, a.enabled = "site_a", True
    b.name, b.enabled = "site_b", True
    mock_load.return_value = {"site_a": a, "site_b": b}
    import json

    mock_cfg.exists.return_value = True
    mock_cfg.read_text.return_value = json.dumps(
        [
            {"name": "site_a", "enabled": True},
            {"name": "site_b", "enabled": False},
        ]
    )
    mgr = SourceManager()
    assert "site_a" in mgr.enabled_parsers
    assert "site_b" not in mgr.enabled_parsers


@patch("youvedio.sources.manager._SOURCES_FILE")
@patch("youvedio.sources.manager._load_parsers")
def test_search_site_unknown(mock_load, mock_cfg):
    mock_load.return_value = {}
    mock_cfg.exists.return_value = False
    mgr = SourceManager()
    assert mgr.search_site("nope", "kw") == []


@patch("youvedio.sources.manager._SOURCES_FILE")
@patch("youvedio.sources.manager._load_parsers")
def test_search_site_disabled(mock_load, mock_cfg):
    p = MagicMock()
    p.name, p.enabled = "s", True
    mock_load.return_value = {"s": p}
    import json

    mock_cfg.exists.return_value = True
    mock_cfg.read_text.return_value = json.dumps([{"name": "s", "enabled": False}])
    mgr = SourceManager()
    assert mgr.search_site("s", "kw") == []


@patch("youvedio.sources.manager._SOURCES_FILE")
@patch("youvedio.sources.manager._load_parsers")
def test_get_parser_missing(mock_load, mock_cfg):
    mock_load.return_value = {}
    mock_cfg.exists.return_value = False
    mgr = SourceManager()
    assert mgr.get_parser("x") is None


@patch("youvedio.sources.manager._SOURCES_FILE")
@patch("youvedio.sources.manager._load_parsers")
def test_search_all_sorts_by_seeders(mock_load, mock_cfg):
    a, b = MagicMock(), MagicMock()
    a.name, a.enabled = "a", True
    a.fetch.return_value = [TorrentResult.create(source="a", title="R2", magnet="", seeders=5)]
    b.name, b.enabled = "b", True
    b.fetch.return_value = [TorrentResult.create(source="b", title="R1", magnet="", seeders=10)]
    mock_load.return_value = {"a": a, "b": b}
    mock_cfg.exists.return_value = False
    mgr = SourceManager()
    results = mgr.search_all("kw")
    assert len(results) == 2
    assert results[0].seeders == 10


@patch("youvedio.sources.manager._SOURCES_FILE")
@patch("youvedio.sources.manager._load_parsers")
def test_search_all_limits_results(mock_load, mock_cfg):
    a = MagicMock()
    a.name, a.enabled = "a", True
    a.fetch.return_value = [
        TorrentResult.create(source="a", title=f"R{i}", magnet="", seeders=i) for i in range(10)
    ]
    mock_load.return_value = {"a": a}
    mock_cfg.exists.return_value = False
    mgr = SourceManager()
    results = mgr.search_all("kw", limit=3)
    assert len(results) == 3


@patch("youvedio.sources.manager._SOURCES_FILE")
@patch("youvedio.sources.manager._load_parsers")
def test_singleton(mock_load, mock_cfg):
    mock_load.return_value = {}
    mock_cfg.exists.return_value = False
    import youvedio.sources.manager as mod
    from youvedio.sources.manager import get_source_manager

    mod._instance = None
    m1 = get_source_manager()
    m2 = get_source_manager()
    assert m1 is m2
