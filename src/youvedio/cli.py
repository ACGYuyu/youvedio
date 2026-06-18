"""CLI entry point."""

import click


@click.group()
def cli():
    """YouVedio - 多语言种子/磁力搜索引擎"""


@cli.command()
def version():
    """Show version."""
    click.echo("YouVedio v0.1.0")


@cli.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="MCP transport (default: stdio for Claude Desktop)",
)
def mcp(transport: str):
    """Start MCP server for LLM agent integration."""
    from youvedio.config import settings
    from youvedio.mcp_server import server

    if transport == "sse":
        server.settings.host = settings.server_host
        server.settings.port = settings.server_port
        addr = f"{settings.server_host}:{settings.server_port}"
        click.echo(f"Starting MCP server (SSE) on http://{addr}", err=True)
        server.run(transport="sse")
    else:
        click.echo("Starting MCP server (stdio) \u2014 connect via Claude Desktop", err=True)
        server.run(transport="stdio")
