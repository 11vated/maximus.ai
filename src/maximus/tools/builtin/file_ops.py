"""File operations tool - move/rename files."""

import logging
from pathlib import Path
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class MoveFileTool(BaseTool):
    """Move or rename a file."""

    def __init__(self):
        metadata = ToolMetadata(
            name="move_file",
            description="Move or rename a file from source to destination.",
            read_only=False,
            concurrent_safe=False,
            permission_level="write",
            local_only=True,
            categories=["file", "write"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        src = args.get("src")
        dst = args.get("dst")

        if not src or not dst:
            return {"success": False, "error": "Missing 'src' or 'dst' argument"}

        workdir = Path(context.get("workdir", "."))
        src_path = workdir / src
        dst_path = workdir / dst

        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            src_path.rename(dst_path)
            return {"success": True, "from": str(src_path), "to": str(dst_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"},
            },
            "required": ["src", "dst"],
        }


class CopyFileTool(BaseTool):
    """Copy a file."""

    def __init__(self):
        metadata = ToolMetadata(
            name="copy_file",
            description="Copy a file from source to destination.",
            read_only=False,
            concurrent_safe=True,
            permission_level="write",
            local_only=True,
            categories=["file", "write"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        src = args.get("src")
        dst = args.get("dst")

        if not src or not dst:
            return {"success": False, "error": "Missing 'src' or 'dst' argument"}

        workdir = Path(context.get("workdir", "."))
        src_path = workdir / src
        dst_path = workdir / dst

        try:
            import shutil
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            return {"success": True, "from": str(src_path), "to": str(dst_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"},
            },
            "required": ["src", "dst"],
        }


class DeleteFileTool(BaseTool):
    """Delete a file (with safety check)."""

    def __init__(self):
        metadata = ToolMetadata(
            name="delete_file",
            description="Delete a file. Requires confirmation for safety.",
            read_only=False,
            concurrent_safe=False,
            permission_level="dangerous",
            local_only=True,
            categories=["file", "write"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        path = args.get("path")
        force = args.get("force", False)

        if not path:
            return {"success": False, "error": "Missing 'path' argument"}

        workdir = Path(context.get("workdir", "."))
        full_path = workdir / path

        try:
            if not force:
                return {"success": False, "error": "Add force=true to confirm deletion"}
            full_path.unlink(missing_ok=True)
            return {"success": True, "deleted": str(full_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "force": {"type": "boolean", "description": "Confirm deletion"},
            },
            "required": ["path"],
        }
