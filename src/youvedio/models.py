"""Data models for torrent/magnet search results."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TorrentResult(BaseModel):
    """Single torrent/magnet result."""

    source: str
    title: str
    magnet: str
    info_hash: str | None = None
    size: str | None = None
    seeders: int | None = None
    leechers: int | None = None
    season: int | None = None
    episode: int | None = None
    quality: str | None = None
    source_type: str | None = None
    page_url: str | None = None
    crawled_at: datetime | None = None

    @staticmethod
    def create(
        source: str,
        title: str,
        magnet: str = "",
        info_hash: str | None = None,
        size: str | None = None,
        seeders: int | None = None,
        leechers: int | None = None,
        season: int | None = None,
        episode: int | None = None,
        quality: str | None = None,
        source_type: str | None = None,
        page_url: str | None = None,
    ) -> TorrentResult:
        return TorrentResult(
            source=source,
            title=title,
            magnet=magnet,
            info_hash=info_hash,
            size=size,
            seeders=seeders,
            leechers=leechers,
            season=season,
            episode=episode,
            quality=quality,
            source_type=source_type,
            page_url=page_url,
        )


class SearchResult(BaseModel):
    """Grouped search results for a query."""

    keyword: str
    searched_at: datetime = Field(default_factory=datetime.utcnow)
    seasons: dict[str, dict[str, list[TorrentResult]]] = Field(default_factory=dict)
    unclassified: list[TorrentResult] = Field(default_factory=list)


class ClassifiedResult(BaseModel):
    """Output schema for JSON export."""

    keyword: str
    searched_at: str
    total: int
    seasons: dict[str, dict[str, list[TorrentResult]]]
    unclassified: list[TorrentResult]
