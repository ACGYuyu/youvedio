"""Data models for torrent/magnet search results."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TorrentResult(BaseModel):
    """Single torrent/magnet result."""

    source: str = Field(description="Site name, e.g. nyaa.si")
    title: str = Field(description="Torrent title")
    magnet: str = Field(description="Magnet URI")
    info_hash: Optional[str] = Field(None, description="BitTorrent info hash")
    size: Optional[str] = Field(None, description="Human-readable size")
    seeders: Optional[int] = Field(None)
    leechers: Optional[int] = Field(None)
    season: Optional[int] = Field(None, description="Season number")
    episode: Optional[int] = Field(None, description="Episode number")
    quality: Optional[str] = Field(
        None, description="Resolution: 4K, 1080p, 720p, etc."
    )
    source_type: Optional[str] = Field(
        None, description="Blu-ray, WEBRip, etc."
    )
    page_url: Optional[str] = Field(None, description="Torrent page URL")
    crawled_at: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    """Grouped search results for a query."""

    keyword: str
    searched_at: datetime = Field(default_factory=datetime.utcnow)
    seasons: dict[str, dict[str, list[TorrentResult]]] = Field(
        default_factory=dict,
        description="Structure: {season_label: {quality: [results]}}",
    )
    unclassified: list[TorrentResult] = Field(default_factory=list)


class ClassifiedResult(BaseModel):
    """Output schema for JSON export."""

    keyword: str
    searched_at: str
    total: int
    seasons: dict[str, dict[str, list[TorrentResult]]]
    unclassified: list[TorrentResult]
