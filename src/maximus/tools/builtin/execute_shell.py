"""Execute shell command tool - local only with safety checks."""

import asyncio
import logging
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)

SAFE_COMMANDS = {"ls", "dir", "type", "echo", "pwd", "cd", "git", "python", "pip", "uv", "npm", "bun", "node", "ruff", "pytest", "mypy"}


class ExecuteShellTool(BaseTool):
    """Execute shell commands with safety checks."""

    def __init__(self):
        metadata = ToolMetadata(
            name="execute_shell",
            description="Execute a shell command. Only safe commands allowed (ls, git, python, etc).",
            read_only=False,
            concurrent_safe=False,
            permission_level="dangerous",
            local_only=True,
            categories=["shell", "system"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        command = args.get("command")
        if not command:
            return {"success": False, "error": "Missing 'command' argument"}

        cmd_lower = command.lower().strip()
        if not any(cmd_lower.startswith(safe) for safe in SAFE_COMMANDS):
            return {"success": False, "error": f"Command not in safe list: {command}"}

        workdir = context.get("workdir", ".")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
                "command": command,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"}
            },
            "required": ["command"],
        }
