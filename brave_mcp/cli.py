from __future__ import annotations

import os

import click

from .config import AVAILABLE_TOOLS, Settings


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--api-key", envvar="BRAVE_API_KEY", help="Brave Search API key")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default=None,
    envvar="BRAVE_MCP_TRANSPORT",
    help="Transport mode (default: stdio)",
)
@click.option("--port", type=int, default=None, envvar="BRAVE_MCP_PORT", help="HTTP port")
@click.option("--host", default=None, envvar="BRAVE_MCP_HOST", help="HTTP host")
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default=None,
    envvar="BRAVE_MCP_LOG_LEVEL",
)
@click.option(
    "--enabled-tools",
    default=None,
    envvar="BRAVE_MCP_ENABLED_TOOLS",
    help=f"Space-separated whitelist. Available: {', '.join(AVAILABLE_TOOLS)}",
)
@click.option(
    "--disabled-tools",
    default=None,
    envvar="BRAVE_MCP_DISABLED_TOOLS",
    help="Space-separated blacklist (mutually exclusive with --enabled-tools)",
)
@click.option("--stateless", is_flag=True, default=None, envvar="BRAVE_MCP_STATELESS")
def serve(
    api_key: str | None,
    transport: str | None,
    port: int | None,
    host: str | None,
    log_level: str | None,
    enabled_tools: str | None,
    disabled_tools: str | None,
    stateless: bool | None,
) -> None:
    """Start the Brave Search MCP server."""
    # CLI flags override env vars by writing back into the environment so
    # Settings (pydantic-settings) picks them up uniformly.
    if api_key:
        os.environ["BRAVE_API_KEY"] = api_key
    if transport:
        os.environ["BRAVE_MCP_TRANSPORT"] = transport
    if port is not None:
        os.environ["BRAVE_MCP_PORT"] = str(port)
    if host:
        os.environ["BRAVE_MCP_HOST"] = host
    if log_level:
        os.environ["BRAVE_MCP_LOG_LEVEL"] = log_level
    if enabled_tools:
        os.environ["BRAVE_MCP_ENABLED_TOOLS"] = enabled_tools
    if disabled_tools:
        os.environ["BRAVE_MCP_DISABLED_TOOLS"] = disabled_tools
    if stateless:
        os.environ["BRAVE_MCP_STATELESS"] = "true"

    from server import create_server  # local import to avoid circular init

    settings = Settings()
    mcp = create_server(settings)

    click.echo(
        f"Starting brave-search-mcp-server "
        f"[transport={settings.transport}, "
        f"log_level={settings.log_level}]",
        err=True,
    )

    if settings.transport == "http":
        click.echo(f"Listening on {settings.host}:{settings.port}", err=True)
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
