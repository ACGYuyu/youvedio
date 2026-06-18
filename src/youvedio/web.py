"""FastAPI web application."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from youvedio.config import settings

app = FastAPI(title="YouVedio")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Render search page."""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouVedio - 种子/磁力搜索</title>
    </head>
    <body>
        <h1>YouVedio</h1>
        <p>多语言种子/磁力搜索引擎</p>
        <p style="color:#888">Coming soon...</p>
    </body>
    </html>
    """


@app.get("/api/search")
async def search(q: str = ""):
    """Search torrents (placeholder)."""
    return {"keyword": q, "results": [], "message": "Not implemented yet"}


def run_server() -> None:
    """Start uvicorn server."""
    uvicorn.run(
        "youvedio.web:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
    )
