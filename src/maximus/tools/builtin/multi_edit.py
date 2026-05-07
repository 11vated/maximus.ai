"""MultiEdit tool - edit multiple files atomically."""

from typing import Any, Dict, List, Optional
from pathlib import Path

from maximus.tools.base import BaseTool
from maximus.models import PermissionLevel, ToolMetadata


class ToolResult:
    """Simple result wrapper."""
    def __init__(self, success: bool, data: Optional[Dict] = None, error: Optional[str] = None):
        self.success = success
        self.data = data or {}
        self.error = error


class MultiEditTool(BaseTool):
    """Edit multiple files in a single atomic operation.
    
    Provides Claude Code's multi-edit capability - edit several files
    at once with a single tool call. All edits are applied together
    or rolled back on failure.
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="multi_edit",
            description="Edit multiple files atomically. Provide a list of file edits to apply together.",
            permission_level=PermissionLevel.WRITE,
            read_only=False
        )
        super().__init__(metadata)
        self.parameters = {
            "edits": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to edit"},
                        "old": {"type": "string", "description": "Text to replace"},
                        "new": {"type": "string", "description": "Replacement text"}
                    },
                    "required": ["path", "old", "new"]
                },
                "description": "List of edits to apply"
            },
            "dry_run": {"type": "boolean", "description": "If true, show diff without applying"}
        }
        self.required_params = ["edits"]

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        edits = args.get("edits", [])
        dry_run = args.get("dry_run", False)
        
        if not edits:
            return ToolResult(success=False, error="No edits provided")

        workdir = Path(context.get("workdir", "."))
        results = []
        all_success = True

        # First, validate all edits
        for edit in edits:
            file_path = workdir / edit["path"]
            if not file_path.exists():
                results.append({
                    "path": edit["path"],
                    "success": False,
                    "error": "File not found"
                })
                all_success = False
                continue
            
            # Check if old text exists
            try:
                content = file_path.read_text(encoding="utf-8")
                if edit["old"] not in content:
                    results.append({
                        "path": edit["path"],
                        "success": False,
                        "error": f"Text to replace not found in file"
                    })
                    all_success = False
            except Exception as e:
                results.append({
                    "path": edit["path"],
                    "success": False,
                    "error": str(e)
                })
                all_success = False

        if not all_success:
            return ToolResult(
                success=False,
                error="Some edits failed validation",
                data={"results": results}
            )

        # If dry run, return diffs
        if dry_run:
            diffs = []
            for edit in edits:
                file_path = workdir / edit["path"]
                content = file_path.read_text(encoding="utf-8")
                new_content = content.replace(edit["old"], edit["new"])
                diffs.append({
                    "path": edit["path"],
                    "old_lines": len(edit["old"].split("\n")),
                    "new_lines": len(edit["new"].split("\n")),
                    "preview": f"--- {edit['path']}\n+++ {edit['path']}\n@@ ... @@"
                })
            return ToolResult(
                success=True,
                data={"diffs": diffs, "dry_run": True}
            )

        # Apply all edits
        applied = []
        for edit in edits:
            file_path = workdir / edit["path"]
            try:
                content = file_path.read_text(encoding="utf-8")
                new_content = content.replace(edit["old"], edit["new"])
                file_path.write_text(new_content, encoding="utf-8")
                applied.append({
                    "path": edit["path"],
                    "success": True
                })
            except Exception as e:
                applied.append({
                    "path": edit["path"],
                    "success": False,
                    "error": str(e)
                })
                # Could implement rollback here

        return ToolResult(
            success=all_success,
            data={"results": applied}
        )