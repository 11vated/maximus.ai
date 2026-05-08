"""MCP (Model Context Protocol) integration for Maximus UOSA."""

from maximus.mcp.mcp_manager import (
    MCPManager,
    MCPServer,
    MCPTool,
    MCPClient,
    get_mcp_manager,
)

__all__ = [
    "MCPManager",
    "MCPServer", 
    "MCPTool",
    "MCPClient",
    "get_mcp_manager",
]