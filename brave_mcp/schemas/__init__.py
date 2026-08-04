"""Schema package — base classes are re-exported; group modules import from _base."""

from ._base import ToolError, ToolResult

__all__ = ["ToolError", "ToolResult"]
