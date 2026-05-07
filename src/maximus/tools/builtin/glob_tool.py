"""Glob tool - pattern matching for file paths."""

import logging
from pathlib import Path
from typing import Any, Dict, List

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class GlobTool(BaseTool):
    """Find files matching a pattern."""

    def __init__(self):
        metadata = ToolMetadata(
            name="glob",
            description="Find files matching a glob pattern (e.g., '**/*.py').",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["file", "search", "read"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        pattern = args.get("pattern", "**/*")
        path = args.get("path", ".")

        workdir = Path(context.get("workdir", "."))
        search_path = workdir / path

        try:
            results = [str(p) for p in search_path.glob(pattern) if p.is_file()]
            return {"success": True, "results": results[:100], "count": len(results)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (default: **/*)"},
                "path": {"type": "string", "description": "Search directory (default: current)"},
            },
            "required": [],
        }
