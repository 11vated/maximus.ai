"""Tools package for Maximus.ai."""

from maximus.tools.registry import ToolRegistry, registry, register_tool, get_registry
from maximus.tools.base import BaseTool, ToolMetadata

# Register builtin tools on import
from maximus.tools.builtin import register_builtin_tools

register_builtin_tools()
