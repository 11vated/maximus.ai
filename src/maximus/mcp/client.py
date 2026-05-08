"""MCP (Model Context Protocol) Client for Maximus.

Provides integration with MCP servers for extended tool capabilities.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to MCP servers."""

    def __init__(self):
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}

    async def add_server(self, name: str, url: str) -> bool:
        """Add and connect to an MCP server.
        
        Args:
            name: Unique name for the server
            url: MCP server URL (e.g., 'github:///path/to/server')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse URL scheme
            parsed = self._parse_url(url)
            
            # Initialize server connection
            self.servers[name] = {
                "url": url,
                "parsed": parsed,
                "tools": [],
            }
            
            # Register tools
            tools = await self._list_tools(name)
            self.tools.update({f"mcp_{name}_{t['name']}": t for t in tools})
            
            logger.info(f"Added MCP server '{name}' with {len(tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add MCP server {name}: {e}")
            return False

    def _parse_url(self, url: str) -> Dict[str, str]:
        """Parse MCP URL into components."""
        # github:///owner/repo?ref=main
        # npm:///package-name
        # file:///path/to/server.py
        
        parts = url.split("://", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid MCP URL: {url}")
        
        scheme = parts[0]
        path = parts[1]
        
        return {
            "scheme": scheme,
            "path": path,
            "ref": None,
        }

    async def _list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List tools available from an MCP server."""
        # For now, return mock tools based on server type
        # Real implementation would connect to the actual server
        
        server = self.servers.get(server_name, {})
        parsed = server.get("parsed", {})
        scheme = parsed.get("scheme", "")
        
        mock_tools = {
            "github": [
                {"name": "create_issue", "description": "Create a GitHub issue"},
                {"name": "list_repos", "description": "List repositories"},
                {"name": "create_pull_request", "description": "Create a pull request"},
            ],
            "npm": [
                {"name": "search", "description": "Search npm packages"},
                {"name": "install", "description": "Install package"},
            ],
            "file": [
                {"name": "read_file", "description": "Read file contents"},
                {"name": "write_file", "description": "Write file contents"},
            ],
        }
        
        return mock_tools.get(scheme, [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool."""
        # Extract server prefix from tool name
        parts = tool_name.split("_", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid tool name: {tool_name}")
        
        server_name = parts[1]
        actual_tool = parts[2]
        
        # Mock implementation - real would call the server
        return f"Called {actual_tool} on server {server_name} with {arguments}"

    def list_tool_names(self) -> List[str]:
        """List all available MCP tool names."""
        return list(self.tools.keys())

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for an MCP tool."""
        return self.tools.get(tool_name)


# Global MCP client instance
_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create the global MCP client."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client