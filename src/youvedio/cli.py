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
def serve():
    """Start web UI server."""
    click.echo("Starting web server...")
    from youvedio.web import run_server

    run_server()
