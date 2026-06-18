"""FastAPI web application — search page, API, and settings."""

from __future__ import annotations

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from youvedio.config import settings
from youvedio.crawler.classifier import classify, group_by_season
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


class SettingsPayload(BaseModel):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    proxy_enabled: bool = False
    http_proxy: str = ""
    https_proxy: str = ""


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
        "page_url": r.page_url or "",
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if templates:
        return templates.TemplateResponse(request, "index.html", {"request": request})
    return HTMLResponse("<h1>YouVedio</h1><p>Template not found</p>")


@app.get("/api/search")
async def api_search(q: str = Query("")):
    if not q.strip():
        return JSONResponse({"keyword": q, "total": 0, "seasons": {}})

    settings.apply_proxy()
    translations = translate_query(q)
    unique_queries: list[str] = []
    for val in [q] + [translations.get(k, "") for k in ("zh", "en", "ja")]:
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

    classified = [classify(r) for r in all_results]
    seasons = group_by_season(classified)

    seasons_dict: dict[str, dict[str, list[dict]]] = {}
    for season_key, quality_map in seasons.items():
        seasons_dict[season_key] = {}
        for quality_key, items in quality_map.items():
            seasons_dict[season_key][quality_key] = [_torrent_to_dict(r) for r in items]

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


@app.get("/api/settings")
async def get_settings():
    """Return current settings (with API key masked)."""
    return JSONResponse(settings.to_dict())


@app.post("/api/settings")
async def update_settings(payload: SettingsPayload):
    """Update settings at runtime."""
    settings.update(**payload.model_dump())
    settings.apply_proxy()
    return JSONResponse({"ok": True, **settings.to_dict()})


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = Query("")):
    if not q.strip():
        return await index(request)
    if templates:
        return templates.TemplateResponse(request, "index.html", {"request": request, "q": q})
    return HTMLResponse(f"<h1>Search: {q}</h1>")


def run_server() -> None:
    """Start uvicorn server."""
    uvicorn.run(
        "youvedio.web:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
    )
