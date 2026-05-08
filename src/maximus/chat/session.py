"""ChatSession - Persistent conversation management.

This implements Claude Code-style continuous chat:
- Maintains message history across turns
- Persists to disk for session resumption
- Supports context injection from memory
- Handles approval workflow for edits
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncGenerator
from uuid import uuid4

from pydantic import BaseModel

from maximus.models import AgentConfig, Event, EventType
from maximus.core.loop import AgentLoop

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = """You are Maximus, a coding assistant. Your ONLY job is to call tools to help the user.

RULES:
1. When you need a tool, output EXACTLY this format (no other text):
TOOL_START{{"name": "TOOL_NAME", "arguments": {{"ARG": "VALUE"}}}}TOOL_END
2. When no tool needed, output regular text
3. Use lowercase for tool names with underscores

EXAMPLES:
User: "list files" → Output: TOOL_START{{"name": "ls", "arguments": {{"path": "."}}}}TOOL_END
User: "read file" → Output: TOOL_START{{"name": "read_file", "arguments": {{"path": "file.py"}}}}TOOL_END

Available tools: ls, read_file, write_file, edit_file, execute_shell, grep, glob

Task: {goal}

Output now:"""


class SessionStatus(str, Enum):
    """Session lifecycle status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class ApprovalState(str, Enum):
    """Edit approval workflow states."""
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_name: Optional[str] = None
    tool_result: Optional[str] = None


class PendingEdit(BaseModel):
    """An edit awaiting user approval."""
    id: str = field(default_factory=lambda: str(uuid4()))
    tool: str
    args: Dict[str, Any]
    diff_content: str
    created_at: datetime = field(default_factory=datetime.now)
    status: ApprovalState = ApprovalState.PENDING


class ChatSession:
    """Persistent chat session with conversation history.
    
    This is the core of Maximus' conversational capability.
    Each session maintains:
    - Message history (all turns)
    - Pending edits awaiting approval
    - Session metadata
    - Memory context
"""
     
    def __init__(
        self,
        session_id: Optional[str] = None,
        workdir: str = ".",
        config: Optional[AgentConfig] = None,
        system_prompt: Optional[str] = None
    ):
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.workdir = Path(workdir)
        self.config = config or AgentConfig(workdir=workdir)
        
        # Message history - the core of conversation
        self.messages: List[Dict[str, Any]] = []
        
        # Pending edits awaiting approval
        self.pending_edits: Dict[str, PendingEdit] = {}
        
        # Session metadata
        self.status = SessionStatus.ACTIVE
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.turn_count = 0
        
        # Project context
        self.project_type: Optional[str] = None
        self.project_context: str = ""
        
        # System prompt customization
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        
        # Agent loop instance (reused across turns)
        self._agent: Optional[AgentLoop] = None
        
        # Session persistence path
        self._session_path = self.workdir / ".maximus" / "sessions" / f"{self.session_id}.json"
        
        # Ensure session directory exists
        self._session_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize with system message
        self._init_system_message()

    def _init_system_message(self) -> None:
        """Initialize the conversation with system prompt."""
        self.messages = [
            {"role": "system", "content": self.system_prompt.format(goal="")}
        ]

    @property
    def agent(self) -> AgentLoop:
        """Get or create the agent loop (reused across turns)."""
        if self._agent is None:
            self._agent = AgentLoop(self.config)
            # Inject existing messages into agent
            self._agent.messages = self.messages.copy()
        return self._agent

    def chat(self, user_input: str) -> AsyncGenerator[Event, None]:
        """Send a message and get response (async generator).
        
        This is the main entry point for chat interaction.
        Maintains conversation context across turns.
        """
        self.last_activity = datetime.now()
        self.turn_count += 1
        
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Inject project context if available
        if self.project_context:
            context_msg = {
                "role": "system",
                "content": f"## Project Context\n{self.project_context}\n\nUse this context to understand the codebase."
            }
            # Insert after system, before user message
            self.messages.insert(1, context_msg)
        
        # Run the agent loop with full history
        try:
            for event in self.agent.run_async(user_input):
                yield event
                
                # Capture assistant responses for history
                if event.type == EventType.TEXT_CHUNK:
                    # This is streamed text - we'll capture final response
                    pass
                    
        except Exception as e:
            logger.error(f"Chat error: {e}")
            self.status = SessionStatus.ERROR
            yield Event(
                type=EventType.ERROR,
                data={"error": str(e), "session_id": self.session_id}
            )
            return
        
        # After completion, save messages to history
        # (The agent loop already updated self.agent.messages)
        self.messages = self.agent.messages.copy()
        
        # Check for pending approval edits
        self._check_pending_edits()

    def _check_pending_edits(self) -> None:
        """Check if any edits need approval."""
        # Tool results are in messages, check for edit_file results
        for msg in self.messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                # If there's a pending edit, mark it
                # This would be enhanced with proper edit tracking

    def add_pending_edit(self, edit: PendingEdit) -> None:
        """Add an edit awaiting user approval."""
        self.pending_edits[edit.id] = edit

    def approve_edit(self, edit_id: str) -> bool:
        """Approve a pending edit."""
        if edit_id not in self.pending_edits:
            return False
        
        edit = self.pending_edits[edit_id]
        edit.status = ApprovalState.APPROVED
        
        # Execute the approved edit
        return True

    def reject_edit(self, edit_id: str) -> bool:
        """Reject a pending edit."""
        if edit_id not in self.pending_edits:
            return False
        
        edit = self.pending_edits[edit_id]
        edit.status = ApprovalState.REJECTED
        del self.pending_edits[edit_id]
        return True

    def get_pending_edits(self) -> List[PendingEdit]:
        """Get all pending edits."""
        return [e for e in self.pending_edits.values() if e.status == ApprovalState.PENDING]

    def set_project_context(self, context: str) -> None:
        """Set project context for this session."""
        self.project_context = context

    def get_history(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        # Skip system messages, return user/assistant
        non_system = [m for m in self.messages if m.get("role") != "system"]
        return non_system[-count:]

    def clear_history(self) -> None:
        """Clear conversation history (keep system prompt)."""
        self._init_system_message()
        if self._agent:
            self._agent.messages = self.messages.copy()

    def save(self) -> None:
        """Persist session to disk."""
        data = {
            "session_id": self.session_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "turn_count": self.turn_count,
            "messages": [
                {k: v.isoformat() if isinstance(v, datetime) else v for k, v in m.items()}
                for m in self.messages
            ],
            "project_type": self.project_type,
            "project_context": self.project_context,
            "pending_edits": [
                {
                    "id": e.id,
                    "tool": e.tool,
                    "args": e.args,
                    "diff_content": e.diff_content,
                    "created_at": e.created_at.isoformat(),
                    "status": e.status.value
                }
                for e in self.pending_edits.values()
            ]
        }
        
        self._session_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Session {self.session_id} saved")

    def load(cls, session_id: str, workdir: str = ".") -> Optional["ChatSession"]:
        """Load session from disk."""
        session_path = Path(workdir) / ".maximus" / "sessions" / f"{session_id}.json"
        
        if not session_path.exists():
            return None
        
        try:
            data = json.loads(session_path.read_text())
            
            session = cls(
                session_id=data["session_id"],
                workdir=workdir
            )
            
            session.status = SessionStatus(data.get("status", "active"))
            session.created_at = datetime.fromisoformat(data["created_at"])
            session.last_activity = datetime.fromisoformat(data["last_activity"])
            session.turn_count = data.get("turn_count", 0)
            session.messages = data.get("messages", [])
            session.project_type = data.get("project_type")
            session.project_context = data.get("project_context", "")
            
            # Restore pending edits
            for e_data in data.get("pending_edits", []):
                edit = PendingEdit(
                    id=e_data["id"],
                    tool=e_data["tool"],
                    args=e_data["args"],
                    diff_content=e_data["diff_content"],
                    created_at=datetime.fromisoformat(e_data["created_at"]),
                    status=ApprovalState(e_data["status"])
                )
                session.pending_edits[edit.id] = edit
            
            logger.info(f"Session {session_id} loaded")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def delete(self) -> bool:
        """Delete session from disk."""
        try:
            if self._session_path.exists():
                self._session_path.unlink()
                logger.info(f"Session {self.session_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    def to_summary(self) -> Dict[str, Any]:
        """Get session summary for listing."""
        user_messages = [m for m in self.messages if m.get("role") == "user"]
        last_user_msg = user_messages[-1]["content"] if user_messages else ""
        
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "turn_count": self.turn_count,
            "message_count": len(self.messages),
            "last_message": last_user_msg[:100] if last_user_msg else "",
            "pending_edits": len(self.get_pending_edits())
        }


class SessionManager:
    """Manager for all chat sessions."""
    
    def __init__(self, workdir: str = "."):
        self.workdir = Path(workdir)
        self.sessions_path = self.workdir / ".maximus" / "sessions"
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        
        # Cache of active sessions
        self._sessions: Dict[str, ChatSession] = {}

    def create_session(
        self,
        workdir: str = ".",
        config: Optional[AgentConfig] = None,
        system_prompt: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            workdir=workdir,
            config=config,
            system_prompt=system_prompt
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID (from cache or disk)."""
        # Check cache first
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # Try to load from disk
        session = ChatSession.load(session_id, str(self.workdir))
        if session:
            self._sessions[session_id] = session
        
        return session

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions."""
        sessions = []
        
        for path in self.sessions_path.glob("*.json"):
            session_id = path.stem
            session = self.get_session(session_id)
            if session:
                sessions.append(session.to_summary())
        
        # Sort by last activity
        sessions.sort(key=lambda s: s["last_activity"], reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        # Remove from cache
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        # Delete from disk
        session_path = self.sessions_path / f"{session_id}.json"
        try:
            if session_path.exists():
                session_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    def cleanup_old_sessions(self, max_sessions: int = 10) -> int:
        """Remove old sessions, keeping most recent."""
        sessions = self.list_sessions()
        
        if len(sessions) <= max_sessions:
            return 0
        
        deleted = 0
        for session in sessions[max_sessions:]:
            if self.delete_session(session["session_id"]):
                deleted += 1
        
        return deleted