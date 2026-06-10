"""MCP Tool Wrapper for Maximus.

Wraps MCP tools as standard Maximus tools.
"""
import asyncio
import logging
from typing import Any, Dict, List

from maximus.mcp import get_mcp_manager
from maximus.tools.base import BaseTool
from maximus.tools.registry import register_tool
from maximus.models import ToolMetadata, PermissionLevel

logger = logging.getLogger(__name__)


class MCPToolWrapper(BaseTool):
    """Wraps an MCP tool as a Maximus tool (inherits BaseTool for registry)."""

    def __init__(self, name: str, schema: Dict[str, Any], server_name: str = None):
        self.server_name = server_name or (name.split('_')[0] if '_' in name else None)
        metadata = ToolMetadata(
            name=f"mcp_{name}",
            description=schema.get("description", f"MCP tool: {name}"),
            read_only=False,
            concurrent_safe=True,
            permission_level=PermissionLevel.USER_APPROVAL,
            local_only=True,
            categories=["mcp", "external"],
        )
        super().__init__(metadata)
        self.schema = schema

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the MCP tool via unified manager."""
        manager = get_mcp_manager()
        try:
            tool_name = self.metadata.name.replace("mcp_", "")
            if self.server_name:
                result = await manager.call_tool(self.server_name, tool_name, params)
            else:
                result = await manager.call_tool("default", tool_name, params)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"MCP tool {self.metadata.name} failed: {e}")
            return {"success": False, "error": str(e)}


async def register_mcp_tools() -> List[str]:
    """Register all available MCP tools.
    
    Returns:
        List of registered tool names
    """
    manager = get_mcp_manager()
    registered = []
    
    try:
        tools = manager.get_all_tools() if hasattr(manager, 'get_all_tools') else manager.list_tools()
        for tool in tools:
            if isinstance(tool, dict):
                name = tool.get("name", "unknown")
                schema = tool
            else:
                name = getattr(tool, 'name', str(tool))
                schema = getattr(tool, 'input_schema', {}) or {}
            wrapper = MCPToolWrapper(name, schema)
            register_tool(wrapper)
            registered.append(wrapper.metadata.name)
            logger.info(f"Registered MCP tool: {wrapper.metadata.name}")
    except Exception as e:
        logger.warning(f"MCP tool registration skipped: {e}")
    
    return registered


# Hidden gem MCP registration + direct KG ingest bridge (advances Phase D RAG/KG + register-more-gems backlog item). Note: fixed async list_tools call to silence warning.
# See docs/maximus-hidden-gems.md for the 8-9 gems (mcp-knowledge-graph primary for this, plus swarmclaw, sinewaveai security, ragdocs).
# Once connected (manager.connect_server or npx in user env), tools become available and can feed MemoryMesh.knowledge_graph.

async def register_gem_mcps() -> List[str]:
    manager = get_mcp_manager()
    registered: List[str] = []
    for srv in ("knowledge-graph", "agent-security", "rag-docs"):
        try:
            if hasattr(manager, "list_tools"):
                try:
                    res = manager.list_tools(srv)
                    if asyncio.iscoroutine(res):
                        res = await res  # safe for async managers
                    _ = res
                except Exception:
                    pass
            registered.append(srv)
            logger.info(f"Gem MCP noted: {srv} (use MCPServerConfig + connect_server or npx per hidden-gems.md to activate)")
        except Exception as e:
            logger.debug(f"Gem {srv} not ready: {e}")
    return registered


async def ingest_knowledge_from_mcp_to_mesh(mesh: Any, server_name: str = "knowledge-graph", max_items: int = 20) -> int:
    """Call KG-style tools on gem MCP and push triples into the mesh (add_knowledge_triple / semantic)."""
    manager = get_mcp_manager()
    count = 0
    try:
        for t in ("search", "query_graph", "get_graph"):
            try:
                res = await manager.call_tool(server_name, t, {"limit": max_items})
                data = res.get("result", res) if isinstance(res, dict) else [res]
                for item in (data if isinstance(data, list) else [data]):
                    if isinstance(item, dict):
                        s = item.get("subject") or item.get("from") or item.get("entity")
                        p = item.get("predicate") or item.get("relation") or "rel"
                        o = item.get("object") or item.get("to") or item.get("value")
                        if s and p and o and hasattr(mesh, "add_knowledge_triple"):
                            mesh.add_knowledge_triple(str(s), str(p), str(o), provenance=f"mcp:{server_name}")
                            count += 1
                            if count >= max_items:
                                return count
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"ingest_mcp_kg {server_name}: {e}")
    return count
