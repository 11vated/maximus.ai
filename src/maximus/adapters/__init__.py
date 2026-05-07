"""Repo adapters for Maximus.ai."""

from maximus.adapters.open_swe_adapter import AnalyzeOpenSweTool, OpenSweAdapter
from maximus.adapters.clawspring_adapter import AnalyzeClawSpringTool, ClawSpringAdapter
from maximus.adapters.nexus_adapter import AnalyzeNexusTool, NexusAdapter

# Register repo analysis tools
def register_repo_tools():
    """Register repo-specific analysis tools."""
    from maximus.tools.registry import register_tool
    register_tool(AnalyzeOpenSweTool())
    register_tool(AnalyzeClawSpringTool())
    register_tool(AnalyzeNexusTool())


__all__ = [
    "AnalyzeOpenSweTool", "OpenSweAdapter",
    "AnalyzeClawSpringTool", "ClawSpringAdapter",
    "AnalyzeNexusTool", "NexusAdapter",
    "register_repo_tools",
]
