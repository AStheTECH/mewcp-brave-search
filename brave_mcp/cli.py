"""argparse: --transport / --host / --port."""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Brave Search MCP Server")
    parser.add_argument(
        "-t", "--transport",
        choices=["stdio", "streamable-http"],
        default=None,
        help="Transport mode (default: streamable-http)",
    )
    parser.add_argument("--host", default=None, help="Bind address")
    parser.add_argument("--port", type=int, default=None, help="Listen port")
    return parser.parse_args()
