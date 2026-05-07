"""Tool registry for Maximus.ai - from ClawSpring pattern."""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from maximus.models import PermissionLevel, ToolMetadata
from maximus.tools.base import BaseTool


class ToolRegistry:
    """Runtime tool registration with safety metadata (ClawSpring pattern)."""

    def __init__(self):
        self._tools: Dict[str, tuple[BaseTool, ToolMetadata]] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool with its metadata."""
        name = tool.metadata.name
        self._tools[name] = (tool, tool.metadata)

        # Update category index
        for cat in tool.metadata.categories:
            if cat not in self._categories:
                self._categories[cat] = []
            if name not in self._categories[cat]:
                self._categories[cat].append(name)

    def unregister(self, name: str) -> None:
        """Remove a tool from registry."""
        if name in self._tools:
            _, metadata = self._tools[name]
            del self._tools[name]
            for cat in metadata.categories:
                if cat in self._categories and name in self._categories[cat]:
                    self._categories[cat].remove(name)

    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        entry = self._tools.get(name)
        return entry[0] if entry else None

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata by name."""
        entry = self._tools.get(name)
        return entry[1] if entry else None

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_by_category(self, category: str) -> List[str]:
        """List tools in a category."""
        return self._categories.get(category, [])

    def list_by_permission(self, level: PermissionLevel) -> List[str]:
        """List tools with given permission level."""
        return [
            name
            for name, (_, meta) in self._tools.items()
            if meta.permission_level == level
        ]

    def dispatch(
        self, name: str, args: Dict, context: Dict
    ) -> Dict[str, Any]:
        """Execute a tool by name with permission checks."""
        entry = self._tools.get(name)
        if not entry:
            return {"success": False, "error": f"Tool '{name}' not found"}

        tool, metadata = entry

        # Permission check
        security_ctx = context.get("security")
        if security_ctx and not security_ctx.has_permission(metadata.permission_level):
            return {"success": False, "error": "Permission denied", "type": "permission_denied"}

        # Local-only check
        if metadata.local_only and context.get("allow_external", False):
            return {"success": False, "error": "External calls not allowed", "type": "policy_violation"}

        return tool.execute(args, context)

    def to_schemas(self) -> List[Dict[str, Any]]:
        """Return all tool schemas for LLM tool calling."""
        return [tool.to_schema() for tool, _ in self._tools.values()]


# Global registry instance
registry = ToolRegistry()


def register_tool(tool: BaseTool) -> None:
    """Register a tool in the global registry."""
    registry.register(tool)


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return registry
