"""MCP (Model Context Protocol) manager - unified to use full real implementation.

This file now delegates to the full manager.py to remove mocks and consolidate.
"""
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
