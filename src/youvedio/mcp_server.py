"""YouVedio MCP Server — torrent search via Model Context Protocol."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from youvedio.analyzer.classify_ai import ai_classify_results, apply_ai_classification
from youvedio.config import settings
from youvedio.crawler.classifier import classify, group_by_season, relevance_sort
from youvedio.crawler.engine import CrawlerEngine
from youvedio.models import TorrentResult

server = FastMCP(
    name="YouVedio",
    instructions=(
        "Torrent/magnet search engine for anime and video content. "
        "Supports multi-language search (Chinese/English/Japanese) via AI translation, "
        "automatic season/quality classification, and AI-powered result organization."
    ),
)


def _to_dict(r: TorrentResult) -> dict[str, Any]:
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


def _seasons_to_json(
    seasons: dict[str, dict[str, list[TorrentResult]]],
) -> dict[str, dict[str, list[dict]]]:
    result: dict[str, dict[str, list[dict]]] = {}
    for sk, qm in seasons.items():
        result[sk] = {q: [_to_dict(r) for r in items] for q, items in qm.items()}
    return result


@server.tool(
    name="search_torrents",
    description=(
        "Search torrent/magnet sites for anime or video content. "
        "Returns results grouped by season and quality. "
        "Set ai_enhanced=false to disable multi-language translation."
    ),
)
def search_torrents(
    keyword: str,
    ai_enhanced: bool = True,
) -> str:
    """Search all known torrent sites for a keyword.

    Args:
        keyword: Search term (anime/video title).
        ai_enhanced: Enable multi-language translation via AI. Default True.

    Returns:
        JSON string with results grouped by season/quality.
    """
    from youvedio.translation import translate_query

    settings.apply_proxy()

    unique_queries: list[str] = [keyword]
    if ai_enhanced:
        translations = translate_query(keyword)
        for k in ("zh", "en", "ja"):
            val = translations.get(k, "")
            if val and val not in unique_queries:
                unique_queries.append(val)

    engine = CrawlerEngine(max_concurrent=settings.crawler_max_concurrent)
    all_results: list[TorrentResult] = []
    total_success = 0
    total_failed = 0
    all_errors: list[str] = []

    for query in unique_queries[:3]:
        progress = engine.search(query)
        all_results.extend(progress.results)
        total_success += progress.success
        total_failed += progress.failed
        all_errors.extend(progress.errors)

    all_results = relevance_sort(keyword, all_results)
    classified = [classify(r) for r in all_results]
    seasons = group_by_season(classified)

    return json.dumps(
        {
            "keyword": keyword,
            "total": len(all_results),
            "sites_success": total_success,
            "sites_failed": total_failed,
            "errors": all_errors[:5],
            "seasons": _seasons_to_json(seasons),
        },
        ensure_ascii=False,
    )


@server.tool(
    name="classify_results",
    description=(
        "Re-classify search results using AI. "
        "Groups by subtitle group, newest season first, best quality first. "
        "Input should be the JSON output from search_torrents."
    ),
)
def classify_results(results_json: str, keyword: str) -> str:
    """Use AI to re-organize search results by subgroup → season → quality.

    Args:
        results_json: JSON string from search_torrents containing results.
        keyword: Original search keyword.

    Returns:
        JSON string with AI-organized results.
    """
    data = json.loads(results_json)
    raw_results: list[TorrentResult] = []

    for season_data in data.get("seasons", {}).values():
        for items in season_data.values():
            for item in items:
                raw_results.append(TorrentResult(**item))

    if not raw_results:
        return json.dumps({"keyword": keyword, "total": 0, "groups": {}})

    ai_data = ai_classify_results(raw_results, keyword)
    if ai_data:
        organized = apply_ai_classification(raw_results, ai_data)
        return json.dumps(
            {
                "keyword": keyword,
                "total": sum(
                    len(items)
                    for sg in organized.values()
                    for sk in sg.values()
                    for items in sk.values()
                ),
                "groups": organized,
            },
            ensure_ascii=False,
        )

    # Fallback: return local grouping
    classified = [classify(r) for r in raw_results]
    seasons = group_by_season(classified)
    return json.dumps(
        {"keyword": keyword, "total": len(raw_results), "groups": _seasons_to_json(seasons)},
        ensure_ascii=False,
    )


@server.resource(
    uri="youvedio://status",
    name="Server Status",
    description="Get server status and configuration info.",
)
def server_status() -> str:
    """Return server status."""
    return json.dumps(
        {
            "name": "YouVedio",
            "version": "0.1.0",
            "ai_api_configured": bool(settings.deepseek_api_key),
            "proxy_configured": bool(settings.http_proxy),
            "sites": list(CrawlerEngine().source_manager.enabled_parsers.keys()),
        },
        ensure_ascii=False,
    )
