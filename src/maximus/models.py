"""Data models for Maximus.ai agent framework."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CognitiveState(str, Enum):
    """Eight-state cognitive loop from Nexus."""

    INIT = "init"
    PLAN = "plan"
    ACT = "act"
    OBSERVE = "observe"
    REFLECT = "reflect"
    ADAPT = "adapt"
    COMMIT = "commit"
    PAUSE = "pause"


class Stance(str, Enum):
    """Seven adaptive behavior modes from Nexus."""

    EXPLORATORY = "exploratory"
    METHODICAL = "methodical"
    AGGRESSIVE = "aggressive"
    CAUTIOUS = "cautious"
    COLLABORATIVE = "collaborative"
    DEBUGGING = "debugging"
    LEARNING = "learning"


class PermissionLevel(str, Enum):
    """Tool permission levels from ClawSpring."""

    SAFE = "safe"
    WRITE = "write"
    DANGEROUS = "dangerous"


class TrustLevel(str, Enum):
    """Four-level trust system from Nexus."""

    UNTRUSTED = "untrusted"
    BASIC = "basic"
    VERIFIED = "verified"
    PRIVILEGED = "privileged"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MemoryScope(str, Enum):
    USER = "user"
    PROJECT = "project"
    FEEDBACK = "feedback"
    REFERENCE = "reference"


class Step(BaseModel):
    """A single executable step in a plan."""

    id: str
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)
    deps: List[str] = Field(default_factory=list)
    timeout: Optional[int] = 300


class Plan(BaseModel):
    """LLM-generated task decomposition."""

    id: str
    goal: str
    repo_ids: List[str] = Field(default_factory=list)
    steps: List[Step] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    estimated_cost: float = 0.0
    success_criteria: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    """A task to be executed by the agent."""

    id: str
    repo_id: str
    goal_id: str
    input: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    planned_steps: List[Step] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Output] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Output(BaseModel):
    """Result of a task or step execution."""

    id: str
    type: str = "report"
    content: str
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryEntry(BaseModel):
    """A memory stored in short or long-term memory."""

    id: str
    key: str
    value: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    provenance: str = ""
    confidence: float = 1.0
    scope: MemoryScope = MemoryScope.PROJECT


class ToolMetadata(BaseModel):
    """Metadata for tool registration from ClawSpring."""

    name: str
    description: str = ""
    read_only: bool = True
    concurrent_safe: bool = True
    permission_level: PermissionLevel = PermissionLevel.SAFE
    local_only: bool = True
    categories: List[str] = Field(default_factory=list)


class AgentConfig(BaseModel):
    """Configuration for Maximus agent."""

    ollama_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    max_model_calls: int = 5000
    trust_level: TrustLevel = TrustLevel.BASIC
    permission_mode: str = "auto"
    max_concurrent_tools: int = 5
    context_window: int = 128000
    compaction_threshold: float = 0.7
    workdir: str = "."


class EventType(str, Enum):
    """Event types from ClawSpring agent loop."""

    TEXT_CHUNK = "text_chunk"
    THINKING_CHUNK = "thinking_chunk"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TURN_DONE = "turn_done"
    PERMISSION_REQUEST = "permission_request"
    STATE_CHANGE = "state_change"


class Event(BaseModel):
    """An event emitted during agent execution."""

    type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
