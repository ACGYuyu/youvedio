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
| P2 | 内置站点解析器 | `base.py`, `nyaa.py`, `dmhy.py`, `mikan.py`, `x1337.py`, `acgrip.py`, `anidex.py`, `tokyotosho.py` | ✅ |
| P3 | 爬虫引擎 | Scrapling 封装 + 并发 + 重试 | ✅ |
| P4 | 分类器 | Season/画质/字幕组提取 + quality_summary | ✅ |
| P5 | | |
| P6 | | |
| P7 | 搜索引擎发现 | Google/Bing 搜索 → URL 提取 | ✅ |
| P8 | | |
| P9 | 整合优化 | 缓存 + MCP 纯净化 + quality_summary | ✅ |

### 版本日志

| 日期 | 提交 | 说明 |
|------|------|------|
| 2026-06-18 | `feat(scaffold): initial project structure` | 初始化项目骨架 |
| 2026-06-18 | `style(models): fix Optional→X|None annotations` | Ruff lint 自动修复 |
| 2026-06-18 | `feat(sources): add 7 built-in site parsers` | 站点解析器基类 + 7 个内置站 |
| 2026-06-18 | `feat(crawler): add crawler engine with retry and title classifier` | 爬虫引擎 + 分类器 |
| 2026-06-18 | `feat: add crawler engine, classifier, translation, and Web UI` | P3-P6: 爬虫/分类/翻译/Web |
| 2026-06-18 | `feat: add search engine discoverer and AI site analyzer` | P7-P8: 发现 + 分析 |
| 2026-06-18 | `feat(web): add settings page with proxy and AI model config` | 设置界面 |
| 2026-06-18 | `refactor: remove all AI components, pure data MCP` | 去掉 AI，纯爬虫工具 |

---

## v0.2.0 — 待规划

- 站点发现与自动入库
- 搜索结果缓存
- 批量关键词搜索
- Docker 部署

---

## 发布标准

- [x] ruff check / ruff format 通过
- [x] mypy 通过（无新增错误）
- [x] pytest 通过（覆盖率 > 80%）✅ 81%
- [ ] 人工确认搜索结果准确性
