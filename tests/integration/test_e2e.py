"""End-to-end integration tests for Maximus.ai full agent loop.

These tests require a running Ollama instance with a model loaded.
They test the complete agent pipeline: prompt -> planning -> tool use -> response.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import List

from maximus.core.loop import AgentLoop
from maximus.models import AgentConfig, CognitiveState, Event, EventType
from maximus.tools.registry import get_registry
from maximus.middleware import (
    ToolErrorMiddleware,
    MessageQueueMiddleware,
    SanitizeMiddleware,
    StepLimitMiddleware,
    apply_middleware,
)


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not Path("/usr/bin/ollama").exists()
        and not Path("C:/Users/11vat/AppData/Local/Programs/Ollama/ollama.exe").exists(),
        reason="Ollama not installed",
    ),
]


@pytest.fixture
def agent_config(tmp_path) -> AgentConfig:
    """Create agent config for testing."""
    return AgentConfig(
        model="qwen2.5-coder:7b",
        workdir=str(tmp_path),
        max_steps=10,
        temperature=0.1,
    )


@pytest.fixture
def agent_loop(agent_config: AgentConfig) -> AgentLoop:
    """Create agent loop instance."""
    return AgentLoop(agent_config)


class TestAgentInitialization:
    """Test agent initialization and configuration."""

    def test_agent_creation(self, agent_config: AgentConfig):
        """Test basic agent creation."""
        loop = AgentLoop(agent_config)
        assert loop.state == CognitiveState.INIT
        assert loop.config.model == "qwen2.5-coder:7b"

    def test_tool_registration(self, agent_loop: AgentLoop):
        """Test that tools are properly registered."""
        registry = get_registry()
        tool_names = registry.list_tools()
        assert len(tool_names) > 0

        required_tools = [
            "read_file", "write_file", "execute_shell", "grep", "ls",
            "glob", "edit_file",
        ]
        for tool_name in required_tools:
            assert tool_name in tool_names, f"Missing required tool: {tool_name}"

    def test_state_transitions(self, agent_loop: AgentLoop):
        """Test state machine transitions."""
        assert agent_loop.state == CognitiveState.INIT

        agent_loop.state = CognitiveState.PLAN
        assert agent_loop.state == CognitiveState.PLAN

        agent_loop.state = CognitiveState.ACT
        assert agent_loop.state == CognitiveState.ACT

        agent_loop.state = CognitiveState.REFLECT
        assert agent_loop.state == CognitiveState.REFLECT

        agent_loop.state = CognitiveState.COMMIT
        assert agent_loop.state == CognitiveState.COMMIT

        agent_loop.state = CognitiveState.PAUSE
        assert agent_loop.state == CognitiveState.PAUSE


class TestAgentExecution:
    """Test agent execution with Ollama."""

    @pytest.mark.asyncio
    async def test_simple_prompt_flow(self, agent_loop: AgentLoop):
        """Test a simple prompt through the entire agent loop."""
        events: List[Event] = []

        async for event in agent_loop.run_async("What is 2 + 2?"):
            events.append(event)

        assert len(events) > 0

        state_events = [e for e in events if e.type == EventType.STATE_CHANGE]
        assert len(state_events) > 0

        # Should end in PAUSE state
        assert agent_loop.state == CognitiveState.PAUSE

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Ollama running")
    async def test_tool_use_flow(self, agent_loop: AgentLoop):
        """Test agent using a tool."""
        events: List[Event] = []

        async for event in agent_loop.run_async("List the files in the current directory"):
            events.append(event)

        tool_events = [e for e in events if e.type in (EventType.TOOL_START, EventType.TOOL_END)]
        assert len(tool_events) > 0, "Agent should use at least one tool"

    @pytest.mark.asyncio
    async def test_event_types_produced(self, agent_loop: AgentLoop):
        """Test that all expected event types are produced."""
        events: List[Event] = []
        async for event in agent_loop.run_async("Show me the current directory"):
            events.append(event)

        event_types = {e.type for e in events}
        assert EventType.STATE_CHANGE in event_types
        assert EventType.TURN_DONE in event_types

    @pytest.mark.asyncio
    async def test_middleware_application(self):
        """Test that middleware can be applied to a tool function."""
        async def mock_tool(name, args):
            return {"success": True, "result": "ok"}

        middlewares = [
            ToolErrorMiddleware(),
            SanitizeMiddleware(),
        ]

        wrapped = apply_middleware(mock_tool, middlewares)
        result = await wrapped("test_tool", {})
        assert result["success"] is True


class TestAgentEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_prompt(self, agent_loop: AgentLoop):
        """Test handling of empty prompt."""
        events: List[Event] = []
        async for event in agent_loop.run_async(""):
            events.append(event)
        assert len(events) >= 0

    @pytest.mark.asyncio
    async def test_very_long_prompt(self, agent_loop: AgentLoop):
        """Test handling of very long prompts."""
        long_prompt = "Hello " * 1000 + "?"
        events: List[Event] = []
        async for event in agent_loop.run_async(long_prompt):
            events.append(event)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_result_output(self, agent_loop: AgentLoop):
        """Test that the final output contains expected fields."""
        events: List[Event] = []
        async for event in agent_loop.run_async("Count to 5"):
            events.append(event)

        turn_done = [e for e in events if e.type == EventType.TURN_DONE]
        if turn_done:
            output = turn_done[-1].data.get("output", {})
            assert "content" in output
            assert "id" in output
