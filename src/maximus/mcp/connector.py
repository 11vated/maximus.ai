"""MCP Connector for Maximus.

Handles connection lifecycle and discovery.
Uses the unified full MCP manager implementation.
"""
import logging
from typing import List

from maximus.mcp import get_mcp_manager
from maximus.mcp.manager import MCPServerConfig, TransportType

logger = logging.getLogger(__name__)


async def add_server(name: str, url: str) -> bool:
    """Add an MCP server by name and URL using the unified real implementation.
    
    Args:
        name: Unique identifier for the server
        url: MCP URL (e.g., 'github:///owner/repo')
        
    Returns:
        True if successful
    """
    manager = get_mcp_manager()
    try:
        if url.startswith("file://"):
            path = url.replace("file://", "") or "/"
            config = MCPServerConfig(
                name=name,
                command=["npx", "-y", "@modelcontextprotocol/server-filesystem", path],
                transport=TransportType.STDIO
            )
        else:
            config = MCPServerConfig(
                name=name,
                command=["npx", "-y", f"@modelcontextprotocol/server-{name}"],
                transport=TransportType.STDIO
            )
        manager.add_server(config)
        await manager.connect_server(name)
        return True
    except Exception as e:
        logger.error(f"Failed to add MCP server {name}: {e}")
        return False


def list_available_servers() -> List[str]:
    """List all available MCP server types."""
    return ["github", "filesystem", "brave-search"]


async def auto_discover_servers() -> List[str]:
    """Auto-discover common MCP servers using real manager."""
    manager = get_mcp_manager()
    discovered = []
    
    known = ["filesystem", "github", "brave-search"]
    for name in known:
        try:
            servers = manager.get_servers()
            if name not in [s["name"] for s in servers]:
                config = MCPServerConfig(
                    name=name,
                    command=["npx", "-y", f"@modelcontextprotocol/server-{name}"],
                    transport=TransportType.STDIO
                )
                manager.add_server(config)
                await manager.connect_server(name)
                discovered.append(name)
        except Exception as e:
            logger.warning(f"Failed to auto-discover {name}: {e}")
    
    return discovered
