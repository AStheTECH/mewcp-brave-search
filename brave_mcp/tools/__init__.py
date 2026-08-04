"""MewCP Brave Search tool registration."""

from fastmcp import FastMCP

from .search_tools import register_search_tools


def register_tools(mcp: FastMCP) -> None:
    register_search_tools(mcp)
