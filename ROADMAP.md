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

## v0.2.0 — 待规划

- 通用站点解析器（JSON 配置驱动，减少 80% 的新站适配工作量）
  - `sources/sites/generic.py` — 通用解析器类
  - `sources.json` 支持 `type: "generic"` 和 `selectors` 配置
  - 支持磁力在属性、需要 Playwright、非 UTF-8 编码等特例
  - 逐步迁移现有独立解析器到通用模式
- 批量关键词搜索
- Docker 部署

---

## 发布标准

- [x] ruff check / ruff format 通过
- [x] mypy 通过（无新增错误）
- [x] pytest 通过（覆盖率 > 80%）✅ 81%
- [ ] 人工确认搜索结果准确性
