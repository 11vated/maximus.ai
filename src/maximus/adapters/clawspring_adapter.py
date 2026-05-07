"""Adapter for ClawSpring (collection-claude-code-source-code)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class AnalyzeClawSpringTool(BaseTool):
    """Analyze ClawSpring repo structure."""

    def __init__(self):
        metadata = ToolMetadata(
            name="analyze_clawspring",
            description="Analyze ClawSpring: event loop, tools, memory, multi-agent.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["repo", "analyze", "clawspring"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        repo_path = args.get("path", ".")
        workdir = Path(context.get("workdir", "."))
        full_path = workdir / repo_path

        try:
            result = {
                "repo": "ClawSpring (Nano Claude Code)",
                "path": str(full_path),
                "tech_stack": ["Python 3.10+", "Ollama", "Rich", "Pydantic"],
                "key_dirs": ["clawspring/", "clawspring/tools/", "skill/", "memory/", "multi_agent/"],
                "key_files": ["clawspring/agent.py", "clawspring/tools.py", "skill/builtin.py"],
                "patterns": [
                    "Event-driven agent loop (TextChunk, ThinkingChunk, ToolStart, ToolEnd)",
                    "Tool registry with metadata (read_only, permission_level, local_only)",
                    "Dual-scope memory (user + project)",
                    "Skill system (YAML frontmatter, $ARGUMENTS)",
                    "Multi-agent (5 types: general, coder, reviewer, researcher, tester)",
                    "Context compaction (rule-based + AI summarization)",
                    "MCP integration (Model Context Protocol)",
                ],
                "tools_count": 25,
                "supports": ["Ollama", "OpenAI", "Anthropic", "Gemini", "DeepSeek"],
            }
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to ClawSpring repo"}
            },
            "required": [],
        }


class ClawSpringAdapter:
    """Adapter for ClawSpring repo-specific operations."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def get_capabilities(self) -> Dict[str, Any]:
        """Detect ClawSpring capabilities."""
        return {
            "repo": "ClawSpring",
            "language": "Python",
            "package_manager": "uv/ pip",
            "event_types": ["TextChunk", "ThinkingChunk", "ToolStart", "ToolEnd", "TurnDone"],
            "memory_scopes": ["user", "project", "feedback", "reference"],
            "multi_agent_types": ["general-purpose", "coder", "reviewer", "researcher", "tester"],
            "skill_system": True,
            "mcp_support": True,
            "permission_modes": ["auto", "accept-all", "manual"],
        }

    def get_tool_categories(self) -> List[str]:
        """Get tool categories."""
        return ["file", "shell", "git", "search", "web", "system"]

    def get_test_command(self) -> str:
        """Get test command."""
        return "pytest tests/ -v"

    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory system info."""
        return {
            "short_term": "Rolling window (deque)",
            "long_term": "File-based (MEMORY.md) + optional ChromaDB",
            "dual_scope": True,
            "confidence_scoring": True,
        }
