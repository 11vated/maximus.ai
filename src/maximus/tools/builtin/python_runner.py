"""Python code runner tool - execute Python code in temp file."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class PythonRunnerTool(BaseTool):
    """Execute Python code in isolation."""

    def __init__(self):
        metadata = ToolMetadata(
            name="run_python",
            description="Execute Python code. Code is written to temp file and run.",
            read_only=False,
            concurrent_safe=False,
            permission_level="dangerous",
            local_only=True,
            categories=["execute", "python", "sandbox"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        code = args.get("code")
        if not code:
            return {"success": False, "error": "Missing 'code' argument"}

        workdir = Path(context.get("workdir", "."))

        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", dir=str(workdir), delete=False
            ) as f:
                f.write(code)
                temp_path = f.name

            # Execute
            proc = await asyncio.create_subprocess_exec(
                "python", temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(workdir),
            )
            stdout, stderr = await proc.communicate()

            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"}
            },
            "required": ["code"],
        }
