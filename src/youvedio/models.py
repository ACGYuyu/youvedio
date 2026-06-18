"""Data models for torrent/magnet search results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TorrentResult:
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
    crawled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SearchResult:
    """Grouped search results for a query."""

    keyword: str
    searched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    seasons: dict[str, dict[str, list[TorrentResult]]] = field(default_factory=dict)
    unclassified: list[TorrentResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        count = len(self.unclassified)
        for season_group in self.seasons.values():
            for results in season_group.values():
                count += len(results)
        return count

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "searched_at": self.searched_at.isoformat(),
            "total": self.total,
            "seasons": self.seasons,
            "unclassified": self.unclassified,
        }
