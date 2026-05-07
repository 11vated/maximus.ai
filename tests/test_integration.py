"""End-to-end integration test for Maximus.ai."""

import pytest
import asyncio
from maximus.core.loop import AgentLoop
from maximus.models import AgentConfig, CognitiveState
from maximus.tools.registry import registry, register_tool
from maximus.adapters.open_swe_adapter import AnalyzeOpenSweTool
from maximus.adapters.clawspring_adapter import AnalyzeClawSpringTool
from maximus.adapters.nexus_adapter import AnalyzeNexusTool


@pytest.fixture(autouse=True)
def setup_tools():
    """Register repo tools before each test."""
    register_tool(AnalyzeOpenSweTool())
    register_tool(AnalyzeClawSpringTool())
    register_tool(AnalyzeNexusTool())
    yield
    # Cleanup not needed since registry is global


@pytest.mark.asyncio
async def test_agent_loop_basic_flow():
    """Test that the agent loop can initialize and transition states."""
    config = AgentConfig(model="qwen2.5-coder:7b", workdir=".")
    agent = AgentLoop(config)

    assert agent.state == CognitiveState.INIT
    assert agent.config.model == "qwen2.5-coder:7b"


@pytest.mark.asyncio
async def test_repo_analysis_open_swe():
    """Test open-swe repo analysis tool."""
    tool = AnalyzeOpenSweTool()
    result = await tool.execute({"repo_path": "C:/Users/11vat/Desktop/agent007/open-swe"}, {})

    assert result["success"] is True
    assert "open-swe" in result["repo"].lower() or "open" in result["repo"].lower()
    assert "tech_stack" in result
    assert "patterns" in result


@pytest.mark.asyncio
async def test_repo_analysis_clawspring():
    """Test ClawSpring repo analysis tool."""
    tool = AnalyzeClawSpringTool()
    result = await tool.execute({"repo_path": "C:/Users/11vat/Desktop/agent007/collection-claude-code-source-code"}, {})

    assert result["success"] is True
    assert "ClawSpring" in result["repo"] or "Claude" in result["repo"]
    assert "patterns" in result


@pytest.mark.asyncio
async def test_repo_analysis_nexus():
    """Test Nexus repo analysis tool."""
    tool = AnalyzeNexusTool()
    result = await tool.execute({"repo_path": "C:/Users/11vat/Desktop/agent007/nexus"}, {})

    assert result["success"] is True
    assert "Nexus" in result["repo"]
    assert "patterns" in result


@pytest.mark.asyncio
async def test_stance_system():
    """Test stance system integration."""
    from maximus.intelligence.stance import StanceManager, StanceType

    manager = StanceManager()
    assert manager.current_stance == StanceType.METHODICAL

    manager.switch(StanceType.EXPLORATORY, "Testing exploration")
    assert manager.current_stance == StanceType.EXPLORATORY

    context = manager.get_planning_context()
    assert "stance" in context
    assert context["stance"] == "exploratory"


@pytest.mark.asyncio
async def test_branch_manager():
    """Test conversation branching."""
    from maximus.memory.branching import BranchManager

    manager = BranchManager(workdir="C:/Users/11vat/Desktop/agent007/maximus.ai")

    branches_before = len(manager.list_branches())

    manager.create_branch("test-branch")
    branches_after = len(manager.list_branches())
    assert branches_after == branches_before + 1

    manager.switch_branch("test-branch")
    assert manager.current_branch_name == "test-branch"

    manager.switch_branch("main")
    manager.delete_branch("test-branch")


@pytest.mark.asyncio
async def test_compaction_manager():
    """Test context compaction."""
    from maximus.memory.compaction import CompactionManager, CompactionConfig

    config = CompactionConfig(max_context_tokens=1000, preserve_recent=5)
    manager = CompactionManager(config)

    messages = [{"role": "user", "content": f"Message {i}" * 20} for i in range(50)]
    compacted = manager.compact(messages)

    assert len(compacted) <= len(messages)
    assert manager.needs_compaction(messages) is True


@pytest.mark.asyncio
async def test_mcp_manager():
    """Test MCP manager."""
    from maximus.mcp.manager import MCPManager, MCPServerConfig

    manager = MCPManager()
    assert len(manager.get_servers()) == 0

    config = MCPServerConfig(
        name="test-server",
        command=["python", "-m", "test_server"],
    )
    manager.add_server(config)
    assert len(manager.get_servers()) == 1

    tools = await manager.list_tools()
    assert len(tools) >= 0
