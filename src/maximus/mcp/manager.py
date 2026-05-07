"""MCP (Model Context Protocol) manager for Maximus.ai - Full implementation.

Implements:
- JSON-RPC 2.0 protocol
- Stdio transport for local servers
- HTTP/SSE transport for remote servers
- Tool discovery and execution
- Server lifecycle management
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncGenerator
from pathlib import Path

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TransportType(str, Enum):
    """MCP transport types."""
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class MCPTool(BaseModel):
    """A tool exposed via MCP."""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    name: str
    command: List[str] = field(default_factory=list)
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    transport: TransportType = TransportType.STDIO
    url: Optional[str] = None


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 request."""
    method: str
    params: Optional[Dict[str, Any]] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    jsonrpc: str = "2.0"


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 response."""
    id: str
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"


class MCPTransport(ABC):
    """Base class for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass

    @abstractmethod
    async def send(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Send request and wait for response."""
        pass

    @abstractmethod
    async def send_notifications(self, request: JSONRPCRequest) -> None:
        """Send notification without waiting for response."""
        pass


class StdioTransport(MCPTransport):
    """Stdio transport for local MCP servers."""

    def __init__(self, command: List[str], env: Dict[str, str] = None):
        self.command = command
        self.env = env or {}
        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_queue: asyncio.Queue = None

    async def connect(self) -> None:
        """Start the MCP server process."""
        try:
            self._process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env
            )
            self._request_queue = asyncio.Queue()
            logger.info(f"Started MCP server: {' '.join(self.command)}")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise

    async def disconnect(self) -> None:
        """Terminate the MCP server process."""
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
            logger.info("MCP server terminated")

    async def send(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Send JSON-RPC request via stdin."""
        if not self._process or self._process.returncode is not None:
            raise RuntimeError("MCP server not running")

        request_json = json.dumps(request.dict()) + "\n"
        self._process.stdin.write(request_json.encode())
        await self._process.stdin.drain()

        response_line = await asyncio.wait_for(
            self._process.stdout.readline(),
            timeout=30.0
        )
        
        if not response_line:
            raise RuntimeError("MCP server closed connection")

        response_data = json.loads(response_line.decode())
        return JSONRPCResponse(**response_data)

    async def send_notifications(self, request: JSONRPCRequest) -> None:
        """Send notification without waiting for response."""
        if not self._process or self._process.returncode is not None:
            return

        request_json = json.dumps(request.dict()) + "\n"
        self._process.stdin.write(request_json.encode())
        await self._process.stdin.drain()


class HTTPTransport(MCPTransport):
    """HTTP transport for remote MCP servers."""

    def __init__(self, url: str, headers: Dict[str, str] = None):
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True
        )

    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def send(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Send JSON-RPC request via HTTP POST."""
        if not self._client:
            raise RuntimeError("HTTP client not connected")

        response = await self._client.post(
            f"{self.url}/rpc",
            json=request.dict()
        )
        response.raise_for_status()
        return JSONRPCResponse(**response.json())

    async def send_notifications(self, request: JSONRPCRequest) -> None:
        """Send notification via HTTP POST."""
        if not self._client:
            return

        try:
            await self._client.post(f"{self.url}/notify", json=request.dict())
        except Exception as e:
            logger.warning(f"Notification failed: {e}")


class MCPManager:
    """Full MCP manager with transport support."""

    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self._transports: Dict[str, MCPTransport] = {}
        self._tools_cache: Dict[str, List[MCPTool]] = {}
        self._capabilities_cache: Dict[str, Dict] = {}

    def add_server(self, config: MCPServerConfig) -> None:
        """Register an MCP server."""
        self.servers[config.name] = config
        self._tools_cache.pop(config.name, None)
        self._capabilities_cache.pop(config.name, None)

    def remove_server(self, name: str) -> None:
        """Remove an MCP server."""
        if name in self.servers:
            del self.servers[name]
        
        if name in self._transports:
            asyncio.create_task(self._transports[name].disconnect())
            del self._transports[name]
        
        self._tools_cache.pop(name, None)
        self._capabilities_cache.pop(name, None)

    async def connect_server(self, name: str) -> None:
        """Connect to a specific MCP server."""
        config = self.servers.get(name)
        if not config:
            raise ValueError(f"Server '{name}' not configured")

        # Create transport
        if config.transport == TransportType.STDIO:
            command = config.command + config.args
            transport = StdioTransport(command, config.env)
        elif config.transport in (TransportType.HTTP, TransportType.SSE):
            if not config.url:
                raise ValueError(f"Server '{name}' requires URL")
            transport = HTTPTransport(config.url)
        else:
            raise ValueError(f"Unknown transport: {config.transport}")

        await transport.connect()
        self._transports[name] = transport
        logger.info(f"Connected to MCP server: {name}")

    async def disconnect_all(self) -> None:
        """Disconnect all servers."""
        for transport in self._transports.values():
            await transport.disconnect()
        self._transports.clear()

    async def initialize_server(self, name: str) -> Dict[str, Any]:
        """Send initialize request to MCP server."""
        if name not in self._transports:
            await self.connect_server(name)

        transport = self._transports[name]
        
        request = JSONRPCRequest(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "maximus",
                    "version": "0.1.0"
                }
            }
        )

        response = await transport.send(request)
        
        if response.error:
            raise RuntimeError(f"Initialize failed: {response.error}")

        capabilities = response.result.get("capabilities", {})
        self._capabilities_cache[name] = capabilities
        return capabilities

    async def list_tools(self, server_name: Optional[str] = None) -> List[MCPTool]:
        """List tools from one or all MCP servers."""
        if server_name:
            return await self._fetch_tools(server_name)

        all_tools = []
        for name in self.servers:
            tools = await self._fetch_tools(name)
            all_tools.extend(tools)
        return all_tools

    async def _fetch_tools(self, server_name: str) -> List[MCPTool]:
        """Fetch tools from a specific MCP server."""
        if server_name in self._tools_cache:
            return self._tools_cache[server_name]

        # Ensure connected
        if server_name not in self._transports:
            try:
                await self.initialize_server(server_name)
            except Exception as e:
                logger.error(f"Failed to initialize {server_name}: {e}")
                return []

        transport = self._transports.get(server_name)
        if not transport:
            return []

        # Send tools/list request
        request = JSONRPCRequest(method="tools/list")
        
        try:
            response = await transport.send(request)
            
            if response.error:
                logger.error(f"tools/list failed: {response.error}")
                return []

            tools_data = response.result.get("tools", [])
            tools = [
                MCPTool(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {})
                )
                for t in tools_data
            ]
            
            self._tools_cache[server_name] = tools
            return tools
            
        except Exception as e:
            logger.error(f"Failed to fetch tools from {server_name}: {e}")
            return []

    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on an MCP server."""
        if server_name not in self._transports:
            await self.initialize_server(server_name)

        transport = self._transports.get(server_name)
        if not transport:
            raise ValueError(f"Server '{server_name}' not connected")

        request = JSONRPCRequest(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )

        response = await transport.send(request)
        
        if response.error:
            raise RuntimeError(f"Tool call failed: {response.error}")

        return response.result

    async def get_prompts(self, server_name: str) -> List[Dict]:
        """Get prompts from an MCP server."""
        if server_name not in self._transports:
            await self.initialize_server(server_name)

        transport = self._transports.get(server_name)
        if not transport:
            return []

        request = JSONRPCRequest(method="prompts/list")
        
        try:
            response = await transport.send(request)
            if response.result:
                return response.result.get("prompts", [])
        except Exception:
            pass
        return []

    async def get_resources(self, server_name: str) -> List[Dict]:
        """Get resources from an MCP server."""
        if server_name not in self._transports:
            await self.initialize_server(server_name)

        transport = self._transports.get(server_name)
        if not transport:
            return []

        request = JSONRPCRequest(method="resources/list")
        
        try:
            response = await transport.send(request)
            if response.result:
                return response.result.get("resources", [])
        except Exception:
            pass
        return []

    def get_servers(self) -> List[Dict[str, Any]]:
        """List all configured MCP servers."""
        return [
            {
                "name": name,
                "command": config.command,
                "transport": config.transport.value,
                "url": config.url,
                "timeout": config.timeout,
                "connected": name in self._transports,
            }
            for name, config in self.servers.items()
        ]

    def get_capabilities(self, server_name: str) -> Optional[Dict]:
        """Get server capabilities."""
        return self._capabilities_cache.get(server_name)