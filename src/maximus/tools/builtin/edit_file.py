"""Edit file tool - local only."""

import logging
from pathlib import Path
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class EditFileTool(BaseTool):
    """Edit specific parts of a file using old/new text replacement."""

    def __init__(self):
        metadata = ToolMetadata(
            name="edit_file",
            description="Edit a file by replacing old_text with new_text. Creates backup if specified.",
            read_only=False,
            concurrent_safe=False,
            permission_level="write",
            local_only=True,
            categories=["file", "edit", "write"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        path = args.get("path")
        old_text = args.get("old_text", "")
        new_text = args.get("new_text", "")
        backup = args.get("backup", False)

        if not path:
            return {"success": False, "error": "Missing 'path' argument"}
        if not old_text:
            return {"success": False, "error": "Missing 'old_text' argument"}

        workdir = Path(context.get("workdir", "."))
        full_path = workdir / path

        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            
            if backup:
                backup_path = full_path.with_suffix(full_path.suffix + ".bak")
                backup_path.write_text(content, encoding="utf-8")

            if old_text not in content:
                return {"success": False, "error": "old_text not found in file"}

            new_content = content.replace(old_text, new_text, 1)
            full_path.write_text(new_content, encoding="utf-8")

            return {
                "success": True,
                "path": str(full_path),
                "bytes": len(new_content),
                "backup_created": backup,
            }
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "old_text": {"type": "string", "description": "Text to replace"},
                "new_text": {"type": "string", "description": "Replacement text"},
                "backup": {"type": "boolean", "description": "Create backup file"},
            },
            "required": ["path", "old_text", "new_text"],
        }
