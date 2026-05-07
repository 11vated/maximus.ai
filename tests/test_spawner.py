"""Tests for AgentSpawner."""

import pytest
import asyncio
from maximus.multi_agent.spawner import AgentSpawner, AgentSpec


def test_spawner_list_types():
    spawner = AgentSpawner()
    types = spawner.list_types()

    assert "general" in types
    assert "coder" in types
    assert "reviewer" in types
    assert "researcher" in types
    assert "tester" in types
    assert len(types) == 5


def test_spawner_spawn():
    spawner = AgentSpawner()
    agent_id = spawner.spawn("coder", "Write a hello world function")

    assert agent_id is not None
    assert len(agent_id) == 8

    active = spawner.list_active()
    assert len(active) == 1
    assert active[0]["type"] == "coder"
    assert "hello world" in active[0]["goal"].lower()


def test_spawner_spawn_invalid_type():
    spawner = AgentSpawner()

    with pytest.raises(ValueError) as exc_info:
        spawner.spawn("invalid_type", "Some goal")

    assert "Unknown agent type" in str(exc_info.value)


def test_spawner_get_result_not_found():
    spawner = AgentSpawner()
    result = spawner.get_result("nonexistent")
    assert result is None


def test_spawner_cleanup():
    spawner = AgentSpawner()
    aid1 = spawner.spawn("general", "Task 1")
    aid2 = spawner.spawn("coder", "Task 2")

    assert len(spawner.active_agents) == 2

    spawner.cleanup(aid1)
    assert len(spawner.active_agents) == 1

    spawner.cleanup()
    assert len(spawner.active_agents) == 0


def test_agent_spec_model():
    spec = AgentSpec(
        agent_id="test123",
        agent_type="reviewer",
        goal="Review code",
        model="deepseek-coder-v2:16b",
    )

    assert spec.agent_id == "test123"
    assert spec.model == "deepseek-coder-v2:16b"


def test_spawner_history_empty():
    spawner = AgentSpawner()
    history = spawner.get_history()
    assert len(history) == 0


@pytest.mark.asyncio
async def test_spawner_execute():
    spawner = AgentSpawner()
    agent_id = spawner.spawn("general", "Print hello")

    result = await spawner.execute(agent_id)

    assert result.agent_id == agent_id
    assert result.agent_type == "general"
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_spawner_execute_invalid():
    spawner = AgentSpawner()

    with pytest.raises(ValueError) as exc_info:
        await spawner.execute("nonexistent")

    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_spawner_execute_all():
    spawner = AgentSpawner()
    aid1 = spawner.spawn("general", "Task 1")
    aid2 = spawner.spawn("coder", "Task 2")

    results = await spawner.execute_all([aid1, aid2])

    assert len(results) == 2
    assert all(r.agent_id in [aid1, aid2] for r in results)
