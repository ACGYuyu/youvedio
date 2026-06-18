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

_SUBGROUP_PATTERN = re.compile(r"^\[([^\]]+)\]")

_QUALITY_RANK: dict[str, int] = {
    "4K": 0,
    "2160P": 1,
    "1080P": 2,
    "720P": 3,
    "480P": 4,
    "360P": 5,
}


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

    # Extract subgroup from [Brackets] at start of title
    sg = _SUBGROUP_PATTERN.match(title)
    if sg:
        result.subgroup = sg.group(1).strip()

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


def _season_sort_key(k: str) -> int:
    """Sort key: newest season first (_unclassified always last)."""
    if k == "_unclassified":
        return 999
    try:
        return -int(k[1:])  # S04 → -4 (before S01 → -1)
    except (ValueError, IndexError):
        return 0


def _quality_sort_key(q: str) -> int:
    """Sort key: best quality first (4K → 0, Unknown → 99)."""
    return _QUALITY_RANK.get(q, 99)


def group_by_season(
    results: list[TorrentResult],
) -> dict[str, dict[str, list[TorrentResult]]]:
    """Group by season (newest first) → quality (best first)."""
    groups: dict[str, dict[str, list[TorrentResult]]] = {}

    for r in results:
        sk = f"S{r.season:02d}" if r.season is not None else None
        qk = r.quality or "Unknown"
        if sk is None:
            groups.setdefault("_unclassified", {}).setdefault("All", []).append(r)
        else:
            groups.setdefault(sk, {}).setdefault(qk, []).append(r)

    for s in groups:
        for q in groups[s]:
            groups[s][q].sort(key=lambda x: x.seeders or 0, reverse=True)

    ordered: dict[str, dict[str, list[TorrentResult]]] = {}
    for sk in sorted(groups, key=_season_sort_key):
        ordered[sk] = dict(sorted(groups[sk].items(), key=lambda x: _quality_sort_key(x[0])))
    return ordered


def group_by_subgroup(
    results: list[TorrentResult],
) -> dict[str, dict[str, dict[str, list[TorrentResult]]]]:
    """Group by subgroup → season (newest) → quality (best)."""
    groups: dict[str, dict[str, dict[str, list[TorrentResult]]]] = {}

    for r in results:
        sg = r.subgroup or "_unknown"
        sk = f"S{r.season:02d}" if r.season is not None else None
        qk = r.quality or "Unknown"
        groups.setdefault(sg, {})
        if sk is None:
            groups[sg].setdefault("_unclassified", {}).setdefault("All", []).append(r)
        else:
            groups[sg].setdefault(sk, {}).setdefault(qk, []).append(r)

    for sg in groups:
        for s in groups[sg]:
            for q in groups[sg][s]:
                groups[sg][s][q].sort(key=lambda x: x.seeders or 0, reverse=True)

    ordered: dict[str, dict[str, dict[str, list[TorrentResult]]]] = {}
    for sg in sorted(groups):
        ordered[sg] = {}
        for sk in sorted(groups[sg], key=_season_sort_key):
            ordered[sg][sk] = dict(
                sorted(groups[sg][sk].items(), key=lambda x: _quality_sort_key(x[0]))
            )
    return ordered


def relevance_sort(query: str, results: list[TorrentResult]) -> list[TorrentResult]:
    """Sort results by relevance to the search query.

    Exact matches at title start get highest priority, then standalone
    word matches, then substring matches. Within same level, seeders
    determine order.
    """
    q_lower = query.lower().strip()
    if not q_lower:
        return results

    def score(r: TorrentResult) -> tuple[int, int]:
        title_lower = r.title.lower()
        if title_lower.startswith(q_lower) or f"[{q_lower}" in title_lower:
            return (3, r.seeders or 0)
        import re

        if re.search(rf"\b{re.escape(q_lower)}\b", title_lower):
            return (2, r.seeders or 0)
        if q_lower in title_lower:
            return (1, r.seeders or 0)
        return (0, r.seeders or 0)

    return sorted(results, key=score, reverse=True)
