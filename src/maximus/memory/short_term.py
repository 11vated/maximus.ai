"""Short-term memory - rolling window (from Nexus + ClawSpring)."""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Dict, List, Optional

from maximus.models import MemoryEntry, MemoryScope

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """Session-scoped rolling window memory (from Nexus)."""

    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self._window: deque[MemoryEntry] = deque(maxlen=capacity)
        self._recent_queries: List[str] = []

    def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry to short-term memory."""
        self._window.append(entry)

    def get_recent(self, n: int = 10) -> List[MemoryEntry]:
        """Get n most recent entries."""
        return list(self._window)[-n:] if self._window else []

    def search(self, query: str, n: int = 5) -> List[MemoryEntry]:
        """Simple keyword search in recent entries."""
        results = []
        query_lower = query.lower()

        for entry in reversed(self._window):
            if query_lower in entry.key.lower() or query_lower in entry.value.lower():
                results.append(entry)
                if len(results) >= n:
                    break

        return results

    def clear(self) -> None:
        """Clear short-term memory."""
        self._window.clear()

    def __len__(self) -> int:
        return len(self._window)

    def to_context(self) -> str:
        """Convert to context string for LLM."""
        lines = []
        for entry in self._window:
            lines.append(f"[{entry.scope.value}] {entry.key}: {entry.value[:200]}")
        return "\n".join(lines)
