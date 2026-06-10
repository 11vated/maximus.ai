"""MCP Tool Wrapper for Maximus.

Wraps MCP tools as standard Maximus tools.
"""
import logging
from typing import Any, Dict, List

from maximus.mcp import get_mcp_manager
from maximus.tools.base import BaseTool
from maximus.tools.registry import register_tool
from maximus.models import ToolMetadata, PermissionLevel

logger = logging.getLogger(__name__)


class MCPToolWrapper(BaseTool):
    """Wraps an MCP tool as a Maximus tool (inherits BaseTool for registry)."""

    def __init__(self, name: str, schema: Dict[str, Any], server_name: str = None):
        self.server_name = server_name or (name.split('_')[0] if '_' in name else None)
        metadata = ToolMetadata(
            name=f"mcp_{name}",
            description=schema.get("description", f"MCP tool: {name}"),
            read_only=False,
            concurrent_safe=True,
            permission_level=PermissionLevel.USER_APPROVAL,
            local_only=True,
            categories=["mcp", "external"],
        )
        super().__init__(metadata)
        self.schema = schema

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the MCP tool via unified manager."""
        manager = get_mcp_manager()
        try:
            tool_name = self.metadata.name.replace("mcp_", "")
            if self.server_name:
                result = await manager.call_tool(self.server_name, tool_name, params)
            else:
                result = await manager.call_tool("default", tool_name, params)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"MCP tool {self.metadata.name} failed: {e}")
            return {"success": False, "error": str(e)}


async def register_mcp_tools() -> List[str]:
    """Register all available MCP tools.
    
    Returns:
        List of registered tool names
    """
    manager = get_mcp_manager()
    registered = []
    
    try:
        tools = manager.get_all_tools() if hasattr(manager, 'get_all_tools') else manager.list_tools()
        for tool in tools:
            if isinstance(tool, dict):
                name = tool.get("name", "unknown")
                schema = tool
            else:
                name = getattr(tool, 'name', str(tool))
                schema = getattr(tool, 'input_schema', {}) or {}
            wrapper = MCPToolWrapper(name, schema)
            register_tool(wrapper)
            registered.append(wrapper.metadata.name)
            logger.info(f"Registered MCP tool: {wrapper.metadata.name}")
    except Exception as e:
        logger.warning(f"MCP tool registration skipped: {e}")
    
    return registered