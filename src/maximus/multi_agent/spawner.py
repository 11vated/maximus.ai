"""Sub-Agent Spawning for Maximus.ai - from ClawSpring patterns."""

import asyncio
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AgentSpec(BaseModel):
    """Specification for spawning a sub-agent."""

    agent_id: str
    agent_type: str
    goal: str
    model: str = "qwen2.5-coder:7b"
    parent_id: Optional[str] = None
    max_iterations: int = 10
    trust_level: str = "basic"


class AgentResult(BaseModel):
    """Result from a sub-agent execution."""

    agent_id: str
    agent_type: str
    success: bool
    output: str
    artifacts: list[str] = []
    error: Optional[str] = None
    duration_ms: float = 0.0


class AgentSpawner:
    """Manages spawning and coordination of specialized sub-agents."""

    AGENT_TYPES = {
        "general": "General-purpose agent for miscellaneous tasks",
        "coder": "Specialized in writing and modifying code",
        "reviewer": "Code review, quality checks, best practices",
        "researcher": "Deep research, documentation, learning",
        "tester": "Test writing, test execution, coverage analysis",
    }

    def __init__(self):
        self.active_agents: dict[str, AgentSpec] = {}
        self.results: dict[str, AgentResult] = {}
        self._history: list[AgentResult] = []

    def spawn(self, agent_type: str, goal: str, model: Optional[str] = None,
             parent_id: Optional[str] = None, **kwargs) -> str:
        """Spawn a new sub-agent and return its ID."""
        if agent_type not in self.AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}. Valid: {list(self.AGENT_TYPES.keys())}")

        agent_id = uuid.uuid4().hex[:8]
        spec = AgentSpec(
            agent_id=agent_id,
            agent_type=agent_type,
            goal=goal,
            model=model or "qwen2.5-coder:7b",
            parent_id=parent_id,
            **kwargs,
        )

        self.active_agents[agent_id] = spec
        return agent_id

    async def execute(self, agent_id: str) -> AgentResult:
        """Execute a sub-agent and return results."""
        if agent_id not in self.active_agents:
            raise ValueError(f"Agent {agent_id} not found")

        spec = self.active_agents[agent_id]
        start_time = datetime.now()

        try:
            from maximus.core.loop import AgentLoop
            from maximus.models import AgentConfig

            config = AgentConfig(model=spec.model, workdir=".")
            agent = AgentLoop(config)

            output_chunks = []
            for event in agent.run(spec.goal):
                if hasattr(event, 'data'):
                    text = event.data.get('text', '')
                    if text:
                        output_chunks.append(text)

            result = AgentResult(
                agent_id=agent_id,
                agent_type=spec.agent_type,
                success=True,
                output="".join(output_chunks),
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        except Exception as e:
            result = AgentResult(
                agent_id=agent_id,
                agent_type=spec.agent_type,
                success=False,
                output="",
                error=str(e),
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        self.results[agent_id] = result
        self._history.append(result)

        if len(self._history) > 100:
            self._history.pop(0)

        return result

    async def execute_all(self, agent_ids: list[str]) -> list[AgentResult]:
        """Execute multiple agents concurrently."""
        tasks = [self.execute(aid) for aid in agent_ids]
        return await asyncio.gather(*tasks)

    def get_result(self, agent_id: str) -> Optional[AgentResult]:
        """Get result for a specific agent."""
        return self.results.get(agent_id)

    def list_types(self) -> dict[str, str]:
        """List available agent types."""
        return dict(self.AGENT_TYPES)

    def list_active(self) -> list[dict[str, Any]]:
        """List all active agents."""
        return [
            {
                "id": spec.agent_id,
                "type": spec.agent_type,
                "goal": spec.goal[:50] + "..." if len(spec.goal) > 50 else spec.goal,
                "model": spec.model,
            }
            for spec in self.active_agents.values()
        ]

    def get_history(self, limit: int = 20) -> list[AgentResult]:
        """Get execution history."""
        return self._history[-limit:]

    def cleanup(self, agent_id: Optional[str] = None) -> None:
        """Clean up agents (stop if running, remove from active)."""
        if agent_id:
            self.active_agents.pop(agent_id, None)
        else:
            self.active_agents.clear()
