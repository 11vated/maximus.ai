"""Read file tool - local only."""

import logging
from pathlib import Path
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ReadFileTool(BaseTool):
    """Read contents of a file (read-only, safe)."""

    def __init__(self):
        metadata = ToolMetadata(
            name="read_file",
            description="Read the contents of a file. Returns file content as string.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["file", "read"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        path = args.get("path")
        if not path:
            return {"success": False, "error": "Missing 'path' argument"}

        workdir = Path(context.get("workdir", "."))
        full_path = workdir / path

        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            return {"success": True, "content": content, "path": str(full_path)}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file (relative to workdir)"}
            },
            "required": ["path"],
        }
