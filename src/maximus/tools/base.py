"""Base tool interface for Maximus.ai."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from maximus.models import Event, EventType, ToolMetadata


class BaseTool(ABC):
    """Abstract base class for all tools (from Nexus + ClawSpring hybrid)."""

    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata

    @abstractmethod
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given arguments.

        Args:
            args: Tool-specific arguments.
            context: Execution context (workdir, env, security, etc.).

        Returns:
            Dict with 'success', 'output', and optional 'error'.
        """
        ...

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def description(self) -> str:
        return self.metadata.description

    def to_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool (for LLM tool calling)."""
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "parameters": self._get_parameters_schema(),
            "local_only": self.metadata.local_only,
            "permission_level": self.metadata.permission_level.value,
        }

    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Override in subclasses to provide parameter schema."""
        return {"type": "object", "properties": {}, "required": []}
