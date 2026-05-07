"""Maximus.ai - 100% Free, Unlimited, Capable Coding Agent"""

__version__ = "0.1.0"

from maximus.core import AgentLoop, AgentLoopGenerator
from maximus.models import (
    AgentConfig, CognitiveState, Event, EventType,
    MemoryEntry, MemoryScope, Plan, Step,
    ToolMetadata,
)
from maximus.tools import ToolRegistry, BaseTool, register_tool
from maximus.memory import ShortTermMemory, LongTermMemory
from maximus.intelligence import Planner, Reflector, QualityReport
from maximus.utils import LLMClient, OllamaClient

__all__ = [
    # Core
    "AgentLoop", "AgentLoopGenerator",
    # Models
    "AgentConfig", "CognitiveState", "Event", "EventType",
    "MemoryEntry", "MemoryScope", "Plan", "Step",
    "ToolMetadata",
    # Tools
    "ToolRegistry", "BaseTool", "register_tool",
    # Memory
    "ShortTermMemory", "LongTermMemory",
    # Intelligence
    "Planner", "Reflector", "QualityReport",
    # Utils
    "LLMClient", "OllamaClient",
]
