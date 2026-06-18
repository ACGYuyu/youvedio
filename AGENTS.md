# AGENTS.md

YouVedio — 多语言种子/磁力搜索引擎。输入关键词 → DeepSeek 翻译 (中/英/日) → 爬取已知种子站 → 按季/画质分类 → Web 展示。

## Python 版本

**推荐 Python 3.12**（已验证）。Python 3.13 应兼容。避免 Python 3.15 alpha（无预编译 wheel）。

## 快速开始

```bash
py -3.12 -m pip install -e ".[dev,ai]"     # 安装 + dev 依赖
py -3.12 -m pre_commit install              # 安装 git hooks
```

复制 `.env.example` 为 `.env`，填入配置：
```bash
cp .env.example .env
# 编辑 .env: 填入 DeepSeek API Key、代理等
```

启动：
```bash
py -3.12 -m youvedio serve                  # http://localhost:8000
```

如果网络在代理后，可在 `.env` 中设置或通过环境变量：
```bash
$env:HTTP_PROXY="http://127.0.0.1:10808"
$env:HTTPS_PROXY="http://127.0.0.1:10808"
```

## 开发命令顺序

```bash
ruff check . && ruff format . && mypy src/ && pytest -v
```

注意：使用 `py -3.12 -m ruff` / `py -3.12 -m mypy` / `py -3.12 -m pytest` 如果默认 Python 不是 3.12。

## 项目结构

```
src/youvedio/
├── sources/sites/    # 站点解析器 (每站一个文件)
│   ├── base.py       # 解析器基类
│   ├── nyaa.py       # Nyaa.si
│   ├── dmhy.py       # 动漫花园
│   ├── mikan.py      # 蜜柑计划
│   └── ...
├── sources/discoverer.py  # 搜索引擎发现新站点
├── crawler/
│   ├── engine.py     # Scrapling 爬虫封装
│   └── classifier.py # 季/画质归类
├── translation.py    # DeepSeek 翻译 (OpenAI 兼容)
├── analyzer/site.py  # AI 站点相关性判断
├── web.py            # FastAPI + Jinja2
├── models.py         # Pydantic 数据模型
└── config.py         # pydantic-settings (.env)
```

## Git 规范

- **分支**: `main` → `dev` → `feat/xxx` → PR → `dev` → (发布) → `main`
- **提交**: Conventional Commits: `feat(scope): msg`, `fix(scope): msg`, `refactor(scope): msg`
- **范围** (scope): `nyaa`, `dmhy`, `engine`, `classifier`, `translation`, `web`, `cli`, `scaffold`, `sources`, `analyzer`

## Web 服务器

```bash
py -3.12 -m youvedio serve          # 启动 http://localhost:8000
```

支持 `?q=` URL 参数自动搜索。代理环境需先设置 `HTTP_PROXY` 环境变量。

## 代码风格

- Ruff lint + format (line-length=100)
- MyPy 类型检查 (渐进式, `check_untyped_defs`)
- pytest + asyncio 模式 (mock HTML, 不依赖网络)
- 类 PascalCase / 函数 snake_case / 文件小写+下划线

## 版本规划

详见 [ROADMAP.md](./ROADMAP.md)。当前版本 **v0.1.0** — 核心爬虫 + Web UI。
