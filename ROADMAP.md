# YouVedio 版本规划

> 种子/磁力搜索引擎 MCP Server

---

## v0.1.0 — MCP Server（当前）

**Python**: 3.12（推荐）| 3.13（兼容）| 避免 3.15 alpha（无预编译 wheel）  
**目标**: 纯数据层 MCP 工具，由 LLM Agent 自行处理语义理解和结果组织

### 计划内容

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P1 | 项目脚手架 | `pyproject.toml`, `config.py`, `models.py`, `__main__.py`, CLI | ✅ |
| P2 | 内置站点解析器 | 7 个站点解析器 | ✅ |
| P3 | 爬虫引擎 | Scrapling 并发爬虫 + 重试 | ✅ |
| P4 | 分类器 | Season/画质/字幕组提取 + quality_summary | ✅ |
| P5 | 搜索引擎发现 | Google/Bing 搜索 → URL 提取 | ✅ |
| P6 | 整合优化 | 缓存 + MCP 服务 + 测试 109 个 81% 覆盖率 | ✅ |

### 版本日志

| 日期 | 提交 | 说明 |
|------|------|------|
| 2026-06-18 | `feat(scaffold): initial project structure` | 初始化项目骨架 |
| 2026-06-18 | `feat(sources): add 7 built-in site parsers` | 站点解析器基类 + 7 个内置站 |
| 2026-06-18 | `feat(crawler): add crawler engine with retry and title classifier` | 爬虫引擎 + 分类器 |
| 2026-06-18 | `feat: add search engine discoverer` | 搜索引擎发现 |
| 2026-06-18 | `feat: MCP server, remove AI/Web, pure data MCP` | MCP 服务化 |
| 2026-06-18 | `feat: quality_summary, cache, test coverage 81%` | 优化 + 测试 |

---

## v0.2.0 — 待规划

- 搜索结果缓存优化
- 批量关键词搜索
- Docker 部署

---

## 发布标准

- [x] ruff check / ruff format 通过
- [x] mypy 通过（无新增错误）
- [x] pytest 通过（覆盖率 > 80%）✅ 81%
- [ ] 人工确认搜索结果准确性
