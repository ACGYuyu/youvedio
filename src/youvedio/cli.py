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
    from youvedio.mcp_server import server

    if transport == "sse":
        click.echo("Starting MCP server (SSE) on http://0.0.0.0:8000", err=True)
    else:
        click.echo("Starting MCP server (stdio) \u2014 connect via Claude Desktop", err=True)
    # Use if/else instead of casting
    if transport == "sse":
        server.run(transport="sse")
    else:
        server.run(transport="stdio")
