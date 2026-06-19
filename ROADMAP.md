# YouVedio 版本规划

> 种子/磁力搜索引擎 MCP Server

---

## v0.1.0 — MCP Server（已发布）

**Python**: 3.12（推荐）| 3.13（兼容）| 避免 3.15 alpha（无预编译 wheel）  
**目标**: 纯数据层 MCP 工具，由 LLM Agent 自行处理语义理解和结果组织

### 计划内容

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P1 | 项目脚手架 | `pyproject.toml`, `config.py`, `models.py`, `__main__.py`, CLI | ✅ |
| P2 | 内置站点解析器 | 7 个站点解析器 | ✅ |
| P3 | 爬虫引擎 | Scrapling 并发爬虫 + 重试 | ✅ |
| P4 | 分类器 | Season/画质/字幕组提取 + quality_summary | ✅ |
| P5 | 整合优化 | 缓存 + MCP 服务 + 测试 109 个 81% 覆盖率 | ✅ |

### 版本日志

| 日期 | 提交 | 说明 |
|------|------|------|
| 2026-06-18 | `feat(scaffold): initial project structure` | 初始化项目骨架 |
| 2026-06-18 | `feat(sources): add 7 built-in site parsers` | 站点解析器基类 + 7 个内置站 |
| 2026-06-18 | `feat(crawler): add crawler engine with retry and title classifier` | 爬虫引擎 + 分类器 |
| 2026-06-18 | `feat: quality_summary, cache, test coverage 81%` | 优化 + 测试 |
| 2026-06-18 | `chore: record v0.1.1 known issues in ROADMAP` | 记录已知问题留待 v0.1.1 修复 |

---

## v0.1.1 — Bugfix（已发布）

**目标**: 修复 v0.1.0 已知问题，提升搜索可靠性

### 计划内容

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P1 | acg.rip 下线 | `sources.json` | ✅ |
| P2 | 修复 `progress.failed` 计数 | `engine.py` | ✅ |
| P3 | 排查 Scrapling `Proxy 'None'` 导致所有站点返回 0 的问题 | `base.py`, `x1337.py` | ✅ |
| P4 | 增加站点级 fetch 日志 | `engine.py` | ✅ |

### 已修复

| # | 问题 | 修复 |
|---|------|------|
| 1 | `dmhy.py` 列偏移：测试用 HTML 缺少 date 列，导致所有 CSS 选择器偏 1 位 | `dmhy.py` — 选定 `td:nth-child(3/4/5/6/7)` |
| 2 | `mikanani.me` 搜索列表无 seeders/leechers 列 | `mikan.py` — 还原 `parse()` 去掉 seeders/leechers 提取 |
| 3 | `tokyotosho.py` 重写：旧 `div.list-topic` 选择器过时 | `tokyotosho.py` — Jackett 确认的 `table.listing tr.category_0` 选择器 |
| 4 | `progress.failed` 从未递增 | `engine.py` — `_fetch_one` 返回 `errored` 标志，主循环据此递增 |
| 5 | Scrapling `Proxy 'None' failed` 警告 | `base.py` + `x1337.py` — 使用 `_cleanup_env_proxy()` / `_restore_env_proxy()` 临时清空代理 env vars |
| 6 | 缺少站点级 fetch 日志 | `engine.py` — `logger.info/warning` 记录开始/结果/失败 |
| 7 | `1337x.to` 搜索列表无磁力链接 | `x1337.py` — `parse_detail_page()` + `fetch()` 重写，跟进详情页提取 magnet |
| 8 | `acgrip.py` 补充 seeders/leechers | `acgrip.py` — 基于 NexusPHP 标准表结构添加 |
| 9 | `tokyotosho.py` 补充 seeders/leechers + 转 Jackett 选择器 | `tokyotosho.py` — `td.stats > span:nth-of-type(1/2)`，`td.desc-bot` 文本提取 size |
| 10 | `1337x.to` StealthyFetcher 超时 | `x1337.py` — `timeout` 乘以 1000（Playwright 用毫秒而 config 是秒） |
| 11 | `tokyotosho.py` search.php 返回 500 | `tokyotosho.py` — 改用 `rss.php?terms=KEYWORD` RSS feed，ElementTree 解析，seeders/leechers 默认为 0 |
| 12 | `tokyotosho.py` 测试适配 RSS | `test_tokyotosho.py` — mock XML 替换 mock HTML，seeders/leechers 断言改为 0 |

### 线上验证结果 (2026-06-19，代理 http://127.0.0.1:10808)

| 站点 | 状态 | 结果数 | 说明 |
|------|------|--------|------|
| `nyaa.si` | ✅ | 75 | title/magnet/seeders/leechers/size/page_url 全部正常 |
| `dmhy.org` | ✅ | 80 | title/magnet/size/seeders/leechers/page_url 全部正常 |
| `mikanani.me` | ✅ | 1000 | title/magnet/size/page_url 正常，确认无 seeders/leechers 列 |
| `anidex.info` | ❌ | 0 | 502 Bad Gateway（代理返回错误，非解析器问题） |
| `tokyotosho.info` | ✅ | 148 | RSS feed 正常（`search.php` 返回 500），无 seeders/leechers |
| `1337x.to` | ❌ | 0 | Cloudflare 403 拦截，StealthyFetcher 和 httpx 均无法绕过 |
| `acg.rip` | ❌ | disabled | TLS 连接失败（站点已死），已在 sources.json 禁用 |

> **MCP 端到端测试**：`search_torrents("Frieren")` 返回 **1303** 条结果，`sites_success=4, sites_failed=0`，`quality_summary` 正常包含 S02/S01/_unclassified。缓存 10 分钟 TTL 生效。

---

## v0.1.2 — 依赖瘦身 + Docker（已发布）

**目标**: 移除 Playwright/Patchright 冗余依赖（-276MB），提供生产级 Docker 镜像

### 计划内容

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P1 | 依赖重构: `scrapling[fetchers]` → `scrapling` + `curl-cffi` | `pyproject.toml` | ✅ |
| P2 | base.py fetch() 重写，移除 Scrapling Fetcher | `base.py` | ✅ |
| P3 | x1337.py StealthyFetcher 降级处理 | `x1337.py` | ✅ |
| P4 | Docker 镜像 490MB | `Dockerfile` | ✅ |

### 版本日志

| 日期 | 提交 | 说明 |
|------|------|------|
| 2026-06-19 | `refactor(deps): drop scrapling[fetchers], add curl-cffi` | 移除 playwright(138MB) + patchright(138MB)，改用 curl_cffi + httpx |
| 2026-06-19 | `refactor(base): replace Fetcher with curl_cffi in fetch()` | 移除 _cleanup_env_proxy 等 Scrapling 特定代码 |
| 2026-06-19 | `chore(docker): build 490MB image, no browser deps` | Docker 镜像 884MB → 490MB |
| 2026-06-19 | `test(x1337): adapt for StealthyFetcher unavailability` | 更新测试适配无 playwright 环境 |

### Docker 镜像

`python:3.12-slim` 基础，仅 `curl-cffi` + `scrapling` + `httpx`，**490MB**（不含 Chrome/Playwright）。

### 线上验证

| 验证项 | 结果 |
|--------|------|
| 测试套件 | 132/132 passed |
| 引擎搜索 "Frieren" | 1303 条，4 站，0 失败 |
| Docker 内搜索 | 1303 条 |
| Linux VM 搜索 | 1303 条 |
| 磁力链接覆盖率 | 100%（1303/1303）|

---

## v0.1.3 — MCP 返回值优化（待发布）

**目标**: 消除双层 JSON 编码，让 Agent 直接解析搜索结果，无需 `py -c` 命令或 PowerShell 回退

### 背景

`search_torrents()` 返回 `str`（自己 `json.dumps` 一次），FastMCP 框架再包一层 `{"result": "..."}`，导致：
- Agent 看到双层 JSON，必须先 `json.loads(outer['result'])` 解一层
- 用 `ConvertFrom-Json` 超时，用 `IndexOf`/`Substring` 出错
- 每次搜索后要花 5+ 分钟在解析上

### 计划内容

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P1 | 返回类型 `str` → `dict`，消除双层编码 | `mcp_server.py` | ⏳ |
| P2 | 新增 `summary_text` 纯文本摘要字段（可选） | `mcp_server.py` | ⏳ |

### 改动说明

**P1**（核心）：`search_torrents` 返回 `dict` 而非 `str`，FastMCP 框架直接序列化，Agent 在工具输出中看到规整的 JSON 对象：

```json
{"result": {"keyword": "...", "total": 680, "quality_summary": {...}, "seasons": {...}}}
```

改动仅：
- `mcp_server.py:80` — 类型标注 `str` → `dict`
- `mcp_server.py:93` — `return json.dumps(cached, ...)` → `return cached`
- `mcp_server.py:115` — `return json.dumps(payload, ...)` → `return payload`

无副作用，缓存仍存 dict，数据不变。

**P2**（可选）：在 payload 中加 `summary_text` 字段，一行字概括所有内容：

```python
"summary_text": "S02: 4K(2), 2160P(17), 1080P(51), Unknown(13); _unclassified: 1080P(597)"
```

Agent 无需解析 JSON 即可了解搜索结果。

---

## v0.2.0 — Generic Site Parser（待发布）

**目标**: 引入配置驱动的通用站点解析器，新增 2 个站点（API + CSS 各一），减少新站适配工作量。

### 设计方案

**GenericSiteParser**（`src/youvedio/sources/sites/generic.py`）：
- 继承 `SiteParser` ABC，根据 `mode` 分派 fetch + parse 策略
- **`mode: "api"`** — httpx POST/GET → JSON → 字段映射
- **`mode: "css"`** — 复用父类 Scrapling GET → CSS selector 逐行提取
- 配置定义在 `sources.json`，`type: "generic"` 标记
- `SourceManager.__init__()` 新增 `_load_generic_parsers()` 从 config 实例化

### 新增站点

| 站点 | 模式 | URL | 字段 | 状态 |
|------|------|-----|------|------|
| **bangumi.moe** | API (JSON POST) | `api/v2/torrent/search` | title/magnet/info_hash/size/seeders/leechers | ✅ 线上验证 102 条结果 |
| **animetosho.org** | CSS (HTML) | `/search?q={keyword}` | title/magnet/page_url/size/seeders(≥1)/leechers | ✅ 线上验证 29 条结果 |

CSS 特殊处理：seeders/leechers 从 `span[title^='Seeders:']` 的 title 属性中 regex 提取。

### 计划内容

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P1 | GenericSiteParser（API + CSS 模式） | `src/youvedio/sources/sites/generic.py` | ⏳ |
| P2 | sources.json 配置 | `sources.json` | ⏳ |
| P3 | SourceManager 加载 generic parsers | `src/youvedio/sources/manager.py` | ⏳ |
| P4 | 测试：generic API/CSS/empty/missing/regex | `tests/test_generic.py` | ⏳ |
| P5 | 测试：manager 加载 generic parsers | `tests/test_manager.py` | ⏳ |
| P6 | 线上验证 + 文档更新 | ROADMAP.md / AGENTS.md | ⏳ |
| P7 | Docker 镜像 | `Dockerfile` + `.dockerignore` | ✅ (490MB, 详见 v0.1.2) |

### 测试清单

| # | 测试 | 说明 |
|---|------|------|
| 1 | `test_generic_api_parse` | mock JSON 3 条结果 → 所有字段正确 |
| 2 | `test_generic_api_empty` | JSON 无 `torrents` key → `[]` |
| 3 | `test_generic_api_size_int` | size 是整数 → 转 str |
| 4 | `test_generic_css_parse` | mock HTML 3 行 → 字段正确 |
| 5 | `test_generic_css_empty` | HTML 无结果行 → `[]` |
| 6 | `test_generic_css_missing_fields` | 某行缺 magnet → 不崩溃 |
| 7 | `test_generic_css_seeders_regex` | `"Seeders: 1 / Leechers: 242"` → seeders=1, leechers=242 |
| 8 | `test_generic_css_bad_regex` | title 属性无匹配 → seeders=0 |
| 9 | `test_generic_search_url_api` | bangumi.moe 的 search_url 正确 |
| 10 | `test_generic_search_url_css` | animetosho 的 search_url 正确 |
| 11 | `test_generic_manager_loads` | mock sources.json generic 条目 → parsers 存在 |

### 可选项：FlareSolverr + 1337x.to 恢复

**背景**：1337x.to 被 Cloudflare JS Challenge 拦截。实测 FlareSolverr（内嵌 Chrome + 自动解 Challenge）可稳定获取搜索结果（646KB，20 条，seeders/leechers 完整）。Docker 容器自带代理路由，无需额外配置。

| 改动 | 文件 | 说明 |
|------|------|------|
| 配置 | `config.py` | `Settings` 加 `flaresolverr_url` |
| 配置 | `.env.example` | 加 `FLARESOLVERR_URL=http://127.0.0.1:8191` |
| 解析器 | `x1337.py` | `fetch()` 新增 `_fetch_via_flaresolverr()` 分支，没配则回退 curl_cffi + httpx |
| 测试 | `test_x1337.py` | mock FlareSolverr JSON 响应，5 个新测试 |
| 文档 | `AGENTS.md` | 加 FlareSolverr 运维说明 |

容器命令：
```bash
docker run -d --name flaresolverr --restart unless-stopped -p 8191:8191 -e LOG_LEVEL=warn flaresolverr/flaresolverr
```

**不做也不影响核心功能** — 目前 5 个站够用，1337x 多一个不多，少一个不少。

### P8-P9：AnimeGarden Tier 1 聚合

**背景**：`api.animes.garden` 是第三方 BT 资源聚合 API，一次请求覆盖 **dmhy + bangumi.moe + ANi** 三个站点。成熟项目（1077 stars，活跃维护），有 MCP 端点，海外可达。

**方案**：Tier 1 聚合 + Tier 2 回落

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P8 | AnimeGardenParser（SiteParser 实现） | `src/youvedio/sources/sites/animegarden.py` | ⏳ |
| P9 | Engine 两阶段策略（Tier 1 → Tier 2 fallback） | `src/youvedio/crawler/engine.py` | ⏳ |
| | 配置：sources.json 加 animegarden + fallback 关系 | `sources.json` | ⏳ |
| | 测试：mock API 响应，fallback 触发/不触发 | `tests/test_animegarden.py` | ⏳ |
| | 线上验证 | ✅ 已验证（API 返回 66KB，有结果） | |

**AnimeGardenParser**：
- `fetch()`: `GET /resources?search={keyword}&limit=50`
- `parse()`: 映射 `items[]` → `TorrentResult`（provider 标记来源）
- 无需 CSS 选择器，JSON 直取

**Engine 两阶段**：
1. **Phase 1** — 并发跑全部 Tier 1（nyaa + mikan + tokyotosho + animegarden）
2. **Phase 2** — 如果 AnimeGarden 返回 0 条或超时，回落跑 dmhy + bangumi parser

**去重**：按 `info_hash` 去重，Engine 层 `relevance_sort` 后哈希去重

### 后续（v0.3.0+）

- RSS mode（subsplease.org 等 RSS 站点）
- 分页支持（搜索多页结果）
- 批量关键词搜索
- Docker 编排（含 FlareSolverr）
- 现有解析器逐步迁移到通用模式

---

## 发布标准

- [x] ruff check / ruff format 通过
- [x] mypy 通过（无新增错误）
- [x] pytest 通过（覆盖率 > 80%）✅ 84%
- [ ] 人工确认搜索结果准确性
