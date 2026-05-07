"""Stance system for Maximus.ai - Adaptive behavior modes."""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel


class StanceType(str, Enum):
    """Available stance types for the agent."""

    EXPLORATORY = "exploratory"
    METHODICAL = "methodical"
    CREATIVE = "creative"
    SURGICAL = "surgical"
    ARCHITECTURAL = "architectural"
    DEBUGGING = "debugging"
    LEARNING = "learning"


class StanceConfig(BaseModel):
    """Configuration for a specific stance."""

    stance_type: StanceType
    description: str
    planning_style: str
    tool_preference: list[str]
    temperature_modifier: float = 0.0
    max_iterations_modifier: int = 0
    reflection_depth: str = "normal"


EXPLORATORY_STANCE = StanceConfig(
    stance_type=StanceType.EXPLORATORY,
    description="Broad exploration, try many approaches, learn quickly",
    planning_style="exploratory",
    tool_preference=["grep", "glob", "ls", "read_file", "browse_url", "web_search"],
    temperature_modifier=0.2,
    max_iterations_modifier=5,
    reflection_depth="shallow",
)

METHODICAL_STANCE = StanceConfig(
    stance_type=StanceType.METHODICAL,
    description="Step-by-step, thorough, minimize errors",
    planning_style="methodical",
    tool_preference=["read_file", "write_file", "edit_file", "git_status", "git_diff"],
    temperature_modifier=-0.1,
    max_iterations_modifier=0,
    reflection_depth="deep",
)

CREATIVE_STANCE = StanceConfig(
    stance_type=StanceType.CREATIVE,
    description="Generate novel solutions, think outside the box",
    planning_style="creative",
    tool_preference=["write_file", "execute_shell", "python_runner", "web_search"],
    temperature_modifier=0.3,
    max_iterations_modifier=3,
    reflection_depth="normal",
)

SURGICAL_STANCE = StanceConfig(
    stance_type=StanceType.SURGICAL,
    description="Precise, targeted changes with minimal side effects",
    planning_style="surgical",
    tool_preference=["grep", "edit_file", "read_file", "git_diff"],
    temperature_modifier=-0.2,
    max_iterations_modifier=-3,
    reflection_depth="deep",
)

ARCHITECTURAL_STANCE = StanceConfig(
    stance_type=StanceType.ARCHITECTURAL,
    description="Focus on structure, patterns, and long-term design",
    planning_style="architectural",
    tool_preference=["ls", "grep", "read_file", "glob", "analyze_open_swe", "analyze_clawspring", "analyze_nexus"],
    temperature_modifier=0.0,
    max_iterations_modifier=5,
    reflection_depth="deep",
)

DEBUGGING_STANCE = StanceConfig(
    stance_type=StanceType.DEBUGGING,
    description="Find and fix issues systematically",
    planning_style="debugging",
    tool_preference=["grep", "read_file", "execute_shell", "python_runner", "git_diff"],
    temperature_modifier=-0.1,
    max_iterations_modifier=0,
    reflection_depth="deep",
)

LEARNING_STANCE = StanceConfig(
    stance_type=StanceType.LEARNING,
    description="Understand codebases, document, and teach",
    planning_style="learning",
    tool_preference=["read_file", "ls", "grep", "browse_url", "web_search", "write_file"],
    temperature_modifier=0.1,
    max_iterations_modifier=3,
    reflection_depth="normal",
)


class StanceManager:
    """Manages agent stances and behavior adaptation."""

    def __init__(self, initial_stance: StanceType = StanceType.METHODICAL):
        self.current_stance = initial_stance
        self._stances: Dict[StanceType, StanceConfig] = {
            StanceType.EXPLORATORY: EXPLORATORY_STANCE,
            StanceType.METHODICAL: METHODICAL_STANCE,
            StanceType.CREATIVE: CREATIVE_STANCE,
            StanceType.SURGICAL: SURGICAL_STANCE,
            StanceType.ARCHITECTURAL: ARCHITECTURAL_STANCE,
            StanceType.DEBUGGING: DEBUGGING_STANCE,
            StanceType.LEARNING: LEARNING_STANCE,
        }
        self._history: list[tuple[StanceType, str]] = []

    @property
    def current_config(self) -> StanceConfig:
        """Get the current stance configuration."""
        return self._stances[self.current_stance]

    def switch(self, new_stance: StanceType, reason: str = "") -> None:
        """Switch to a new stance."""
        old = self.current_stance
        self.current_stance = new_stance
        self._history.append((old, reason))
        if len(self._history) > 50:
            self._history.pop(0)

    def get_planning_context(self) -> dict[str, Any]:
        """Get context for the planner based on current stance."""
        config = self.current_config
        return {
            "stance": config.stance_type.value,
            "planning_style": config.planning_style,
            "preferred_tools": config.tool_preference,
            "temperature_modifier": config.temperature_modifier,
            "max_iterations": 10 + config.max_iterations_modifier,
            "reflection_depth": config.reflection_depth,
        }

    def suggest_stance(self, goal: str) -> StanceType:
        """Suggest the best stance for a given goal."""
        goal_lower = goal.lower()

        if any(w in goal_lower for w in ["explore", "discover", "find out", "understand"]):
            return StanceType.EXPLORATORY
        elif any(w in goal_lower for w in ["fix", "bug", "error", "issue", "debug"]):
            return StanceType.DEBUGGING
        elif any(w in goal_lower for w in ["create", "build", "design", "architecture", "structure"]):
            return StanceType.ARCHITECTURAL
        elif any(w in goal_lower for w in ["change", "modify", "update", "edit", "patch"]):
            return StanceType.SURGICAL
        elif any(w in goal_lower for w in ["new", "innovative", "creative", "idea"]):
            return StanceType.CREATIVE
        elif any(w in goal_lower for w in ["learn", "document", "explain", "tutorial"]):
            return StanceType.LEARNING
        else:
            return StanceType.METHODICAL

    def get_available_stances(self) -> list[dict[str, str]]:
        """List all available stances."""
        return [
            {"type": s.stance_type.value, "description": s.description}
            for s in self._stances.values()
        ]
