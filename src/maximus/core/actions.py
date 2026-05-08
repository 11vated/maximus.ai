"""Action and Observation types for OpenHands-style agent loop.

This defines the structured actions the agent can take and the observations
returned from execution, enabling better tracking and debugging.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """All possible actions the agent can take."""
    # File operations
    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"
    
    # Shell/Command operations
    EXECUTE = "execute"  # Execute shell command
    RUN = "run"          # Run a script/program
    
    # Search/Discovery operations  
    GREP = "grep"
    GLOB = "glob"
    SEARCH = "search"     # Web search
    BROWSE = "browse"     # Web browse
    
    # Git operations
    GIT_STATUS = "git_status"
    GIT_DIFF = "git_diff"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GIT_PULL = "git_pull"
    GIT_BRANCH = "git_branch"
    
    # Tool management
    INSTALL_PACKAGE = "install_package"  # NEW: Auto-install packages
    REGISTER_TOOL = "register_tool"
    CONFIGURE = "configure"
    
    # Agent control
    THINK = "think"           # Internal reasoning
    PLAN = "plan"            # Create a plan
    OBSERVE = "observe"      # Observe results
    REFLECT = "reflect"      # Meta-cognition
    ANSWER = "answer"        # Final response to user
    
    # Memory operations (NEW for OS)
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    MEMORY_SEARCH = "memory_search"
    
    # Discovery operations (NEW for UOSA)
    DISCOVER_PACKAGES = "discover_packages"
    EVALUATE_TOOL = "evaluate_tool"
    PLAN_TOOL_USE = "plan_tool_use"


class ObservationType(str, Enum):
    """Types of observations returned from action execution."""
    # Success
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    
    # Content types
    FILE_CONTENT = "file_content"
    COMMAND_OUTPUT = "command_output"
    SEARCH_RESULTS = "search_results"
    WEB_CONTENT = "web_content"
    GIT_STATUS_OUTPUT = "git_status"
    GIT_DIFF_OUTPUT = "git_diff"
    PACKAGE_INFO = "package_info"
    MEMORY_CONTENT = "memory_content"
    
    # Agent states
    PLAN_CREATED = "plan_created"
    REASONING_COMPLETE = "reasoning_complete"
    REFLECTION_COMPLETE = "reflection_complete"


@dataclass
class Action:
    """A single action to be executed.
    
    This is the primary unit of work in the agent loop.
    Actions are created by the LLM and executed by the Workspace.
    """
    action_type: ActionType
    args: Dict[str, Any] = field(default_factory=dict)
    thought: str = ""  # Why this action was chosen
    id: str = ""       # Unique ID for tracking
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    timeout: Optional[int] = None  # Max execution time in seconds
    sandbox: bool = True           # Run in sandbox?
    
    def __post_init__(self):
        if not self.id:
            self.id = f"{self.action_type.value}_{self.created_at.timestamp()}"


@dataclass
class Observation:
    """Result of executing an action.
    
    Observations are fed back to the agent to inform the next action.
    This is the key to the action-observation loop.
    """
    observation_type: ObservationType
    content: Any = None
    error: Optional[str] = None
    action_id: str = ""  # Links to the action that produced this
    
    # Trace info
    execution_time_ms: float = 0.0
    tool_used: Optional[str] = None
    success: bool = True
    
    # Memory linkage
    memories_created: List[str] = field(default_factory=list)  # IDs of memories written
    
    def __post_init__(self):
        if self.observation_type in (ObservationType.ERROR, ObservationType.TIMEOUT):
            self.success = False


@dataclass
class EventLog:
    """Structured event log for the entire agent run.
    
    This enables:
    - Full replay/debugging of agent decisions
    - Learning from past runs
    - Telemetry and observability
    - Performance analysis
    """
    events: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    
    def add_action(self, action: Action, turn: int):
        """Log an action being taken."""
        self.events.append({
            "type": "action",
            "turn": turn,
            "action_type": action.action_type.value,
            "args": action.args,
            "thought": action.thought,
            "id": action.id,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_observation(self, observation: Observation, turn: int):
        """Log an observation from execution."""
        self.events.append({
            "type": "observation",
            "turn": turn,
            "observation_type": observation.observation_type.value,
            "success": observation.success,
            "execution_time_ms": observation.execution_time_ms,
            "error": observation.error,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_llm_call(self, prompt: str, response: str, turn: int):
        """Log an LLM call (truncated for size)."""
        self.events.append({
            "type": "llm_call",
            "turn": turn,
            "prompt_preview": prompt[:500] if prompt else "",
            "response_preview": response[:500] if response else "",
            "timestamp": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Export event log as dictionary."""
        return {
            "events": self.events,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_events": len(self.events)
        }
    
    def get_trace(self) -> str:
        """Get a human-readable trace of the run."""
        lines = ["=== Agent Run Trace ==="]
        current_turn = -1
        
        for event in self.events:
            if event["turn"] != current_turn:
                current_turn = event["turn"]
                lines.append(f"\n--- Turn {current_turn} ---")
            
            if event["type"] == "action":
                lines.append(f"  → {event['action_type']}: {event.get('args', {})}")
            elif event["type"] == "observation":
                status = "✓" if event.get("success") else "✗"
                lines.append(f"    {status} {event['observation_type']} ({event.get('execution_time_ms', 0):.0f}ms)")
            elif event["type"] == "llm_call":
                lines.append(f"    🤖 LLM called")
        
        return "\n".join(lines)


def action_to_llm_format(action: Action) -> str:
    """Convert action to natural language for LLM context."""
    lines = [f"Action: {action.action_type.value}"]
    
    if action.thought:
        lines.append(f"Thought: {action.thought}")
    
    if action.args:
        lines.append(f"Arguments:")
        for k, v in action.args.items():
            # Truncate long values
            v_str = str(v)[:200] + "..." if len(str(v)) > 200 else str(v)
            lines.append(f"  {k}: {v_str}")
    
    return "\n".join(lines)


def observation_to_llm_format(observation: Observation) -> str:
    """Convert observation to natural language for LLM context."""
    if not observation.success:
        return f"Error: {observation.error or observation.observation_type.value}"
    
    content = observation.content
    if isinstance(content, str):
        # Truncate long outputs
        if len(content) > 2000:
            content = content[:2000] + "\n... [truncated]"
        return content
    
    return str(content)