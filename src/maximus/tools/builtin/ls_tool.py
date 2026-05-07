"""List directory contents tool."""

import logging
from pathlib import Path
from typing import Any, Dict, List

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class LsTool(BaseTool):
    """List files and directories."""

    def __init__(self):
        metadata = ToolMetadata(
            name="ls",
            description="List directory contents. Returns list of files and folders.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["file", "read", "navigation"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        path = args.get("path", ".")
        workdir = Path(context.get("workdir", "."))
        full_path = workdir / path

        try:
            entries = []
            for entry in full_path.iterdir():
                entries.append({
                    "name": entry.name,
                    "type": "dir" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else 0,
                })
            return {"success": True, "entries": entries, "path": str(full_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: current)"}
            },
            "required": [],
        }
