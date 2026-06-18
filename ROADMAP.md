# YouVedio 版本规划

> 种子/磁力多语言搜索引擎

---

## v0.1.0 — 核心爬虫 + Web UI（当前）

**Python**: 3.12（推荐）| 3.13（兼容）| 避免 3.15 alpha（无预编译 wheel）  
**目标**: 实现完整的搜索流水线：输入关键词 → 多语言翻译 → 爬取已知种子站 → 分类 → Web 展示

### 计划内容

| 阶段 | 模块 | 文件 | 状态 |
|------|------|------|------|
| P1 | 项目脚手架 | `pyproject.toml`, `config.py`, `models.py`, `__main__.py`, CLI | ✅ |
| P2 | 内置站点解析器 | `base.py`, `nyaa.py`, `dmhy.py`, `mikan.py`, `x1337.py`, `acgrip.py`, `anidex.py`, `tokyotosho.py` | ✅ |
| P3 | 爬虫引擎 | Scrapling 封装 + 并发 + 重试 | ✅ |
| P4 | 分类器 | Season/画质/格式提取 | ✅ |
| P5 | 翻译服务 | DeepSeek API (中→英/日) | ✅ |
| P6 | Web UI | FastAPI + Jinja2 简约搜索页 + 分类 Tab | ✅ |
| P7 | 搜索引擎发现 | Google/Bing 搜索 → URL 提取 | ✅ |
| P8 | AI 站点分析 | DeepSeek 判断站点相关性 | ✅ |
| P9 | 整合联调 | 全流程流水线 | ⬜ |

### 版本日志

| 日期 | 提交 | 说明 |
|------|------|------|
| 2026-06-18 | `feat(scaffold): initial project structure` | 初始化项目骨架 |
| 2026-06-18 | `style(models): fix Optional→X|None annotations` | Ruff lint 自动修复 |
| 2026-06-18 | `feat: add search engine discoverer and AI site analyzer` | P7-P8: 搜索引擎发现 + AI 站点分析 |

---

## v0.2.0 — 待规划

- 站点发现与自动入库
- 搜索结果缓存
- 批量关键词搜索
- Docker 部署

---

## 发布标准

- [ ] ruff check / ruff format 通过
- [ ] mypy 通过（无新增错误）
- [ ] pytest 通过（覆盖率 > 80%）
- [ ] 人工确认搜索结果准确性
