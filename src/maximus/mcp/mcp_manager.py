"""MCP (Model Context Protocol) Integration for Maximus UOSA.

This enables Maximus to:
- Discover available MCP servers
- Connect to MCP tools dynamically
- Use MCP tools in the agent loop
- Auto-install MCP servers when needed
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import subprocess
import os

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """An MCP tool definition."""
    name: str
    description: str
    server_name: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert to tool schema for LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema
        }


@dataclass
class MCPServer:
    """An MCP server instance."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    status: str = "stopped"  # stopped, starting, running, error
    tools: List[MCPTool] = field(default_factory=list)
    process: Optional[subprocess.Popen] = None
    
    @property
    def is_running(self) -> bool:
        return self.status == "running" and self.process is not None


class MCPClient:
    """Client for communicating with MCP servers via JSON-RPC."""
    
    def __init__(self, server: MCPServer):
        self.server = server
        self._request_id = 0
        
    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with MCP server."""
        # In a real implementation, this would use stdin/stdout JSON-RPC
        # For now, we'll simulate the protocol
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": self.server.name,
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {}
            }
        }
    
    async def list_tools(self) -> List[MCPTool]:
        """List available tools from the server."""
        # Simulate tool listing - in production, this would be JSON-RPC
        return self.server.tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool."""
        # Simulate tool call - in production, this would be JSON-RPC
        logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
        
        return {
            "success": True,
            "content": f"Tool {tool_name} executed successfully"
        }
    
    async def close(self):
        """Close the connection."""
        if self.server.process:
            self.server.process.terminate()
            self.server.status = "stopped"


class MCPManager:
    """Manages MCP servers and tools for Maximus.
    
    This is the core of the MCP integration - it:
    - Maintains a list of available MCP servers
    - Starts/stops servers as needed
    - Provides tools to the agent loop
    - Auto-discovers servers from common locations
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.clients: Dict[str, MCPClient] = {}
        
        # Known MCP servers (built-in)
        self._known_servers = {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                "description": "File system operations"
            },
            "github": {
                "command": "npx", 
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "description": "GitHub API operations"
            },
            "brave-search": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "description": "Web search"
            }
        }
    
    async def initialize(self):
        """Initialize MCP manager and discover available servers."""
        logger.info("Initializing MCP Manager")
        
        # Auto-discover servers from environment
        await self._discover_servers()
        
        # Load user-configured servers
        await self._load_user_servers()
        
        logger.info(f"MCP Manager initialized with {len(self.servers)} servers")
    
    async def _discover_servers(self):
        """Auto-discover MCP servers from common locations."""
        # Check for MCP_CONFIG environment variable
        mcp_config = os.environ.get("MCP_CONFIG")
        if mcp_config and Path(mcp_config).exists():
            await self._load_config(mcp_config)
        
        # Check for ~/.mcp/servers.json
        mcp_dir = Path.home() / ".mcp"
        if mcp_dir.exists():
            servers_file = mcp_dir / "servers.json"
            if servers_file.exists():
                await self._load_config(str(servers_file))
    
    async def _load_config(self, config_path: str):
        """Load MCP server configuration."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            for name, server_config in config.get("servers", {}).items():
                await self.add_server(
                    name=name,
                    command=server_config.get("command", ""),
                    args=server_config.get("args", []),
                    env=server_config.get("env", {})
                )
        except Exception as e:
            logger.warning(f"Failed to load MCP config: {e}")
    
    async def _load_user_servers(self):
        """Load user-configured servers from Maximus config."""
        # Check for maximus MCP config
        config_dir = Path.home() / ".maximus"
        mcp_file = config_dir / "mcp_servers.json"
        
        if mcp_file.exists():
            try:
                with open(mcp_file, 'r') as f:
                    servers = json.load(f)
                    
                for name, config in servers.items():
                    await self.add_server(
                        name=name,
                        command=config.get("command", ""),
                        args=config.get("args", []),
                        env=config.get("env", {})
                    )
            except Exception as e:
                logger.warning(f"Failed to load user MCP servers: {e}")
    
    async def add_server(
        self,
        name: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None
    ) -> bool:
        """Add and start an MCP server."""
        if args is None:
            args = []
        if env is None:
            env = {}
        
        server = MCPServer(
            name=name,
            command=command,
            args=args,
            env=env
        )
        
        self.servers[name] = server
        logger.info(f"Added MCP server: {name}")
        
        # Try to start the server
        return await self.start_server(name)
    
    async def start_server(self, name: str) -> bool:
        """Start an MCP server."""
        server = self.servers.get(name)
        if not server:
            logger.error(f"Server not found: {name}")
            return False
        
        if server.is_running:
            return True
        
        try:
            server.status = "starting"
            
            # Start the process
            process = await asyncio.create_subprocess_exec(
                server.command,
                *server.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **server.env}
            )
            
            server.process = process
            
            # Wait a moment for startup
            await asyncio.sleep(1)
            
            # Check if it's running
            if process.returncode is not None and process.returncode != 0:
                server.status = "error"
                logger.error(f"MCP server {name} failed to start")
                return False
            
            # Initialize the client
            client = MCPClient(server)
            await client.initialize()
            
            # Get tools
            server.tools = await client.list_tools()
            self.clients[name] = client
            
            server.status = "running"
            logger.info(f"MCP server {name} started with {len(server.tools)} tools")
            return True
            
        except Exception as e:
            server.status = "error"
            logger.error(f"Failed to start MCP server {name}: {e}")
            return False
    
    async def stop_server(self, name: str):
        """Stop an MCP server."""
        server = self.servers.get(name)
        if not server:
            return
        
        client = self.clients.get(name)
        if client:
            await client.close()
            del self.clients[name]
        
        if server.process:
            server.process.terminate()
            server.process = None
        
        server.status = "stopped"
        logger.info(f"MCP server {name} stopped")
    
    def get_all_tools(self) -> List[MCPTool]:
        """Get all available MCP tools from all servers."""
        tools = []
        for server in self.servers.values():
            if server.is_running:
                tools.extend(server.tools)
        return tools
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas in LLM-compatible format."""
        schemas = []
        for tool in self.get_all_tools():
            schemas.append(tool.to_schema())
        return schemas
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a specific MCP server."""
        client = self.clients.get(server_name)
        if not client:
            return {"success": False, "error": f"Server not connected: {server_name}"}
        
        try:
            return await client.call_tool(tool_name, arguments)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers."""
        return {
            "total_servers": len(self.servers),
            "running": sum(1 for s in self.servers.values() if s.is_running),
            "servers": {
                name: {
                    "status": server.status,
                    "tools": len(server.tools),
                    "command": f"{server.command} {' '.join(server.args[:2])}..."
                }
                for name, server in self.servers.items()
            }
        }
    
    async def auto_discover_and_connect(self, task: str) -> List[MCPTool]:
        """Automatically discover and connect to MCP servers needed for a task.
        
        This is the Forage-style autonomous discovery.
        """
        needed_servers = []
        
        # Simple keyword matching for server selection
        task_lower = task.lower()
        
        if "file" in task_lower or "read" in task_lower or "write" in task_lower:
            if "filesystem" not in self.servers:
                needed_servers.append("filesystem")
        
        if "github" in task_lower or "git" in task_lower:
            if "github" not in self.servers:
                needed_servers.append("github")
        
        if "search" in task_lower or "web" in task_lower:
            if "brave-search" not in self.servers:
                needed_servers.append("brave-search")
        
        # Start needed servers
        for server_name in needed_servers:
            if server_name in self._known_servers:
                config = self._known_servers[server_name]
                await self.add_server(
                    name=server_name,
                    command=config["command"],
                    args=config["args"]
                )
        
        return self.get_all_tools()


# Global MCP manager instance
_mcp_manager: Optional[MCPManager] = None

def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager instance."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager