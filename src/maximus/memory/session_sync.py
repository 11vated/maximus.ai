"""Session memory synchronization for Maximus.ai."""

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class SessionStatus(Enum):
    """Session status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class SessionMemory:
    """Session memory for synchronization between agent runs."""

    def __init__(self, session_id: str, workdir: Path):
        self.session_id = session_id
        self.workdir = workdir
        self.memory_path = workdir / ".maximus" / "sessions" / f"{session_id}.json"
        self.history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.status = SessionStatus.ACTIVE
        self.created = datetime.now()
        self.last_updated = datetime.now()

    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add an event to session history."""
        self.history.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })
        self.last_updated = datetime.now()
        self._save()

    def update_context(self, key: str, value: Any) -> None:
        """Update session context."""
        self.context[key] = value
        self.last_updated = datetime.now()
        self._save()

    def _save(self) -> None:
        """Save session to disk."""
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id": self.session_id,
            "status": self.status.value,
            "created": self.created.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "history": self.history,
            "context": self.context,
        }
        with open(self.memory_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    @classmethod
    def load(cls, session_id: str, workdir: Path) -> Optional[SessionMemory]:
        """Load session from disk."""
        memory_path = workdir / ".maximus" / "sessions" / f"{session_id}.json"
        if not memory_path.exists():
            return None

        with open(memory_path, "r") as f:
            data = json.load(f)

        session = cls(session_id, workdir)
        session.status = SessionStatus(data.get("status", "active"))
        session.created = datetime.fromisoformat(data.get("created", datetime.now().isoformat()))
        session.last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        session.history = data.get("history", [])
        session.context = data.get("context", {})
        return session

    def get_recent_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent history items."""
        return self.history[-count:] if self.history else []

    def clear_history(self) -> None:
        """Clear session history."""
        self.history = []
        self._save()

    def set_status(self, status: SessionStatus) -> None:
        """Update session status."""
        self.status = status
        self._save()


class SessionSyncManager:
    """Manager for synchronizing session memories."""

    def __init__(self, workdir: Path):
        self.workdir = workdir
        self.sessions_path = workdir / ".maximus" / "sessions"
        self.active_sessions: Dict[str, SessionMemory] = {}

    def get_or_create_session(self, session_id: str) -> SessionMemory:
        """Get existing session or create new one."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        # Try to load from disk
        session = SessionMemory.load(session_id, self.workdir)
        if session is None:
            session = SessionMemory(session_id, self.workdir)
            session._save()

        self.active_sessions[session_id] = session
        return session

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions."""
        if not self.sessions_path.exists():
            return []

        sessions = []
        for path in self.sessions_path.glob("*.json"):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id"),
                    "status": data.get("status"),
                    "created": data.get("created"),
                    "last_updated": data.get("last_updated"),
                    "event_count": len(data.get("history", [])),
                })
            except Exception:
                continue

        return sorted(sessions, key=lambda x: x.get("last_updated", ""), reverse=True)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        session_path = self.sessions_path / f"{session_id}.json"
        if session_path.exists():
            session_path.unlink()
            self.active_sessions.pop(session_id, None)
            return True
        return False

    def sync_to_agent_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """Sync session memory to agent context."""
        session = self.get_or_create_session(session_id)
        context["session_id"] = session_id
        context["session_history"] = session.get_recent_history(20)
        context["session_context"] = session.context

    def sync_from_agent_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """Sync agent context back to session memory."""
        session = self.get_or_create_session(session_id)
        if "tasks" in context:
            session.update_context("tasks", context["tasks"])
