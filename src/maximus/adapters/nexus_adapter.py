"""Adapter for Nexus repo."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class AnalyzeNexusTool(BaseTool):
    """Analyze Nexus repo structure."""

    def __init__(self):
        metadata = ToolMetadata(
            name="analyze_nexus",
            description="Analyze Nexus: cognitive loop, intelligence layer, memory, tools.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["repo", "analyze", "nexus"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        repo_path = args.get("path", ".") 
        workdir = Path(context.get("workdir", "."))
        full_path = workdir / repo_path

        try:
            result = {
                "repo": "Nexus",
                "path": str(full_path),
                "tech_stack": ["Python 3.10+", "Ollama", "FastAPI", "Rich", "Pydantic", "ChromaDB"],
                "key_dirs": ["src/nexus/agent/", "src/nexus/tools/", "src/nexus/memory/", "src/nexus/cognitive/"],
                "key_files": ["src/nexus/agent/loop.py", "ARCHITECTURE.md", "NEXUS_DEEP_BLUEPRINT.md"],
                "patterns": [
                    "8-state cognitive loop (INIT→PLAN→ACT→OBSERVE→REFLECT→ADAPT→COMMIT→PAUSE)",
                    "Intelligence layer (ModelRouter, Stances, ProjectMap)",
                    "Memory: Short-term (rolling) + Long-term (ChromaDB/file)",
                    "7 adaptive behavior modes (stances)",
                    "Conversation branching (git-like)",
                    "Diff-before-write philosophy",
                    "4-level trust system (untrusted→privileged)",
                    "Hook system (HookEngine + WatcherEngine)",
                    "SWE-bench integration",
                ],
                "test_count": "630+",
                "local_first": True,
                "supports": ["Ollama only (local)"],
            }
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to Nexus repo"}
            },
            "required": [],
        }


class NexusAdapter:
    """Adapter for Nexus repo-specific operations."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def get_capabilities(self) -> Dict[str, Any]:
        """Detect Nexus capabilities."""
        return {
            "repo": "Nexus",
            "cognitive_states": 8,
            "stance_modes": 7,
            "trust_levels": 4,
            "memory_layers": ["short_term", "long_term", "context_store"],
            "intelligence_features": ["ModelRouter", "Stances", "ProjectMap", "SessionStore"],
            "swe_bench": True,
            "tui": "Textual-based (optional)",
            "vector_store": "ChromaDB (optional)",
        }

    def get_cognitive_states(self) -> List[str]:
        """Get the 8 cognitive states."""
        return ["INIT", "PLAN", "ACT", "OBSERVE", "REFLECT", "ADAPT", "COMMIT", "PAUSE"]

    def get_stances(self) -> List[Dict[str, str]]:
        """Get the 7 behavior stances."""
        return [
            {"name": "exploratory", "desc": "Broad exploration"},
            {"name": "methodical", "desc": "Step-by-step approach"},
            {"name": "agressive", "desc": "Bold changes"},
            {"name": "cautious", "desc": "Minimal changes"},
            {"name": "collaborative", "desc": "User-in-the-loop"},
            {"name": "debugging", "desc": "Focus on bugs"},
            {"name": "learning", "desc": "Knowledge acquisition"},
        ]

    def get_test_command(self) -> str:
        """Get test command."""
        return "pytest tests/ -v --cov"

    def get_architecture_summary(self) -> Dict[str, Any]:
        """Get architecture highlights."""
        return {
            "pattern": "Cognitive partnership (not just tool use)",
            "philosophy": "Transparency Over Performance, Growth Over Capability",
            "core_loop": "AgentLoop (8-state cognitive machine)",
            "differentiator": "Meta-cognition with IRSC dual-loop",
        }
