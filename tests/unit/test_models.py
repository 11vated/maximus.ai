"""Tests for Maximus.ai data models."""

import pytest
from maximus.models import (
    AgentConfig, CognitiveState, MemoryEntry, MemoryScope,
    PermissionLevel, Plan, Step, ToolMetadata, TrustLevel
)


def test_agent_config_defaults():
    """Test AgentConfig defaults."""
    config = AgentConfig()
    assert config.ollama_url == "http://localhost:11434"
    assert config.model == "qwen2.5-coder:7b"
    assert config.max_model_calls == 5000


def test_cognitive_states():
    """Test cognitive state enum."""
    assert CognitiveState.INIT.value == "init"
    assert CognitiveState.PLAN.value == "plan"
    assert len(list(CognitiveState)) == 8


def test_permission_levels():
    """Test permission level enum."""
    assert PermissionLevel.SAFE.value == "safe"
    assert PermissionLevel.WRITE.value == "write"
    assert PermissionLevel.DANGEROUS.value == "dangerous"


def test_trust_levels():
    """Test trust level enum."""
    assert TrustLevel.UNTRUSTED.value == "untrusted"
    assert TrustLevel.PRIVILEGED.value == "privileged"


def test_memory_entry():
    """Test MemoryEntry creation."""
    entry = MemoryEntry(
        id="test123",
        key="test_key",
        value="test_value",
        scope=MemoryScope.PROJECT
    )
    assert entry.id == "test123"
    assert entry.scope == MemoryScope.PROJECT


def test_tool_metadata():
    """Test ToolMetadata creation."""
    meta = ToolMetadata(
        name="test_tool",
        description="A test tool",
        local_only=True
    )
    assert meta.name == "test_tool"
    assert meta.local_only is True


def test_step_creation():
    """Test Step model."""
    step = Step(
        id="1",
        tool="read_file",
        args={"path": "test.py"}
    )
    assert step.id == "1"
    assert step.tool == "read_file"


def test_plan_creation():
    """Test Plan model."""
    plan = Plan(
        id="plan1",
        goal="Test goal",
        steps=[Step(id="1", tool="read_file", args={})]
    )
    assert plan.goal == "Test goal"
    assert len(plan.steps) == 1
