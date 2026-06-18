# AGENTS.md

种子/磁力搜索引擎 MCP Server。并发爬取 5 个种子站，按季/画质/字幕组归类，通过 MCP 协议暴露。

## Quick start

```bash
cp .env.example .env
pip install -e ".[dev]"
pre-commit install
py -3.12 -m youvedio mcp               # stdio
py -3.12 -m youvedio mcp --transport sse  # HTTP
```

Linux: replace `py -3.12` with `python3`, `pip` with `pip3`.

## Dev loop (order matters)

```bash
ruff check . && ruff format . && mypy src/ && pytest -v
```

If default Python isn't 3.12, prefix each tool: `py -3.12 -m` / `python3 -m`.

## Architecture

```
src/youvedio/
├── __main__.py          # python -m youvedio → cli()
├── mcp_server.py        # FastMCP server, single tool: search_torrents
├── models.py            # TorrentResult (pydantic)
├── config.py            # Settings from .env, singleton
├── crawler/
│   ├── engine.py        # CrawlerEngine: concurrent fetch + retry → CrawlProgress
│   └── classifier.py    # Title → season/quality/subgroup/source_type regex
├── sources/
│   ├── manager.py       # Auto-discovers parsers via pkgutil, reads sources.json
│   └── sites/
│       ├── base.py      # SiteParser ABC: css_text/css_attr/safe_int/proxy helpers
│       ├── nyaa.py / dmhy.py / mikan.py / x1337.py / acgrip.py / anidex.py / tokyotosho.py
└── storage/
    └── cache.py         # TTL cache (10 min), file-based
```

- **Parsers auto-register**: any file in `src/youvedio/sources/sites/` (except `base.py`) with a `SiteParser` subclass is discovered by `pkgutil.iter_modules`. Register in `sources.json` to enable/disable.
- **Engine progress**: `_fetch_one` returns `(name, results, errored: bool)`; `progress.failed` increments on `errored=True` with zero results.
- **MCP search_torrents**: cached 10 min (file-based JSON in `data/cache/`). Returns `seasons` + `quality_summary`. Sorted by relevance → seeders within same season/quality.

## Dependencies

- `scrapling` (no `[fetchers]`) — CSS/HTML parsing only (`scrapling.parser.Selector`)
- `curl-cffi` — TLS fingerprint HTTP (default in `SiteParser.fetch()`)
- `httpx` — fallback HTTP (when curl_cffi fails)
- Playwright + Patchright were removed in v0.1.2; StealthyFetcher path retained with try/except in `x1337.py`. Docker: 490MB.

## Scrapling gotchas

- `::text` pseudo-element does **not** work with attribute selectors like `a[type='...']` — use element text directly (`el.css("selector").get()`).
- Prefer `:nth-of-type(n)` over `:nth-child(n)` when `<br>` or other elements may appear between targets.
- Scrapling INFO logging is silenced at `base.py` import time — only WARNING+ shows.

## Testing patterns

- **Parser tests**: inline mock HTML (no network). Instantiate parser, call `parse(html)`, assert fields on `TorrentResult`.
- **Engine tests**: `@patch("youvedio.crawler.engine.SourceManager")` + `MagicMock()` parsers. Use `retry_count=0` to avoid fetches.
- **All 132 tests** pass without network.

## Adding a new site

1. Create `src/youvedio/sources/sites/<name>.py` — inherit `SiteParser`, implement `search_url()` + `parse()`.
2. Register in `sources.json` with `"enabled": true`.
3. Validate: `ruff check . && mypy src/ && pytest -v`.

Helper methods: `css_text`, `css_attr`, `safe_int`, `normalize_size`, `extract_info_hash`, `extract_page_url`.

## Docker

```bash
docker build -t youvedio . && docker run -d -p 8000:8000 youvedio
```

`python:3.12-slim` base, 490MB. Proxy via `-e HTTP_PROXY=...`. Default: SSE on port 8000.

## Online status

| Site | Reachable | Results | Notes |
|------|-----------|---------|-------|
| nyaa.si | ✅ | 75 | All fields correct |
| dmhy.org | ✅ | 80 | All fields correct |
| mikanani.me | ✅ | 1000 | No seeders/leechers column (expected) |
| tokyotosho.info | ✅ | 148 | RSS feed (search.php returns 500) — seeders default 0 |
| 1337x.to | ❌ | 0 | Cloudflare 403. FlareSolverr bypasses it (optional) |
| anidex.info | ❌ | 0 | DDoS-Guard (not Cloudflare), reachable via proxy |
| acg.rip | ❌ | disabled | TCP EOF on all domains — site dead |

## Known quirks

- **TokyoTosho**: Uses RSS (`rss.php?terms=...`) because `search.php` returns 500. RSS has no seeders/leechers. Uses `www.tokyotosho.info` (plain redirect causes SSRF).
- **1337x.to**: Cloudflare 403 blocks search + detail pages. FlareSolverr (port 8191) works if deployed. Without it, falls back to curl_cffi + httpx (both fail).
- **anidex.info**: Behind DDoS-Guard JS challenge (not Cloudflare). Worth revisiting if challenge solver is added.
- **proxy-less deployments**: `settings.apply_proxy()` in `mcp_server.py` no-ops when `http_proxy` is empty.

## Git

- Conventional Commits: `feat(scope): msg`, `fix(scope): msg`, `refactor(scope)`, `chore`, `docs`, `test`.
- Scopes: `nyaa`, `dmhy`, `engine`, `classifier`, `mcp`, `cli`, `scaffold`, `sources`, `storage`.
- Branch flow: `main` ← `dev` ← `feat/xxx` → PR → `dev`.

## Agent workflow (search_torrents)

1. Resolve abbreviations yourself (RE0 → Re:Zero, MHA → My Hero Academia).
2. Search once — `quality_summary` shows all available per season. Do NOT re-search for specific qualities.
3. Check `_unclassified` for movies/OVAs/SPs (no season number) — may contain 4K/2160P.
4. Reply naturally: `[SubGroup] → Season X → Quality (count)`. Recommend highest-seeded.
5. Batch = `episode === null`; single episodes = `episode !== null`.
