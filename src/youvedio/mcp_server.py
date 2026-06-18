"""YouVedio MCP Server — torrent search via Model Context Protocol."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from youvedio.config import settings
from youvedio.crawler.classifier import classify, group_by_season, relevance_sort
from youvedio.crawler.engine import CrawlerEngine
from youvedio.models import TorrentResult
from youvedio.storage.cache import get as cache_get
from youvedio.storage.cache import set as cache_set

server = FastMCP(
    name="YouVedio",
    instructions="Torrent/magnet search engine for anime and video content.",
)


def _to_dict(r: TorrentResult) -> dict:
    return {
        "source": r.source,
        "title": r.title,
        "magnet": r.magnet,
        "info_hash": r.info_hash or "",
        "size": r.size or "",
        "seeders": r.seeders,
        "leechers": r.leechers,
        "season": r.season,
        "episode": r.episode,
        "quality": r.quality or "",
        "source_type": r.source_type or "",
        "subgroup": r.subgroup or "",
        "page_url": r.page_url or "",
    }


def _seasons_to_json(seasons):
    result = {}
    for sk, qm in seasons.items():
        result[sk] = {q: [_to_dict(r) for r in items] for q, items in qm.items()}
    return result


@server.tool(
    name="search_torrents",
    description=(
        "Search all known torrent/magnet sites for anime or video content. "
        "Returns results grouped by season and quality. "
        "Results are cached for 10 minutes."
    ),
)
def search_torrents(keyword: str) -> str:
    """Search all known torrent sites for a keyword.

    Args:
        keyword: Search term (anime/video title in any language).

    Returns:
        JSON string with results grouped by season and quality.
    """
    cache_key = f"search:{keyword.strip().lower()}"
    cached = cache_get(cache_key)
    if cached:
        return json.dumps(cached, ensure_ascii=False)

    settings.apply_proxy()

    engine = CrawlerEngine(max_concurrent=settings.crawler_max_concurrent)
    progress = engine.search(keyword)

    all_results = relevance_sort(keyword, progress.results)
    classified = [classify(r) for r in all_results]
    seasons = group_by_season(classified)

    payload = {
        "keyword": keyword,
        "total": len(all_results),
        "sites_success": progress.success,
        "sites_failed": progress.failed,
        "seasons": _seasons_to_json(seasons),
    }

    cache_set(cache_key, payload)
    return json.dumps(payload, ensure_ascii=False)


@server.resource(
    uri="youvedio://status",
    name="Server Status",
    description="Server status and configured sites.",
)
def server_status() -> str:
    return json.dumps(
        {
            "name": "YouVedio",
            "version": "0.1.0",
            "proxy_configured": bool(settings.http_proxy or settings.https_proxy),
            "sites": list(CrawlerEngine().source_manager.enabled_parsers.keys()),
        },
        ensure_ascii=False,
    )
