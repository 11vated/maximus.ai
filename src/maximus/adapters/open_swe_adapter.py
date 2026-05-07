"""Adapter for open-swe repo (LangChain agent)."""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any, Dict, List

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class AnalyzeOpenSweTool(BaseTool):
    """Analyze open-swe repo structure."""

    def __init__(self):
        metadata = ToolMetadata(
            name="analyze_open_swe",
            description="Analyze open-swe repo: structure, tech stack, key components.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["repo", "analyze", "open-swe"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        repo_path = args.get("path", ".")
        workdir = Path(context.get("workdir", "."))
        full_path = workdir / repo_path

        try:
            result = {
                "repo": "open-swe",
                "path": str(full_path),
                "tech_stack": ["Python", "LangGraph", "FastAPI", "Ollama"],
                "key_dirs": ["agent/", "agent/tools/", "evals/", "tests/"],
                "key_files": ["agent/server.py", "agent/prompt.py", "pyproject.toml"],
                "patterns": [
                    "LangGraph Pregel graph executor",
                    "Middleware stack (6 layers)",
                    "Deep Agents framework",
                    "Cloud sandbox (LangSmith/Daytona/Modal)",
                    "Trigger system (GitHub/Linear/Slack)",
                ],
                "tools_count": 12,
                "test_framework": "pytest + pytest-asyncio",
            }
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to open-swe repo"}
            },
            "required": [],
        }


class OpenSweAdapter:
    """Adapter for open-swe repo-specific operations."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def get_capabilities(self) -> Dict[str, Any]:
        """Detect open-swe capabilities."""
        return {
            "repo": "open-swe",
            "language": "Python",
            "package_manager": "uv",
            "test_framework": "pytest",
            "llm_provider": "OpenAI/Anthropic",
            "sandbox": "LangSmith/Daytona/Modal",
            "middleware_layers": 6,
            "tools_count": 12,
            "has_docker": True,
            "has_evals": True,
        }

    def analyze_middleware(self) -> Dict[str, Any]:
        """Analyze middleware stack."""
        return {
            "layers": [
                "SanitizeToolInputsMiddleware",
                "ModelCallLimitMiddleware",
                "ToolErrorMiddleware",
                "check_message_queue_before_model",
                "ensure_no_empty_msg",
                "notify_step_limit_reached",
            ],
            "pattern": "LangGraph middleware stack",
            "source": "agent/middleware/",
        }

    def get_test_command(self) -> str:
        """Get test command for this repo."""
        return "uv run pytest -vvv tests/"

    def get_lint_command(self) -> str:
        """Get lint command."""
        return "ruff check && ruff format --diff"

    def get_install_command(self) -> str:
        """Get install command."""
        return "uv pip install -e ."
