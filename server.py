"""
Brave Search MCP Server
=======================
Wraps the Brave Search API as a Model Context Protocol server.
Mirrors the structure of server.ts + index.ts in the upstream TypeScript repo.

Usage
-----
stdio (default):
    python server.py

HTTP / SSE:
    BRAVE_MCP_TRANSPORT=http python server.py

Via CLI:
    python -m brave_mcp.cli serve --transport stdio
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp.server.fastmcp import FastMCP

from brave_mcp.config import Settings
from brave_mcp.service import BraveSearchService
from brave_mcp import tools


def create_server(settings: Settings) -> FastMCP:
    """Mirror of createMcpServer() in server.ts."""
    svc = BraveSearchService(settings)

    @asynccontextmanager
    async def _lifespan(server: FastMCP) -> AsyncGenerator[None, None]:
        yield
        await svc.aclose()

    mcp = FastMCP(
        "brave-search-mcp-server",
        instructions="Use this server to search the Web for various types of data via the Brave Search API.",
        lifespan=_lifespan,
    )

    tools.register(mcp, svc, settings)
    return mcp


if __name__ == "__main__":
    import logging
    import sys

    try:
        settings = Settings()
    except Exception as exc:
        from pydantic import ValidationError
        if isinstance(exc, ValidationError):
            for err in exc.errors():
                print(f"Configuration error: {err.get('msg', err)}", file=sys.stderr)
        else:
            print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    mcp = create_server(settings)

    if settings.transport == "http":
        print(
            f"brave-search-mcp-server starting "
            f"[http://{settings.host}:{settings.port}]",
            flush=True,
        )
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
