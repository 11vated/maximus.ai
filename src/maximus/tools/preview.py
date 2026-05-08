"""Preview write tool - required before actual file writes.

This tool is part of Layer 2 safety - user must call preview_write
before any write_file call.
"""
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool


class PreviewWriteTool(BaseTool):
    """Preview a file write without actually writing.
    
    This is a safety tool - calling it before write_file allows
    the write to proceed. Without this, write_file will be blocked.
    """
    
    def __init__(self):
        metadata = ToolMetadata(
            name="preview_write",
            description="Preview what would be written to a file. Must be called before write_file. Shows the user what will be written and enables the actual write.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["file", "preview", "safety"],
        )
        super().__init__(metadata)
        
    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute preview - just record that preview was called."""
        path = args.get("path", "")
        content = args.get("content", "")
        
        # Record this preview call for safety tracking
        from maximus.core.safety import get_safety_controller
        safety = get_safety_controller()
        session_id = context.get("session_id", "default")
        safety.record_preview(session_id)
        
        # Show what would be written (but don't write)
        lines = content.split('\n')
        preview_lines = lines[:10]  # First 10 lines
        truncated = len(lines) > 10
        
        return {
            "success": True,
            "path": path,
            "preview": "\n".join(preview_lines),
            "truncated": truncated,
            "total_lines": len(lines),
            "message": f"Preview recorded. This will write {len(lines)} lines to {path}. Call write_file to confirm."
        }
        
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to preview"},
                "content": {"type": "string", "description": "Content that would be written"},
            },
            "required": ["path", "content"],
        }