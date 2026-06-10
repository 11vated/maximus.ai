"""MCP (Model Context Protocol) integration for Maximus UOSA."""

from .manager import (
    MCPManager,
    MCPTool,
    MCPServerConfig,
    TransportType,
    get_mcp_manager,
)

__all__ = [
    "MCPManager",
    "MCPTool",
    "MCPServerConfig",
    "TransportType",
    "get_mcp_manager",
]