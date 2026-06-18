# AGENTS.md

种子/磁力搜索引擎 MCP Server。并发爬取 7 个种子站，按季/画质/字幕组归类，通过 MCP 协议暴露。

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

Prefix each tool with `py -3.12 -m` / `python3 -m` if default Python isn't 3.12.

## Architecture

```
src/youvedio/
├── __main__.py          # python -m youvedio → cli()
├── mcp_server.py        # FastMCP server, single tool: search_torrents
├── models.py            # TorrentResult (pydantic), SearchResult, ClassifiedResult
├── config.py            # Settings from .env, singleton `settings` object
├── crawler/
│   ├── engine.py        # CrawlerEngine: concurrent fetch + retry → CrawlProgress
│   └── classifier.py    # Title → season/quality/subgroup/source_type regex
├── sources/
│   ├── manager.py       # Auto-discovers parsers via pkgutil, reads sources.json
│   └── sites/
│       ├── base.py      # SiteParser ABC: css_text/css_attr/safe_int/proxy helpers
│       ├── nyaa.py / dmhy.py / mikan.py / x1337.py / acgrip.py / anidex.py / tokyotosho.py
└── storage/
    └── cache.py         # TTL cache (10 min), used by mcp_server
```

- **Parsers auto-register**: any file in `src/youvedio/sources/sites/` (except `base.py`) with a `SiteParser` subclass is auto-discovered by `pkgutil.iter_modules`. Register in `sources.json` for enable/disable config.
- **Engine progress**: `_fetch_one` returns `(name, results, errored: bool)`; `progress.failed` increments on `errored=True` and zero results.
- **MCP search_torrents**: cached 10 min. Returns `seasons` + `quality_summary`. Results auto-sorted by relevance → seeders within same quality.

## Scrapling gotchas

- `::text` pseudo-element **does not work** with attribute selectors like `a[type='...']` — avoid combining them. Use element text extraction directly (e.g., `el.css("selector").get()` without `::text`).
- Prefer `:nth-of-type(n)` over `:nth-child(n)` when elements of other types (like `<br>`) may appear between targets.
- Proxy env vars (`HTTP_PROXY`, etc.) are read by Scrapling internally. When no proxy is configured, `_cleanup_env_proxy()` / `_restore_env_proxy()` in `base.py` temporarily pops them to prevent `Proxy 'None' failed` warnings.
- Scrapling INFO-level logging is silenced at `base.py` import time — only WARNING+ shows.

## Testing patterns

- **Parser tests**: inline mock HTML (no network). Instantiate parser, call `parse(html)`, assert fields on `TorrentResult`.
- **Engine tests**: `@patch("youvedio.crawler.engine.SourceManager")` + `MagicMock()` parsers. Always use `retry_count=0` to avoid real fetches.
- **All tests** pass without network. 123 tests as of v0.1.1.

## Adding a new site

1. Create `src/youvedio/sources/sites/<name>.py` — inherit `SiteParser`, implement `search_url()` + `parse()`.
2. Register in `sources.json` with `"enabled": true`.
3. Validate: `ruff check . && mypy src/ && pytest -v`.

Helper methods available on `SiteParser`: `css_text`, `css_attr`, `safe_int`, `normalize_size`, `extract_info_hash`, `extract_page_url`.

## Online verification (2026-06-19, proxy via 127.0.0.1:10808)

| Site | Reachable | Results | Notes |
|------|-----------|---------|-------|
| **nyaa.si** | ✅ | 75 | seeders/leechers/magnet all correct |
| **dmhy.org** | ✅ | 80 | seeders/leechers/magnet all correct |
| **mikanani.me** | ✅ | 1000 | no seeders/leechers columns (expected) |
| **anidex.info** | ❌ | 0 | 502 Bad Gateway (proxy/network issue) |
| **tokyotosho.info** | ✅ | 148 | RSS feed (search.php returns 500 server-side) |
| **1337x.to** | ❌ | 0 | Cloudflare 403 even via StealthyFetcher |
| **acg.rip** | ❌ | 0 | TLS error — disabled in sources.json |

## Known quirks

- **`acg.rip` is dead** (SSL errors, always times out). Disabled in `sources.json`.
- **TokyoTosho**: Uses RSS feed (`rss.php?terms=...`) because `search.php` returns HTTP 500 server-side. RSS has no seeders/leechers — defaults to 0. `tokyotosho.info` (plain) redirects cause SSRF; uses `www.tokyotosho.info` directly.
- **1337x.to**: search listing blocked (Cloudflare 403), `parse_detail_page()` uses `StealthyFetcher` to follow detail pages for magnet links. Not reachable even via proxy.
- **proxy-less deployments**: `settings.apply_proxy()` in `mcp_server.py` only writes env vars if `http_proxy` is non-empty. On servers without proxy, it's a no-op.

## Git

- Conventional Commits: `feat(scope): msg`, `fix(scope): msg` etc.
- Scope from: `nyaa`, `dmhy`, `engine`, `classifier`, `mcp`, `cli`, `scaffold`, `sources`, `storage`.
- Branch flow: `main` ← `dev` ← `feat/xxx` → PR → `dev`.

## Agent workflow (search_torrents)

1. Resolve abbreviations yourself (RE0 → Re:Zero, MHA → My Hero Academia).
2. Search once — `quality_summary` tells you everything available per season. Do NOT re-search for specific qualities.
3. Check `_unclassified` for movies/OVAs/SPs (no season number) — may contain 4K/2160P.
4. Reply in natural language: `[SubGroup] → Season X → Quality (count)`. Recommend highest-seeded.
5. Batch = `episode === null`; single episodes = `episode !== null`.
