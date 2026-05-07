"""Grep/search tool - local only."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class GrepTool(BaseTool):
    """Search file contents using regex."""

    def __init__(self):
        metadata = ToolMetadata(
            name="grep",
            description="Search file contents using regex. Returns matching lines with file paths.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["search", "read"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        pattern = args.get("pattern")
        path = args.get("path", ".")
        include = args.get("include", "*.py")

        if not pattern:
            return {"success": False, "error": "Missing 'pattern' argument"}

        workdir = Path(context.get("workdir", "."))
        search_path = workdir / path

        try:
            results = await self._search(pattern, search_path, include)
            return {"success": True, "results": results, "count": len(results)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _search(self, pattern: str, path: Path, include: str) -> List[Dict]:
        """Search using available tools."""
        results = []
        try:
            # Try ripgrep first
            proc = await asyncio.create_subprocess_exec(
                "rg", "-n", "--color=never", "--include", include, pattern, str(path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            lines = stdout.decode("utf-8", errors="replace").strip().split("\n")
            for line in lines:
                if line.strip() and ":" in line:
                    results.append({"match": line})
        except FileNotFoundError:
            # Fallback to Python
            for f in path.rglob(include.replace("*", "**")):
                if f.is_file():
                    try:
                        text = f.read_text(encoding="utf-8", errors="replace")
                        for i, line in enumerate(text.split("\n"), 1):
                            if pattern in line:
                                results.append({"file": str(f), "line": f"{i}: {line}"})
                    except Exception:
                        pass
        return results[:100]  # Limit results

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search"},
                "path": {"type": "string", "description": "Path to search (default: current dir)"},
                "include": {"type": "string", "description": "File glob (default: *.py)"},
            },
            "required": ["pattern"],
        }
