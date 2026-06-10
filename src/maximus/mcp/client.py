"""MCP Client - unified to delegate to full real implementation (mocks removed)."""
from .manager import get_mcp_manager, MCPTool

# For compat, provide thin client that uses the manager
class MCPClient:
    def __init__(self):
        self._manager = get_mcp_manager()

    async def add_server(self, name: str, url: str) -> bool:
        from .connector import add_server as _add
        return await _add(name, url)

    async def _list_tools(self, server_name: str):
        return await self._manager.list_tools(server_name)

    async def call_tool(self, tool_name: str, arguments):
        # delegate
        return await self._manager.call_tool(tool_name.split('_')[1] if '_' in tool_name else tool_name, tool_name, arguments)

    def list_tool_names(self):
        return [t.name for t in self._manager.list_tools()]

    def get_tool_schema(self, name):
        for t in self._manager.list_tools():
            if t.name == name:
                return t.input_schema
        return None

_client = None
def get_mcp_client():
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
