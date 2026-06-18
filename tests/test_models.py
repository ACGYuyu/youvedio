"""Tests for Pydantic data models."""

from datetime import datetime, timezone

from youvedio.models import TorrentResult


class TestTorrentResult:
    def test_create_with_required_only(self):
        r = TorrentResult.create(source="nyaa.si", title="Test", magnet="magnet:?xt=urn:btih:abc")
        assert r.source == "nyaa.si"
        assert r.title == "Test"
        assert r.magnet == "magnet:?xt=urn:btih:abc"
        assert r.info_hash is None
        assert r.size is None
        assert r.seeders is None
        assert r.leechers is None
        assert r.season is None
        assert r.episode is None
        assert r.quality is None
        assert r.source_type is None
        assert r.subgroup is None
        assert r.page_url is None
        assert r.crawled_at is None

    def test_create_with_all_fields(self):
        r = TorrentResult.create(
            source="nyaa.si",
            title="[FBI] Show S01 1080p",
            magnet="magnet:?xt=urn:btih:abc",
            info_hash="abc123",
            size="1.4 GiB",
            seeders=100,
            leechers=10,
            season=1,
            episode=5,
            quality="1080P",
            source_type="WEB-DL",
            subgroup="FBI",
            page_url="https://nyaa.si/view/123",
        )
        assert r.info_hash == "abc123"
        assert r.size == "1.4 GiB"
        assert r.seeders == 100
        assert r.leechers == 10
        assert r.season == 1
        assert r.episode == 5
        assert r.quality == "1080P"
        assert r.source_type == "WEB-DL"
        assert r.subgroup == "FBI"

    def test_pydantic_serialization(self):
        r = TorrentResult.create(
            source="nyaa.si",
            title="Test",
            magnet="magnet:?xt=urn:btih:abc",
            seeders=50,
            quality="1080P",
        )
        d = r.model_dump()
        assert d["source"] == "nyaa.si"
        assert d["seeders"] == 50
        assert d["quality"] == "1080P"
        assert d["leechers"] is None
        assert d["season"] is None

    def test_pydantic_json_roundtrip(self):
        r1 = TorrentResult.create(
            source="nyaa.si",
            title="[FBI] Show S01 1080p",
            magnet="magnet:?xt=urn:btih:abc",
            seeders=100,
            season=1,
            quality="1080P",
        )
        json_str = r1.model_dump_json()
        r2 = TorrentResult.model_validate_json(json_str)
        assert r2.source == r1.source
        assert r2.title == r1.title
        assert r2.seeders == r1.seeders
        assert r2.season == r1.season
        assert r2.quality == r1.quality
