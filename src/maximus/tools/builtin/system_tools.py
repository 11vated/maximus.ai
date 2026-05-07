"""System info and environment tools."""

import asyncio
import logging
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class EnvInfoTool(BaseTool):
    """Get environment variable or all env vars."""

    def __init__(self):
        metadata = ToolMetadata(
            name="env_info",
            description="Get environment variable(s).",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["system", "info"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        var_name = args.get("name")
        try:
            if var_name:
                value = os.environ.get(var_name)
                return {"success": True, "name": var_name, "value": value}
            else:
                safe_keys = ["PATH", "PYTHONPATH", "HOME", "USER", "OS", "TEMP"]
                env = {k: os.environ.get(k, "") for k in safe_keys if k in os.environ}
                return {"success": True, "env": env}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Environment variable name (optional)"}
            },
            "required": [],
        }


class SystemInfoTool(BaseTool):
    """Get system information."""

    def __init__(self):
        metadata = ToolMetadata(
            name="system_info",
            description="Get system information (OS, Python version, etc.).",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["system", "info"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {
                "success": True,
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": sys.version,
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}


class CreateDirTool(BaseTool):
    """Create a directory (and parents if needed)."""

    def __init__(self):
        metadata = ToolMetadata(
            name="create_dir",
            description="Create a directory, including parent directories if needed.",
            read_only=False,
            concurrent_safe=True,
            permission_level="write",
            local_only=True,
            categories=["file", "write"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        path = args.get("path")
        if not path:
            return {"success": False, "error": "Missing 'path' argument"}

        workdir = Path(context.get("workdir", "."))
        full_path = workdir / path

        try:
            full_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to create"}
            },
            "required": ["path"],
        }


class ListProcessesTool(BaseTool):
    """List running processes."""

    def __init__(self):
        metadata = ToolMetadata(
            name="list_processes",
            description="List running processes (Windows: tasklist, Unix: ps).",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["system", "info"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    "tasklist", "/fo", "csv",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    "ps", "aux",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            stdout, _ = await proc.communicate()
            return {"success": True, "output": stdout.decode("utf-8", errors="replace")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}
