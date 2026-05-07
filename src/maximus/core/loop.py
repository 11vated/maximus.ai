"""Agent loop - 8-state cognitive loop (Nexus) with event streaming (ClawSpring)."""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

from maximus.models import (
    AgentConfig, CognitiveState, Event, EventType, Output, Step, Plan
)
from maximus.tools.registry import get_registry

logger = logging.getLogger(__name__)


class AgentLoop:
    """Hybrid agent loop: Nexus 8-state machine + ClawSpring event streaming."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.state = CognitiveState.INIT
        # Register builtin tools if not already registered
        from maximus.tools.builtin import register_builtin_tools
        register_builtin_tools()
        self.registry = get_registry()
        self.planner = None
        self.reflector = None
        self.memory = None
        self.model_calls = 0

    def run(self, goal: str) -> "AgentLoopGenerator":
        """Main entry point: returns a generator wrapper."""
        return AgentLoopGenerator(self, goal)

    async def run_async(self, goal: str) -> AsyncGenerator[Event, None]:
        """Async generator yielding events throughout agent execution."""
        self.state = CognitiveState.INIT
        yield Event(type=EventType.STATE_CHANGE, data={"state": self.state.value})

        # INIT: Setup
        self.state = CognitiveState.PLAN
        yield Event(type=EventType.STATE_CHANGE, data={"state": self.state.value})

        # PLAN: Create plan
        from maximus.intelligence.planner import Planner
        if not self.planner:
            self.planner = Planner(self.config)

        plan = await self.planner.create_plan(goal)
        yield Event(type=EventType.STATE_CHANGE, data={"state": "plan_created", "plan_id": plan.id})

        # ACT: Execute steps
        self.state = CognitiveState.ACT
        yield Event(type=EventType.STATE_CHANGE, data={"state": self.state.value})

        results = []
        for step in plan.steps:
            yield Event(type=EventType.TOOL_START, data={"tool": step.tool, "step_id": step.id})

            result = await self._execute_step(step, plan)
            results.append(result)

            yield Event(type=EventType.TOOL_END, data={"tool": step.tool, "result": result})

        # OBSERVE: Collect results
        self.state = CognitiveState.OBSERVE
        yield Event(type=EventType.STATE_CHANGE, data={"state": self.state.value})

        # REFLECT: Quality assessment
        self.state = CognitiveState.REFLECT
        yield Event(type=EventType.STATE_CHANGE, data={"state": self.state.value})

        from maximus.intelligence.reflector import Reflector
        if not self.reflector:
            self.reflector = Reflector(self.config)

        quality = await self.reflector.assess(plan, results)
        yield Event(type=EventType.STATE_CHANGE, data={"state": "reflection_done", "quality": quality.dict()})

        if quality.needs_revision and quality.confidence < 0.8:
            self.state = CognitiveState.ADAPT
            yield Event(type=EventType.STATE_CHANGE, data={"state": self.state.value})
            yield Event(type=EventType.STATE_CHANGE, data={"state": "adaptation_done"})

        # COMMIT: Finalize
        self.state = CognitiveState.COMMIT
        yield Event(type=EventType.STATE_CHANGE, data={"state": self.state.value})

        output = Output(
            id=f"output_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            type="report",
            content=f"Completed goal: {goal}\nSteps: {len(plan.steps)}\nResults: {len(results)}"
        )

        # PAUSE: Done
        self.state = CognitiveState.PAUSE
        yield Event(type=EventType.STATE_CHANGE, data={"state": self.state.value})
        yield Event(type=EventType.TURN_DONE, data={"output": output.dict()})

    async def _execute_step(self, step: Step, plan: Plan) -> Dict[str, Any]:
        """Execute a single step."""
        tool = self.registry.get(step.tool)
        if not tool:
            return {"success": False, "error": f"Tool '{step.tool}' not found"}

        if self.model_calls >= self.config.max_model_calls:
            return {"success": False, "error": "Model call limit reached"}

        try:
            result = await tool.execute(step.args, {"workdir": self.config.workdir})
            return result
        except Exception as e:
            logger.error(f"Step {step.id} failed: {e}")
            return {"success": False, "error": str(e)}


class AgentLoopGenerator:
    """Synchronous generator wrapper for AgentLoop."""

    def __init__(self, loop: AgentLoop, goal: str):
        self._loop = loop
        self._goal = goal
        self._async_gen = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._async_gen is None:
            import asyncio
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())
            self._async_gen = self._loop.run_async(self._goal)

        import asyncio
        try:
            return asyncio.get_event_loop().run_until_complete(self._async_gen.__anext__())
        except StopAsyncIteration:
            raise StopIteration
