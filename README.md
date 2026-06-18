# YouVedio

种子/磁力搜索引擎 MCP Server。并发爬取多个种子站，按季/画质/字幕组归类结果，通过 MCP 协议暴露给 LLM Agent。

## 功能特性

- **多站并发** — 同时爬取 7 个种子站（Nyaa、动漫花园、蜜柑计划、1337x、ACG.RIP、AniDEX、TokyoTosho）
- **反爬绕过** — 基于 Scrapling，自动处理 Cloudflare 等反爬机制
- **智能分类** — 正则提取季数/画质/字幕组，按最新季→最高清排序
- **本地缓存** — 10 分钟 TTL，相同关键词秒回
- **MCP 协议** — 标准 Model Context Protocol，兼容 Claude Desktop / OpenCode 等客户端
- **可扩展** — 新增站点只需写一个解析器文件

## 快速开始

### 安装

```bash
pip install -e ".[dev]"
pre-commit install
```

### 配置

复制 `.env.example` 为 `.env`，填入配置（主要是代理）：

```bash
cp .env.example .env
```

如果网络在代理后：

```bash
# 在 .env 中设置，或终端环境变量：
$env:HTTP_PROXY="http://127.0.0.1:10808"
$env:HTTPS_PROXY="http://127.0.0.1:10808"
```

### 启动 MCP Server

```bash
# stdio 模式（Claude Desktop）
py -3.12 -m youvedio mcp

# SSE 模式（HTTP 远程访问）
py -3.12 -m youvedio mcp --transport sse
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

- `seasons` — 按季→画质分组的完整结果
- `quality_summary` — 快速概览，告诉 Agent 有哪些画质、字幕组、是否有合集包

### Resource

| URI | 说明 |
|-----|------|
| `youvedio://status` | 服务器状态和已配置的站点列表 |

## 项目结构

```
src/youvedio/
├── mcp_server.py            # MCP 服务入口
├── sources/
│   ├── manager.py           # 站点注册与发现
│   ├── discoverer.py        # 搜索引擎发现新站点
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
        # ...
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

## 使用 OpenCode 开发

```bash
# 1. 克隆
git clone <repo> && cd youvedio

# 2. 安装
pip install -e ".[dev]"
pre-commit install
cp .env.example .env        # 编辑 .env 配置代理

# 3. 启动 MCP Server（终端1）
py -3.12 -m youvedio mcp

# 4. 启动 OpenCode（终端2，项目目录下）
opencode

# 5. 开发循环
# 改代码 → ruff check && format && mypy && pytest
```

项目根目录的 `opencode.json` 已配置好 MCP 服务器和开发指令，OpenCode 启动后会自动加载。

### 提交规范

```
feat(nyaa): add season/quality classifier for nyaa.si parser
fix(dmhy): handle missing seeders field
refactor(engine): extract base fetcher class
test(classifier): add season extraction tests
docs: update README with installation guide
```

### 分支策略

```
main       ← 稳定分支
  dev      ← 开发主分支
    feat/xxx    ← 功能分支
    fix/xxx     ← 修复分支
    refactor/xxx ← 重构分支
```

PR 流程: `feat/xxx` → PR → `dev` → (发布) → `main`

## 技术栈

- **Python** 3.12+（推荐 3.12）
- **Scrapling** — 网页爬取与反爬绕过
- **MCP Python SDK** — Model Context Protocol 实现
- **httpx** — AI API 调用
- **Ruff / MyPy / pytest** — 代码质量

## 许可证

MIT
