"""Test runner tool - pytest, npm test, etc."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class TestRunnerTool(BaseTool):
    """Run tests using pytest or other test frameworks."""

    def __init__(self):
        metadata = ToolMetadata(
            name="run_tests",
            description="Run tests using pytest (Python) or npm test (Node.js).",
            read_only=True,
            concurrent_safe=False,
            permission_level="safe",
            local_only=True,
            categories=["test", "execute"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        test_type = args.get("type", "pytest")
        path = args.get("path", ".")

        workdir = Path(context.get("workdir", "."))
        test_path = workdir / path

        try:
            if test_type == "pytest":
                cmd = ["python", "-m", "pytest", str(test_path), "-v"]
            elif test_type == "npm":
                cmd = ["npm", "test"]
            else:
                return {"success": False, "error": f"Unknown test type: {test_type}"}

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(workdir),
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"Command not found: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["pytest", "npm"], "description": "Test framework"},
                "path": {"type": "string", "description": "Test path (default: current dir)"},
            },
            "required": [],
        }
