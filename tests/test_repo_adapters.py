"""Tests for repo adapter tools."""

import pytest
from maximus.adapters.open_swe_adapter import AnalyzeOpenSweTool
from maximus.adapters.clawspring_adapter import AnalyzeClawSpringTool
from maximus.adapters.nexus_adapter import AnalyzeNexusTool
from maximus.tools.registry import ToolRegistry, register_tool


def test_open_swe_tool_metadata():
    tool = AnalyzeOpenSweTool()
    assert tool.metadata.name == "analyze_open_swe"
    assert tool.metadata.read_only is True
    assert tool.metadata.permission_level == "safe"


@pytest.mark.asyncio
async def test_open_swe_tool_execute():
    tool = AnalyzeOpenSweTool()
    result = await tool.execute({"repo_path": "."}, {})
    assert result["success"] is True
    assert "analysis" in result


@pytest.mark.asyncio
async def test_open_swe_tool_tech_stack():
    tool = AnalyzeOpenSweTool()
    result = await tool.execute({}, {})
    tech = result["analysis"]["tech_stack"]
    assert "python" in tech["language"].lower()


def test_clawspring_tool_metadata():
    tool = AnalyzeClawSpringTool()
    assert tool.metadata.name == "analyze_clawspring"
    assert "clawspring" in tool.metadata.description.lower()


@pytest.mark.asyncio
async def test_clawspring_tool_execute():
    tool = AnalyzeClawSpringTool()
    result = await tool.execute({"repo_path": "."}, {})
    assert result["success"] is True
    assert "event_loop" in result["analysis"]["key_components"]


def test_clawspring_tool_categories():
    tool = AnalyzeClawSpringTool()
    assert "clawspring" in tool.metadata.categories


def test_nexus_tool_metadata():
    tool = AnalyzeNexusTool()
    assert tool.metadata.name == "analyze_nexus"
    assert tool.metadata.local_only is True


@pytest.mark.asyncio
async def test_open_swe_tool_execute():
    tool = AnalyzeOpenSweTool()
    result = await tool.execute({"repo_path": "."}, {})
    assert result["success"] is True
    assert "repo" in result


@pytest.mark.asyncio
async def test_open_swe_tool_tech_stack():
    tool = AnalyzeOpenSweTool()
    result = await tool.execute({}, {})
    tech = result["tech_stack"]
    assert "Python" in tech


@pytest.mark.asyncio
async def test_clawspring_tool_execute():
    tool = AnalyzeClawSpringTool()
    result = await tool.execute({"repo_path": "."}, {})
    assert result["success"] is True
    assert "patterns" in result


@pytest.mark.asyncio
async def test_nexus_tool_execute():
    tool = AnalyzeNexusTool()
    result = await tool.execute({}, {})
    assert result["success"] is True
    assert "patterns" in result


@pytest.mark.asyncio
async def test_nexus_tool_stance_count():
    tool = AnalyzeNexusTool()
    result = await tool.execute({}, {})
    assert "7 adaptive behavior modes" in str(result["patterns"])


def test_all_tools_registered():
    from maximus.tools.builtin import register_repo_tools

    register_repo_tools()

    from maximus.tools.registry import registry

    names = registry.list_tools()
    assert "analyze_open_swe" in names
    assert "analyze_clawspring" in names
    assert "analyze_nexus" in names
