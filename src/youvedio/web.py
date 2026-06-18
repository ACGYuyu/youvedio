"""FastAPI web application — search page and API."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from youvedio.config import settings
from youvedio.crawler.classifier import classify, group_by_season, group_by_subgroup, relevance_sort
from youvedio.crawler.engine import CrawlerEngine
from youvedio.models import TorrentResult
from youvedio.translation import translate_query

logger = logging.getLogger(__name__)

_HERE = Path(__file__).parent
_TEMPLATES = _HERE / "templates"
_STATIC = _HERE / "static"

app = FastAPI(title="YouVedio")

if _STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

templates = Jinja2Templates(directory=str(_TEMPLATES)) if _TEMPLATES.exists() else None


def _torrent_to_dict(r: TorrentResult) -> dict:
    return {
        "source": r.source,
        "title": r.title,
        "magnet": r.magnet,
        "info_hash": r.info_hash,
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


def _sse_event(name: str, data: dict) -> str:
    """Format an SSE event string."""
    return f"event: {name}\ndata: {json.dumps(data)}\n\n"


def _build_seasons_dict(
    all_results: list[TorrentResult],
    by: str = "season",
) -> dict:
    """Classify and group results. by='season' or 'subgroup'."""
    classified = [classify(r) for r in all_results]

    def _to_dicts(items: list[TorrentResult]) -> list[dict]:
        return [_torrent_to_dict(r) for r in items]

    if by == "subgroup":
        raw_sg = group_by_subgroup(classified)
        result: dict = {}
        for sg, seasons in raw_sg.items():
            result[sg] = {}
            for season_key, quality_map in seasons.items():
                result[sg][season_key] = {q: _to_dicts(items) for q, items in quality_map.items()}
        return result

    raw_sn = group_by_season(classified)
    result = {}
    for sk, qm in raw_sn.items():
        result[sk] = {q: _to_dicts(items) for q, items in qm.items()}
    return result


def _get_queries(q: str, ai_enhanced: bool) -> list[str]:
    """Build list of search queries (with translations if AI enabled)."""
    unique: list[str] = [q]
    if ai_enhanced:
        translations = translate_query(q)
        for k in ("zh", "en", "ja"):
            val = translations.get(k, "")
            if val and val not in unique:
                unique.append(val)
    return unique[:3]


def _run_crawl(q: str, ai_enhanced: bool) -> tuple[list[TorrentResult], int, int, list[str]]:
    """Run the crawl synchronously (blocking)."""
    settings.apply_proxy()
    engine = CrawlerEngine(max_concurrent=settings.crawler_max_concurrent)
    all_results: list[TorrentResult] = []
    total_success = 0
    total_failed = 0
    all_errors: list[str] = []

    for query in _get_queries(q, ai_enhanced):
        progress = engine.search(query)
        all_results.extend(progress.results)
        total_success += progress.success
        total_failed += progress.failed
        all_errors.extend(progress.errors)

    all_results = relevance_sort(q, all_results)
    return all_results, total_success, total_failed, all_errors


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if templates:
        return templates.TemplateResponse(request, "index.html", {"request": request})
    return HTMLResponse("<h1>YouVedio</h1><p>Template not found</p>")


@app.get("/api/search")
async def api_search(
    q: str = Query(""),
    ai_enhanced: bool = Query(True),
    group_by: str = Query("season"),
):
    if not q.strip():
        return JSONResponse({"keyword": q, "total": 0, "seasons": {}})

    all_results, total_success, total_failed, all_errors = _run_crawl(q, ai_enhanced)
    seasons_dict = _build_seasons_dict(all_results, by=group_by)

    return JSONResponse(
        {
            "keyword": q,
            "total": len(all_results),
            "sites_success": total_success,
            "sites_failed": total_failed,
            "errors": all_errors,
            "seasons": seasons_dict,
        }
    )


@app.get("/api/search/stream")
async def api_search_stream(
    q: str = Query(""),
    ai_enhanced: bool = Query(True),
    group_by: str = Query("season"),
):
    """SSE endpoint that streams crawl progress and final results."""

    async def event_stream() -> AsyncGenerator[str, None]:
        if not q.strip():
            yield _sse_event("result", {"keyword": q, "total": 0, "seasons": {}})
            return

        settings.apply_proxy()
        queries = _get_queries(q, ai_enhanced)
        loop = asyncio.get_event_loop()

        all_results: list[TorrentResult] = []
        total_success = 0
        total_failed = 0
        all_errors: list[str] = []

        for qidx, query in enumerate(queries):
            engine = CrawlerEngine(max_concurrent=settings.crawler_max_concurrent)
            parsers = list(engine.source_manager.enabled_parsers.items())
            sites_done = 0
            total_sites = len(parsers)
            total_queries = len(queries)

            for name, parser in parsers:
                yield _sse_event(
                    "progress",
                    {
                        "site": name,
                        "status": "fetching",
                        "completed": sites_done,
                        "total": total_sites,
                        "queries_done": qidx,
                        "total_queries": total_queries,
                    },
                )

                def _run(p, kw):
                    return p.fetch(kw)

                try:
                    results = await loop.run_in_executor(None, _run, parser, query)
                    classified = [classify(r) for r in results]
                    all_results.extend(classified)
                    total_success += 1 if results else 0
                    sites_done += 1
                    yield _sse_event(
                        "progress",
                        {
                            "site": name,
                            "status": "ok",
                            "results": len(results),
                            "completed": sites_done,
                            "total": total_sites,
                            "queries_done": qidx,
                            "total_queries": total_queries,
                        },
                    )
                except Exception as e:
                    total_failed += 1
                    all_errors.append(f"{name}: {e}")
                    sites_done += 1
                    yield _sse_event(
                        "progress",
                        {
                            "site": name,
                            "status": "fail",
                            "error": str(e)[:60],
                            "completed": sites_done,
                            "total": total_sites,
                            "queries_done": qidx,
                            "total_queries": total_queries,
                        },
                    )

        seasons_dict = _build_seasons_dict(all_results, by=group_by)
        yield _sse_event(
            "result",
            {
                "keyword": q,
                "total": len(all_results),
                "sites_success": total_success,
                "sites_failed": total_failed,
                "errors": all_errors,
                "seasons": seasons_dict,
            },
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = Query("")):
    if not q.strip():
        return await index(request)
    if templates:
        return templates.TemplateResponse(request, "index.html", {"request": request, "q": q})
    return HTMLResponse(f"<h1>Search: {q}</h1>")


def run_server() -> None:
    uvicorn.run(
        "youvedio.web:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
    )
