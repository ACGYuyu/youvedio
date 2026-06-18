"""Torrent title classifier — extract season, quality, source type, etc."""

from __future__ import annotations

import re

from youvedio.models import TorrentResult

_SEASON_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"[Ss](\d{1,2})\s*[Ee]"),  # S01E05
    re.compile(r"[Ss]eason[.\s]*(\d{1,2})"),  # Season 1, season.02
    re.compile(r"第(\d{1,2})\s*[季部]"),  # 第1季, 第二部
    re.compile(r"(\d{1,2})(?:st|nd|rd|th)\s*[Ss]eason"),
    re.compile(r"Part[\s.]*(\d{1,2})"),  # Part 1, Part.2
    re.compile(r"(\d{1,2})期"),  # 第一期
    re.compile(r"(?:^|\s)[Ss](\d{1,2})(?:\s|$|\.)"),  # standalone S01
]

_EPISODE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"[Ee][Pp]?\s*(\d{1,4})"),  # EP01, E01
    re.compile(r"[Ss]\d{1,2}\s*[Ee](\d{1,4})"),  # S01E05
    re.compile(r"第(\d{1,4})\s*[话話集]"),  # 第1话, 第01話
    re.compile(r"Vol[.\s]*(\d{1,4})", re.IGNORECASE),
    re.compile(r"-[\s](\d{1,4})\s*(?:v[234])?$"),  # trailing number
]

_QUALITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b4K\b", re.IGNORECASE),
    re.compile(r"\b2160p?\b", re.IGNORECASE),
    re.compile(r"\b1080p?\b", re.IGNORECASE),
    re.compile(r"\b720p?\b", re.IGNORECASE),
    re.compile(r"\b480p?\b", re.IGNORECASE),
    re.compile(r"\b360p?\b", re.IGNORECASE),
]

_SOURCE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bBlu[.-]?Ray\b", re.IGNORECASE), "Blu-ray"),
    (re.compile(r"\bBDRip\b", re.IGNORECASE), "BDRip"),
    (re.compile(r"\bWEB[.-]?DL\b", re.IGNORECASE), "WEB-DL"),
    (re.compile(r"\bWEBRip\b", re.IGNORECASE), "WEBRip"),
    (re.compile(r"\bHDTV\b", re.IGNORECASE), "HDTV"),
    (re.compile(r"\bDVD[Rr]ip\b", re.IGNORECASE), "DVDRip"),
    (re.compile(r"\bHDRip\b", re.IGNORECASE), "HDRip"),
    (re.compile(r"\bH[.]?265\b", re.IGNORECASE), "HEVC"),
    (re.compile(r"\bHEVC\b", re.IGNORECASE), "HEVC"),
    (re.compile(r"\bAVC\b", re.IGNORECASE), "h264"),
    (re.compile(r"\bAV1\b", re.IGNORECASE), "AV1"),
]


def _first_match(patterns: list, text: str) -> str | None:
    for p in patterns:
        m = p.search(text)
        if m:
            return m.group(1) if m.lastindex else m.group(0)
    return None


def _source_match(text: str) -> str | None:
    for pattern, label in _SOURCE_PATTERNS:
        if pattern.search(text):
            return label
    return None


def classify(result: TorrentResult) -> TorrentResult:
    """Classify a TorrentResult by parsing its title."""
    title = result.title

    season_match = _first_match(_SEASON_PATTERNS, title)
    if season_match:
        result.season = int(season_match)

    episode_match = _first_match(_EPISODE_PATTERNS, title)
    if episode_match:
        result.episode = int(episode_match)

    quality_match = _first_match(_QUALITY_PATTERNS, title)
    if quality_match:
        result.quality = quality_match.upper()

    source_type = _source_match(title)
    if source_type:
        result.source_type = source_type

    return result


def group_by_season(
    results: list[TorrentResult],
) -> dict[str, dict[str, list[TorrentResult]]]:
    """Group results by season label, then by quality."""
    groups: dict[str, dict[str, list[TorrentResult]]] = {}
    unclassified: list[TorrentResult] = []

    for r in results:
        season_key = f"S{r.season:02d}" if r.season is not None else None
        quality_key = r.quality or "Unknown"

        if season_key is None:
            unclassified.append(r)
            continue

        if season_key not in groups:
            groups[season_key] = {}
        if quality_key not in groups[season_key]:
            groups[season_key][quality_key] = []
        groups[season_key][quality_key].append(r)

    # Sort within each group
    for season in groups:
        for quality in groups[season]:
            groups[season][quality].sort(key=lambda x: x.seeders or 0, reverse=True)

    if unclassified:
        groups["_unclassified"] = {"All": unclassified}

    return groups
