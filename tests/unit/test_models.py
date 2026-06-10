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


# --- Phase D / MemoryMesh KG harness tests (expand deterministic coverage for Graphiti cross + gem ingest paths) ---
def test_knowledge_graph_memory():
    """Test direct KG node/edge ops (core of mcp-knowledge-graph integration)."""
    from maximus.memory.memory_mesh import KnowledgeGraphMemory
    kg = KnowledgeGraphMemory()
    kg.add_relation("Maximus", "uses", "KnowledgeGraphMemory")
    assert len(kg._edges) >= 1
    res = kg.query_related("Maximus", limit=5)
    assert len(res) >= 1
    assert any(r.get("type") in ("edge", "node") for r in res)


def test_memory_mesh_kg_methods():
    """Test MemoryMesh KG extensions (add_knowledge_triple, query, context inclusion)."""
    from maximus.memory.memory_mesh import MemoryMesh, KnowledgeLayer
    mesh = MemoryMesh()
    # add via helper (exercises binding + dual semantic+kg write)
    entry = mesh.add_knowledge_triple(
        "AgentLoop", "integrates", "KG+MemoryMesh",
        layer=KnowledgeLayer.DOMAIN, tags=["phase_d"], provenance="test"
    )
    assert entry is not None
    assert len(mesh.knowledge_graph._edges) >= 1
    # query
    qres = mesh.query_knowledge_graph("AgentLoop", limit=5)
    assert len(qres) >= 1
    # context includes KG section
    ctx = mesh.to_context()
    assert "Knowledge Graph" in ctx or "kg" in ctx.lower()


def test_kg_ingest_shape():
    """Smoke shape for ingest bridge (mcp -> mesh). Does not require live MCP server."""
    from maximus.memory.memory_mesh import MemoryMesh
    mesh = MemoryMesh()
    # Simulate what ingest_knowledge_from_mcp_to_mesh would do
    mesh.add_knowledge_triple("test_subject", "test_pred", "test_obj", provenance="mcp:knowledge-graph")
    assert any("mcp:knowledge-graph" in str(e) for e in mesh.knowledge_graph._edges)
