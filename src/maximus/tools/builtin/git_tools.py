"""Git tools - local only."""

import asyncio
import logging
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class GitStatusTool(BaseTool):
    """Check git status."""

    def __init__(self):
        metadata = ToolMetadata(
            name="git_status",
            description="Check git repository status (status, branch, etc).",
            read_only=True,
            concurrent_safe=False,
            permission_level="safe",
            local_only=True,
            categories=["git", "vcs"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        workdir = context.get("workdir", ".")

        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "status": stdout.decode("utf-8", errors="replace"),
                "error": stderr.decode("utf-8", errors="replace") if proc.returncode != 0 else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}


class GitDiffTool(BaseTool):
    """Show git diff."""

    def __init__(self):
        metadata = ToolMetadata(
            name="git_diff",
            description="Show git diff for staged or unstaged changes.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["git", "vcs"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        staged = args.get("staged", False)
        workdir = context.get("workdir", ".")

        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": True,
                "diff": stdout.decode("utf-8", errors="replace"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "staged": {"type": "boolean", "description": "Show staged changes"}
            },
            "required": [],
        }


class GitCommitTool(BaseTool):
    """Commit changes to git."""

    def __init__(self):
        metadata = ToolMetadata(
            name="git_commit",
            description="Commit staged changes with a message.",
            read_only=False,
            concurrent_safe=False,
            permission_level="write",
            local_only=True,
            categories=["git", "vcs"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        message = args.get("message", "Update files")
        add_all = args.get("add_all", False)

        workdir = context.get("workdir", ".")

        try:
            if add_all:
                proc = await asyncio.create_subprocess_exec(
                    "git", "add", ".",
                    cwd=workdir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", message,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace"),
                "error": stderr.decode("utf-8", errors="replace") if proc.returncode != 0 else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "add_all": {"type": "boolean", "description": "Stage all changes first"},
            },
            "required": ["message"],
        }


class GitAddTool(BaseTool):
    """Stage files for commit."""

    def __init__(self):
        metadata = ToolMetadata(
            name="git_add",
            description="Stage files for git commit.",
            read_only=False,
            concurrent_safe=False,
            permission_level="write",
            local_only=True,
            categories=["git", "vcs"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        files = args.get("files", ["."])

        workdir = context.get("workdir", ".")

        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "add", *files,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "files": {"type": "array", "items": {"type": "string"}, "description": "Files to stage"},
            },
            "required": ["files"],
        }


class GitPushTool(BaseTool):
    """Push commits to remote."""

    def __init__(self):
        metadata = ToolMetadata(
            name="git_push",
            description="Push commits to remote repository.",
            read_only=False,
            concurrent_safe=False,
            permission_level="dangerous",
            local_only=True,
            categories=["git", "vcs"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        remote = args.get("remote", "origin")
        branch = args.get("branch", "")

        workdir = context.get("workdir", ".")

        cmd = ["git", "push", remote]
        if branch:
            cmd.append(branch)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace"),
                "error": stderr.decode("utf-8", errors="replace") if proc.returncode != 0 else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "remote": {"type": "string", "description": "Remote name (default: origin)"},
                "branch": {"type": "string", "description": "Branch to push"},
            },
            "required": [],
        }
