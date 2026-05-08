"""MCP Tool Wrapper for Maximus.

Wraps MCP tools as standard Maximus tools.
"""
import logging
from typing import Any, Dict, List

from maximus.mcp.client import get_mcp_client

logger = logging.getLogger(__name__)


class MCPToolWrapper:
    """Wraps an MCP tool as a Maximus tool."""

    def __init__(self, name: str, schema: Dict[str, Any]):
        self.name = name
        self.schema = schema
        self.description = schema.get("description", f"MCP tool: {name}")

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the MCP tool."""
        client = get_mcp_client()
        
        try:
            result = await client.call_tool(self.name, params)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"MCP tool {self.name} failed: {e}")
            return {"success": False, "error": str(e)}


async def register_mcp_tools() -> List[str]:
    """Register all available MCP tools.
    
    Returns:
        List of registered tool names
    """
    client = get_mcp_client()
    registered = []
    
    for tool_name in client.list_tool_names():
        schema = client.get_tool_schema(tool_name)
        if schema:
            # In real implementation, this would register with the tool registry
            registered.append(tool_name)
            logger.info(f"Registered MCP tool: {tool_name}")
    
    return registered