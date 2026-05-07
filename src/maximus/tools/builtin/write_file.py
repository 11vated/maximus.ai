"""Write file tool - local only."""

import logging
from pathlib import Path
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class WriteFileTool(BaseTool):
    """Write content to a file."""

    def __init__(self):
        metadata = ToolMetadata(
            name="write_file",
            description="Write content to a file. Creates parent directories if needed.",
            read_only=False,
            concurrent_safe=False,
            permission_level="write",
            local_only=True,
            categories=["file", "write"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        path = args.get("path")
        content = args.get("content", "")

        if not path:
            return {"success": False, "error": "Missing 'path' argument"}

        workdir = Path(context.get("workdir", "."))
        full_path = workdir / path

        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(full_path), "bytes": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        }
