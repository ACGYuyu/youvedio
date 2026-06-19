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

## v0.2.0 — 解析器通用化 + 聚合（待发布）

**目标**: 将 v0.1 的 5 个硬编码站点解析器迁移到配置驱动模式，再加 AnimeGarden 聚合源减少请求数。

---

### P1-P3：GenericSiteParser 框架

将现存 5 个独立 Parser 的共性抽成 GenericSiteParser，配置驱动不再重复写 class。

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P1 | GenericSiteParser（CSS 模式） | `src/youvedio/sources/sites/generic.py` | ⏳ |
| P2 | 现存在 5 站迁移到 generic 配置 | `sources.json` + 各站 .py 文件 | ⏳ |
| P3 | SourceManager 加载 generic parsers | `src/youvedio/sources/manager.py` | ⏳ |

**GenericSiteParser**（`mode: "css"`）：
- 继承 `SiteParser` ABC
- 配置项：`url_template`、`row_selector`、`fields`（字段名 → CSS selector）
- 迁移范围：nyaa / dmhy / mikan / tokyotosho（CSS 选择器直接写进 `sources.json`）
- x1337 保留独立 parser（Cloudflare 需要特殊处理）

**迁移收益**：
- 新增站点只需写 `sources.json` 配置，不写代码
- 现有 5 站维护量减少（CSS 变化只改配置不改代码）
- Parser 文件从 5 个 → 1 个（generic.py）+ 1 个（x1337.py）

---

### P4-P5：AnimeGarden Tier 1 聚合

**背景**：`api.animes.garden` 是第三方 BT 聚合 API，一次请求覆盖 **dmhy + bangumi.moe + ANi** 三个站点。成熟项目（1077 stars，活跃维护），海外可达。

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P4 | AnimeGardenParser（API 模式 GenericSiteParser） | `sources.json` 配置 | ⏳ |
| P5 | Engine 两阶段策略（Tier 1 → Tier 2 fallback） | `src/youvedio/crawler/engine.py` | ⏳ |
| | 配置：sources.json 加 animegarden + fallback 关系 | `sources.json` | ⏳ |
| | 测试：mock API 响应 | `tests/test_animegarden.py` | ⏳ |

**Engine 两阶段**：
1. **Phase 1** — 并发跑全部 Tier 1（nyaa + mikan + tokyotosho + animegarden）
2. **Phase 2** — 如果 AnimeGarden 返回 ≤ 5 条或超时，回落跑 dmhy + bangumi parser

**去重**：按 `info_hash` 去重，Engine 层 `relevance_sort` 后哈希去重

---

### 可选项：FlareSolverr + 1337x.to 恢复

**背景**：1337x.to 被 Cloudflare JS Challenge 拦截。实测 FlareSolverr 可稳定获取结果。

| 改动 | 文件 | 说明 |
|------|------|------|
| 配置 | `config.py` | `Settings` 加 `flaresolverr_url` |
| 解析器 | `x1337.py` | `fetch()` 新增 `_fetch_via_flaresolverr()` 分支 |
| 测试 | `test_x1337.py` | mock FlareSolverr JSON 响应 |

**不做也不影响核心功能** — AnimeGarden + nyaa + mikan + tokyotosho 已覆盖多数场景。

---

### 测试清单

**GenericSiteParser 测试**：

| # | 测试 | 说明 |
|---|------|------|
| 1 | `test_generic_css_parse` | mock HTML → 字段正确 |
| 2 | `test_generic_css_empty` | HTML 无结果 → `[]` |
| 3 | `test_generic_css_missing_fields` | 某行缺字段 → 不崩溃 |
| 4 | `test_generic_search_url` | url_template 正确 |
| 5 | `test_generic_manager_loads` | sources.json generic 条目 → parsers 存在 |
| 6-10 | 迁移后各站回归测试 | 原有 Parser 测试继续通过 |

**AnimeGarden 测试**：

| # | 测试 | 说明 |
|---|------|------|
| 11 | `test_animegarden_fetch` | mock API 返回 10 条 → 正确 |
| 12 | `test_animegarden_empty` | API 返回 0 条 → `[]` |
| 13 | `test_engine_fallback` | mock AnimeGarden 超时 → dmhy 回落触发 |

---

### 发布标准

- P1-P3 迁移完成（5 站 → generic 配置）
- P4-P5 开发 + 测试完成
- 原 132 测试全部通过 + 新测试全覆盖
- ruff / mypy / pytest 全绿

### 后续（v0.3.0+）

- RSS mode（subsplease.org 等 RSS 站点）
- 分页支持（搜索多页结果）
- 批量关键词搜索
- Docker 编排（含 FlareSolverr）

---

## 发布标准

- [x] ruff check / ruff format 通过
- [x] mypy 通过（无新增错误）
- [x] pytest 通过（覆盖率 > 80%）✅ 84%
- [ ] 人工确认搜索结果准确性
