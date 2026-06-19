# AGENTS.md

种子/磁力搜索引擎 MCP Server。并发爬取多个种子站，按季/画质/字幕组归类，通过 MCP 协议暴露。

## Quick start

```bash
cp .env.example .env
pip install -e ".[dev]"
pre-commit install
py -3.12 -m youvedio mcp                  # stdio
py -3.12 -m youvedio mcp --transport sse  # HTTP
```

Linux: replace `py -3.12` with `python3`, `pip` with `pip3`.

## Dev loop (order matters)

```bash
ruff check . && ruff format . && mypy src/ && pytest -v
```

CI runs the same checks in 3 parallel jobs (ruff, mypy, pytest) plus coverage gate: `pytest --cov=src --cov-fail-under=80`.

### Test markers

```bash
pytest -m "not network"   # CI — all offline tests (132 tests)
pytest -m network          # manual — hits real sites, needs proxy
pytest -v                  # default runs all, network tests skip unless marked
```

## Architecture

```
src/youvedio/
├── __main__.py          # python -m youvedio → CLI
├── mcp_server.py        # FastMCP, single tool: search_torrents → returns JSON string
├── models.py            # TorrentResult (pydantic)
├── config.py            # Settings from .env, singleton
├── crawler/
│   ├── engine.py        # CrawlerEngine: concurrent fetch + retry → CrawlProgress
│   └── classifier.py    # Title → season/quality/subgroup/source_type regex
├── sources/
│   ├── manager.py       # Auto-discovers parsers via pkgutil, reads sources.json
│   └── sites/
│       ├── base.py      # SiteParser ABC: css_text/css_attr/safe_int helpers
│       ├── nyaa.py / dmhy.py / mikan.py / x1337.py / tokyotosho.py
│       ├── anidex.py    # always fails (DDoS-Guard)
│       └── acgrip.py    # disabled (site dead)
└── storage/
    └── cache.py         # TTL cache (10 min, file-based JSON)
```

## Sources

sources.json at repo root, not inside src/.

| Site | Status | Notes |
|------|--------|-------|
| nyaa.si | ✅ |  |
| dmhy.org | ✅ |  |
| mikanani.me | ✅ | No seeders/leechers column (expected) |
| tokyotosho.info | ✅ | RSS feed (search.php returns 500), seeders default 0 |
| 1337x.to | ❌ | Cloudflare 403. FlareSolverr (port 8191) can bypass (optional) |
| anidex.info | ❌ | DDoS-Guard JS challenge, always fails |
| acg.rip | ❌ | disabled — site dead |

**Parsers auto-register**: any `.py` file in `sources/sites/` (except `base.py`) with a `SiteParser` subclass is discovered. Enable/disable in `sources.json`.

## Scrapling gotchas

- `::text` does **not** work with attribute selectors like `a[type='...']` — use `el.css("selector").get()`.
- Prefer `:nth-of-type(n)` over `:nth-child(n)` when `<br>` may appear between targets.
- Scrapling INFO logging silenced at `base.py` import time — only WARNING+ shows.
- `scrapling` installed **without** `[fetchers]` extra — CSS/HTML parsing only. HTTP fetching via `curl_cffi` + `httpx` fallback in `base.py`.

## Testing patterns

- **Parser tests**: inline mock HTML (no network). Instantiate parser, call `parse(html)`, assert fields.
- **Engine tests**: `@patch("youvedio.crawler.engine.SourceManager")` + `MagicMock()`. Use `retry_count=0`.
- **All 132 tests** pass without network. Mark integration tests `@pytest.mark.network`.

## MCP tool quirks

- `search_torrents()` returns `str` — a JSON string. FastMCP wraps it as `{"result": "..."}`.
- The agent sees **double-encoded JSON**: `{"result": "{\\"keyword\\": ...}"}`. Parse with:
  ```
  py -3.12 -c "import json; f=open('FILE','r',encoding='utf-8'); outer=json.load(f); inner=json.loads(outer['result']); print(json.dumps(inner.get('quality_summary',{}),indent=2,ensure_ascii=False))"
  ```
- **Do NOT** use PowerShell `ConvertFrom-Json`, `Select-String`, `IndexOf`, or subagents — they fail or timeout.
- v0.1.3 planned fix: change return type `str` → `dict` to eliminate double encoding.

## Release workflow

Tag push (e.g., `v0.1.3`) triggers `.github/workflows/release.yml`:
- Runs tests (ruff + format + mypy + pytest)
- Generates grouped changelog from conventional commits
- Creates GitHub Release with notes

```bash
git tag v0.x.x && git push origin v0.x.x
```

## opencode.json

MCP command uses `python3` (Linux default). Windows: change to `["py", "-3.12", "-m", "youvedio", "mcp"]`.

## Pre-commit

`.pre-commit-config.yaml` runs ruff lint + ruff format + mypy on every commit.

## Agent workflow (search_torrents)

1. Resolve abbreviations yourself (RE0 → Re:Zero, MHA → My Hero Academia).
2. Search once — `quality_summary` shows all available per season. Do NOT re-search for specific qualities.
3. Parse the tool output using the command above. Check `_unclassified` for movies/OVAs/SPs (no season number) — may contain 4K/2160P.
4. Reply naturally: `[SubGroup] → Season X → Quality (count)`. Recommend highest-seeded.
5. Batch = `episode === null`; single episodes = `episode !== null`.

## v0.2.0 roadmap

See ROADMAP.md. Major phases:
- P1-P3: GenericSiteParser (config-driven CSS parser, migrate existing 5 sites)
- P4-P5: AnimeGarden Tier 1 aggregation (one API call covers dmhy + bangumi.moe + ANi)
- P6: Integration tests (network test marker)
- Optional: FlareSolverr for 1337x.to
