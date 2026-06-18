# YouVedio

种子/磁力搜索引擎 MCP Server。并发爬取多个种子站，按季/画质/字幕组归类结果，通过 MCP 协议暴露给 LLM Agent。

## 功能特性

- **多站并发** — 同时爬取 7 个种子站（Nyaa、动漫花园、蜜柑计划、1337x、ACG.RIP、AniDEX、TokyoTosho）
- **反爬绕过** — 基于 Scrapling，自动处理 Cloudflare 等反爬机制
- **智能分类** — 正则提取季数/画质/字幕组，按最新季→最高清排序
- **本地缓存** — 10 分钟 TTL，相同关键词秒回
- **MCP 协议** — 标准 Model Context Protocol，兼容 Claude Desktop / OpenCode 等客户端

## 快速开始

### 安装

```bash
pip install -e ".[dev]"
pre-commit install
```

### 配置

复制 `.env.example` 为 `.env`，填入代理等配置：

```bash
cp .env.example .env
```

如果网络在代理后，可在 `.env` 中设置或通过环境变量：

```bash
$env:HTTP_PROXY="http://127.0.0.1:10808"
$env:HTTPS_PROXY="http://127.0.0.1:10808"
```

### 启动 MCP Server

```bash
# stdio 模式（Claude Desktop / OpenCode）
py -3.12 -m youvedio mcp

# SSE 模式（HTTP 远程访问）
py -3.12 -m youvedio mcp --transport sse
```

## 安装到你的 MCP 客户端

以下步骤也可让 Agent 自动执行。

### 方式一：stdio 模式（本地，推荐）

MCP 服务器作为本地子进程运行，通过标准输入输出通信。

**安装 Skill：**

```bash
# 将本项目 skill 复制到你的全局 skill 目录
cp -r .opencode/skills/youvedio-torrent-search ~/.config/opencode/skills/
```

**OpenCode 配置（`opencode.json`）：**

```json
{
  "mcp": {
    "youvedio": {
      "type": "local",
      "command": ["py", "-3.12", "-m", "youvedio", "mcp"],
      "environment": {
        "HTTP_PROXY": "{env:HTTP_PROXY}"
      }
    }
  }
}
```

**Claude Desktop 配置（`claude_desktop_config.json`）：**

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

### 方式二：SSE 模式（远程部署）

MCP 服务器部署在远程服务器上，通过 HTTP 访问。

**启动服务器：**

```bash
py -3.12 -m youvedio mcp --transport sse
# 默认监听 http://0.0.0.0:8000
```

**OpenCode 配置（`opencode.json`）：**

```json
{
  "mcp": {
    "youvedio": {
      "type": "remote",
      "url": "http://your-server:8000/sse"
    }
  }
}
```

**Claude Desktop 配置（`claude_desktop_config.json`）：**

```json
{
  "mcpServers": {
    "youvedio": {
      "type": "sse",
      "url": "http://your-server:8000/sse"
    }
  }
}
```

> SSE 模式需要服务器有公网 IP 或内网穿透。如果服务器有防火墙，需开放 8000 端口。

### 验证连接

启动客户端后，Agent 应能看到 `search_torrents` 工具和 `youvedio://status` 资源。
opencode
```

Agent 会自动加载 MCP 工具和 skill，然后你可以直接说"我想看XXX"。

### Claude Desktop 配置（备选）

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

## MCP 工具

### `search_torrents(keyword)`

搜索所有种子站，返回按季/画质归类的结果。结果自动缓存 10 分钟。

**返回格式：**

```json
{
  "keyword": "Re:Zero",
  "total": 155,
  "sites_success": 5,
  "sites_failed": 2,
  "seasons": {
    "S04": {
      "1080P": [
        {"title": "...", "magnet": "magnet:?...", "seeders": 1348, "subgroup": "Erai-raws", "size": "1.4 GiB"}
      ]
    }
  },
  "quality_summary": {
    "S04": {
      "2160P": {"total": 3, "subgroups": ["Feibanyama"], "has_batch": false, "has_single_episodes": true},
      "1080P": {"total": 51, "subgroups": ["Erai-raws", "FBI"], "has_batch": false}
    }
  }
}
```

| 字段 | 说明 |
|------|------|
| `seasons` | 按季→画质分组的完整结果 |
| `quality_summary` | 快速概览：有哪些画质、字幕组、是否有合集包 |
| `_unclassified` | 剧场版/OVA/SP（无季度号时出现于此） |

### Resource

| URI | 说明 |
|-----|------|
| `youvedio://status` | 服务器状态和已配置的站点列表 |

## 开发指南

### 环境

```bash
git clone <repo> && cd youvedio
pip install -e ".[dev]"
pre-commit install
cp .env.example .env
```

项目根目录的 `opencode.json` 已配置好 MCP 服务器和 AGENTS.md 指令，OpenCode 启动后自动加载。

### 开发循环

```bash
ruff check . && ruff format . && mypy src/ && pytest -v
```

因默认 Python 可能不是 3.12，可使用：

```bash
py -3.12 -m ruff check .
py -3.12 -m mypy src/
py -3.12 -m pytest -v
```

### 代码风格

| 规则 | 约定 |
|------|------|
| Lint + Format | Ruff (line-length=100) |
| 类型检查 | MyPy (渐进式) |
| 测试 | pytest + asyncio 模式，109 个测试，81% 覆盖率 |
| 命名 | 类 `PascalCase` / 函数 `snake_case` / 文件小写+下划线 |
| 提交 | Conventional Commits: `feat(scope): msg` |

### 分支策略

```
main       ← 稳定分支
  dev      ← 开发主分支
    feat/xxx    ← 功能分支
    fix/xxx     ← 修复分支
    refactor/xxx ← 重构分支
```

PR 流程: `feat/xxx` → PR → `dev` → (发布) → `main`

## 项目结构

```
src/youvedio/
├── mcp_server.py            # MCP 服务入口
├── sources/
│   ├── manager.py           # 站点注册与发现
│   └── sites/               # 站点解析器（每站一个文件）
│       ├── base.py          # 解析器基类
│       ├── nyaa.py          # Nyaa.si
│       ├── dmhy.py          # 动漫花园
│       ├── mikan.py         # 蜜柑计划
│       ├── x1337.py         # 1337x.to
│       ├── acgrip.py        # ACG.RIP
│       ├── anidex.py        # AniDEX
│       └── tokyotosho.py    # TokyoTosho
├── crawler/
│   ├── engine.py            # Scrapling 爬虫引擎（并发）
│   └── classifier.py        # 季/画质/字幕组分类器
├── storage/
│   └── cache.py             # 本地缓存（TTL 10分钟）
├── models.py                # 数据模型
└── config.py                # .env 配置
```

## 添加新站点

1. 在 `src/youvedio/sources/sites/` 下新建 `yoursite.py`：

```python
from youvedio.models import TorrentResult
from youvedio.sources.sites.base import SiteParser

class YourSiteParser(SiteParser):
    name = "yoursite.com"
    base_url = "https://yoursite.com"
    lang = "en"

    def search_url(self, keyword: str) -> str:
        return f"{self.base_url}/search?q={keyword}"

    def parse(self, html: str, source=None) -> list[TorrentResult]:
        from scrapling.parser import Selector
        doc = Selector(html)
        # 使用 self.css_text / self.css_attr 提取数据
```

2. 在 `sources.json` 中注册：

```json
{"name": "yoursite.com", "url": "https://yoursite.com", "lang": "en", "enabled": true}
```

3. 验证：

```bash
ruff check . && mypy src/
```

解析器会自动注册，`search_torrents` 会自动包含新站点。

## 技术栈

- **Python** 3.12+（推荐 3.12，避免 3.15 alpha）
- **Scrapling** — 网页爬取与反爬绕过
- **MCP Python SDK** — Model Context Protocol 实现
- **Ruff / MyPy / pytest** — 代码质量

## 许可证

MIT
