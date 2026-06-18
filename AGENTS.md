# AGENTS.md

YouVedio — 种子/磁力搜索引擎 MCP Server。LLM Agent 通过 MCP 协议调用工具搜索种子站，返回结构化结果。

## Python 版本

**推荐 Python 3.12**（已验证）。Python 3.13 应兼容。避免 Python 3.15 alpha（无预编译 wheel）。

## 快速开始

```bash
py -3.12 -m pip install -e ".[dev]"         # 安装 + dev 依赖
py -3.12 -m pre_commit install              # 安装 git hooks
```

复制 `.env.example` 为 `.env`，填入配置：
```bash
cp .env.example .env
# 编辑 .env: 填入代理等
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
├── storage/
│   └── cache.py        # 结果缓存 (TTL 10分钟)
├── models.py           # 数据模型
└── config.py           # .env 配置
```

## MCP Tools

| Tool | 说明 |
|------|------|
| `search_torrents` | 搜索所有已知种子站，返回按季/画质归类的结果（缓存 10 分钟） |

## Resource

| URI | 说明 |
|-----|------|
| `youvedio://status` | 服务器状态和配置信息 |

## Agent 工作流

当用户说"我想看XXX"时，Agent 应该：

1. **解析名称** → 自己将缩写转为全称 (如 "RE0" → Re:Zero)
2. **搜索** → 用全称调用 `search_torrents`（**只用搜一次**，结果里包含所有季/画质/字幕组）
3. **先看 quality_summary** → 了解有哪些季、画质、字幕组可用，**不要换关键词重搜**
4. **检查 _unclassified 区** → 剧场版/OVA/SP 没有季度号，会出现在 `_unclassified` 里。检查其中的高画质（2160P/4K）和高做种项目，主动告知用户
5. **回复** → 自然语言格式：

```
[字幕组名] → 第X季 → 画质 (数量)
示例:
FBI → 第4季 → 4K (3个), 1080P (12个)
Erai-raws → 第4季 → 1080P (5个), 720P (2个)
```

## Git 规范

- **分支**: `main` → `dev` → `feat/xxx` → PR → `dev` → (发布) → `main`
- **提交**: Conventional Commits: `feat(scope): msg`, `fix(scope): msg`, `refactor(scope): msg`
- **范围** (scope): `nyaa`, `dmhy`, `engine`, `classifier`, `mcp`, `cli`, `scaffold`, `sources`, `storage`

## 代码风格

- Ruff lint + format (line-length=100)
- MyPy 类型检查 (渐进式, `check_untyped_defs`)
- pytest + asyncio 模式 (mock HTML, 不依赖网络)
- 类 PascalCase / 函数 snake_case / 文件小写+下划线

## 版本规划

详见 [ROADMAP.md](./ROADMAP.md)。当前版本 **v0.1.0** — MCP Server。

## 添加新站点流程

1. 在 `src/youvedio/sources/sites/` 下新建 `<name>.py`
2. 继承 `SiteParser`，实现 `search_url()` 和 `parse()` 方法
3. 在 `sources.json` 中注册
4. 运行 `ruff check . && mypy src/` 验证
