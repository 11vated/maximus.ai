"""MCP Connector for Maximus.

Handles connection lifecycle and discovery.
"""
import logging
from typing import List

from maximus.mcp.client import get_mcp_client

logger = logging.getLogger(__name__)


async def add_server(name: str, url: str) -> bool:
    """Add an MCP server by name and URL.
    
    Args:
        name: Unique identifier for the server
        url: MCP URL (e.g., 'github:///owner/repo')
        
    Returns:
        True if successful
    """
    client = get_mcp_client()
    return await client.add_server(name, url)


def list_available_servers() -> List[str]:
    """List all available MCP server types."""
    return ["github://", "npm://", "file://"]


async def auto_discover_servers() -> List[str]:
    """Auto-discover common MCP servers."""
    # Discover popular servers
    discovered = []
    
    # Common GitHub repos with MCP servers
    github_servers = [
        ("github", "github:///modelcontextprotocol/servers"),
        ("filesystem", "file:///"),
        ("sqlite", "github:///modelcontextprotocol/servers/sqlite"),
    ]
    
    for name, url in github_servers:
        try:
            if await add_server(name, url):
                discovered.append(name)
        except Exception as e:
            logger.warning(f"Failed to auto-discover {name}: {e}")
    
    return discovered