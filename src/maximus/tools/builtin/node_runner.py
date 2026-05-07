"""Node.js code runner tool."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class NodeRunnerTool(BaseTool):
    """Execute Node.js code in isolation."""

    def __init__(self):
        metadata = ToolMetadata(
            name="run_node",
            description="Execute Node.js code. Code is written to temp file and run.",
            read_only=False,
            concurrent_safe=False,
            permission_level="dangerous",
            local_only=True,
            categories=["execute", "node", "javascript", "sandbox"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        code = args.get("code")
        if not code:
            return {"success": False, "error": "Missing 'code' argument"}

        workdir = Path(context.get("workdir", "."))

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".js", dir=str(workdir), delete=False
            ) as f:
                f.write(code)
                temp_path = f.name

            proc = await asyncio.create_subprocess_exec(
                "node", temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(workdir),
            )
            stdout, stderr = await proc.communicate()

            Path(temp_path).unlink(missing_ok=True)

            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
            }
        except FileNotFoundError:
            return {"success": False, "error": "Node.js not found. Install from nodejs.org"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "JavaScript code to execute"}
            },
            "required": ["code"],
        }
