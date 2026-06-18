# AGENTS.md

YouVedio — 多语言种子/磁力搜索引擎 MCP Server。LLM Agent 通过 MCP 协议调用工具搜索种子站，返回结构化结果。

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

如果网络在代理后，可在 `.env` 中设置或通过环境变量：
```bash
$env:HTTP_PROXY="http://127.0.0.1:10808"
$env:HTTPS_PROXY="http://127.0.0.1:10808"
```

## 启动 MCP Server

```bash
py -3.12 -m youvedio mcp                   # stdio 模式 (Claude Desktop)
py -3.12 -m youvedio mcp --transport sse   # SSE 模式 (HTTP)
```

### Claude Desktop 配置

```json
{
  "mcpServers": {
    "youvedio": {
      "command": "py",
      "args": ["-3.12", "-m", "youvedio", "mcp"],
      "env": {
        "HTTP_PROXY": "http://127.0.0.1:10808",
        "HTTPS_PROXY": "http://127.0.0.1:10808"
      }
    }
  }
}
```

## 开发命令顺序

```bash
ruff check . && ruff format . && mypy src/ && pytest -v
```

注意：使用 `py -3.12 -m ruff` / `py -3.12 -m mypy` / `py -3.12 -m pytest` 如果默认 Python 不是 3.12。

## 项目结构

```
src/youvedio/
├── mcp_server.py       # MCP 服务 (tools + resources)
├── sources/sites/      # 站点解析器 (每站一个文件)
│   ├── base.py         # 解析器基类
│   ├── nyaa.py         # Nyaa.si
│   ├── dmhy.py         # 动漫花园
│   ├── mikan.py        # 蜜柑计划
│   └── ...
├── sources/discoverer.py  # 搜索引擎发现新站点
├── crawler/
│   ├── engine.py       # Scrapling 爬虫引擎 (并发)
│   └── classifier.py   # 季/画质/字幕组归类
├── translation.py      # DeepSeek 翻译 (OpenAI 兼容)
├── analyzer/
│   ├── site.py         # AI 站点相关性判断
│   └── classify_ai.py  # AI 结果归类 (字幕组→季→画质)
├── models.py           # 数据模型
└── config.py           # .env 配置
```

## MCP Tools

| Tool | 说明 |
|------|------|
| `search_torrents` | 搜索所有已知种子站，返回按季/画质归类的结果 |
| `classify_results` | AI 按字幕组→最新季→最高清重新组织结果 |

## Resource

| URI | 说明 |
|-----|------|
| `youvedio://status` | 服务器状态和配置信息 |

## Git 规范

- **分支**: `main` → `dev` → `feat/xxx` → PR → `dev` → (发布) → `main`
- **提交**: Conventional Commits: `feat(scope): msg`, `fix(scope): msg`, `refactor(scope): msg`
- **范围** (scope): `nyaa`, `dmhy`, `engine`, `classifier`, `translation`, `mcp`, `cli`, `scaffold`, `sources`, `analyzer`

## 代码风格

- Ruff lint + format (line-length=100)
- MyPy 类型检查 (渐进式, `check_untyped_defs`)
- pytest + asyncio 模式 (mock HTML, 不依赖网络)
- 类 PascalCase / 函数 snake_case / 文件小写+下划线

## 版本规划

详见 [ROADMAP.md](./ROADMAP.md)。当前版本 **v0.1.0** — MCP Server。
