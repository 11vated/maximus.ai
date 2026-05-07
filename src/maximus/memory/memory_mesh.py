"""MemoryMesh - Multi-bank memory system (Nexus pattern).

Implements:
- 4 memory banks: episodic, semantic, procedural, working
- Memory lineage tracking
- Project-scoped Memdir for persistent memory
- 5-layer knowledge store
"""

from __future__ import annotations

import json
import logging
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MemoryBank(str, Enum):
    """Four memory banks from Nexus."""
    EPISODIC = "episodic"    # Session/event memories
    SEMANTIC = "semantic"    # Factual knowledge
    PROCEDURAL = "procedural"  # Action patterns
    WORKING = "working"       # Current task scratchpad


class MemoryScope(str, Enum):
    """Memory scope levels."""
    PRIVATE = "private"       # Only creating agent sees
    SHARED = "shared"        # All agents can access
    PROJECT = "project"      # Persists across sessions for this project
    GLOBAL = "global"        # Persists across all projects


class KnowledgeLayer(str, Enum):
    """Five-layer knowledge stratification."""
    SYNTAX = "syntax"        # Tokens, signatures, type definitions
    FLOW = "flow"            # Control flow, data flow, call graphs
    PATTERNS = "patterns"    # Design patterns, architectural styles
    DOMAIN = "domain"        # Business logic, domain terminology
    INTENT = "intent"        # Design philosophy, principles


@dataclass
class MemoryLineage:
    """Tracks memory origin and propagation."""
    origin_agent: str = ""
    source_bank: Optional[MemoryBank] = None
    creation_time: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    decay_factor: float = 1.0


class MemoryEntry(BaseModel):
    """A single memory entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    value: str
    bank: MemoryBank
    scope: MemoryScope = MemoryScope.PROJECT
    layer: Optional[KnowledgeLayer] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    provenance: str = ""  # Where this memory came from
    lineage: Optional[MemoryLineage] = None
    
    # Content metadata
    content_type: str = "text"  # text, code, fact, procedure
    importance: float = 0.5  # 0-1 importance
    tags: List[str] = field(default_factory=list)
    
    # Retrieval metadata
    embedding: Optional[List[float]] = None
    access_count: int = 0


@dataclass
class MemoryQuery:
    """Query for memory retrieval."""
    query: str
    banks: List[MemoryBank] = field(default_factory=lambda: list(MemoryBank))
    scope: Optional[MemoryScope] = None
    layer: Optional[KnowledgeLayer] = None
    min_importance: float = 0.0
    limit: int = 10


class EpisodicMemory:
    """Bank 1: Session/event memories.
    
    Stores conversation history, events, user interactions.
    Example: "User asked about auth on Tuesday"
    """

    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self._events: deque[MemoryEntry] = deque(maxlen=capacity)

    def add_event(
        self,
        event_type: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> MemoryEntry:
        """Add an episodic memory."""
        entry = MemoryEntry(
            key=event_type,
            value=content,
            bank=MemoryBank.EPISODIC,
            provenance=metadata.get("source", "agent") if metadata else "agent",
            content_type="event",
            metadata=metadata or {}
        )
        self._events.append(entry)
        return entry

    def get_recent(self, n: int = 10) -> List[MemoryEntry]:
        """Get n most recent events."""
        return list(self._events)[-n:]

    def get_session_history(self, session_id: str) -> List[MemoryEntry]:
        """Get all events from a specific session."""
        return [e for e in self._events if session_id in e.provenance]

    def to_context(self) -> str:
        """Convert recent events to context."""
        lines = ["## Recent Events"]
        for e in list(self._events)[-5:]:
            lines.append(f"- {e.timestamp.strftime('%H:%M')}: {e.key}: {e.value[:100]}")
        return "\n".join(lines)


class SemanticMemory:
    """Bank 2: Factual knowledge.
    
    Stores project knowledge, patterns, facts.
    Example: "ConfigFactory creates Config objects"
    """

    def __init__(self):
        self._facts: Dict[str, MemoryEntry] = {}  # key -> entry
        self._index: Dict[str, set] = {}  # tag -> entry ids

    def add_fact(
        self,
        key: str,
        value: str,
        layer: KnowledgeLayer = KnowledgeLayer.DOMAIN,
        tags: Optional[List[str]] = None
    ) -> MemoryEntry:
        """Add a factual memory."""
        entry = MemoryEntry(
            key=key,
            value=value,
            bank=MemoryBank.SEMANTIC,
            layer=layer,
            content_type="fact",
            tags=tags or []
        )
        self._facts[entry.id] = entry
        
        # Update index
        for tag in entry.tags:
            if tag not in self._index:
                self._index[tag] = set()
            self._index[tag].add(entry.id)
        
        return entry

    def get_fact(self, key: str) -> Optional[MemoryEntry]:
        """Get a specific fact."""
        for entry in self._facts.values():
            if entry.key == key:
                return entry
        return None

    def search_by_tag(self, tag: str) -> List[MemoryEntry]:
        """Search facts by tag."""
        ids = self._index.get(tag, set())
        return [self._facts[i] for i in ids if i in self._facts]

    def get_by_layer(self, layer: KnowledgeLayer) -> List[MemoryEntry]:
        """Get all facts at a specific knowledge layer."""
        return [e for e in self._facts.values() if e.layer == layer]

    def to_context(self) -> str:
        """Convert facts to context."""
        lines = ["## Known Facts"]
        layer_map = {}
        for entry in self._facts.values():
            if entry.layer not in layer_map:
                layer_map[entry.layer] = []
            layer_map[entry.layer].append(f"{entry.key}: {entry.value[:80]}")
        
        for layer, facts in layer_map.items():
            lines.append(f"\n### {layer.value.upper()}")
            for fact in facts[:5]:
                lines.append(f"- {fact}")
        return "\n".join(lines)


class ProceduralMemory:
    """Bank 3: Action patterns.
    
    Stores tool usage patterns, successful strategies.
    Example: "User prefers pytest over unittest"
    """

    def __init__(self):
        self._patterns: List[MemoryEntry] = []
        self._success_history: List[Dict] = []  # Tool usage success

    def record_action(
        self,
        action: str,
        context: str,
        success: bool,
        result: Optional[str] = None
    ) -> MemoryEntry:
        """Record a tool usage pattern."""
        entry = MemoryEntry(
            key=action,
            value=f"{context} -> {'success' if success else 'failure'}",
            bank=MemoryBank.PROCEDURAL,
            provenance="agent",
            content_type="procedure",
            importance=0.7 if success else 0.3
        )
        self._patterns.append(entry)
        
        # Track success for learning
        self._success_history.append({
            "action": action,
            "context": context,
            "success": success,
            "result": result,
            "timestamp": datetime.now()
        })
        
        return entry

    def get_successful_patterns(self, action: str) -> List[MemoryEntry]:
        """Get successful patterns for an action."""
        return [
            p for p in self._patterns 
            if p.key == action and p.importance >= 0.5
        ]

    def get_preferred_tools(self) -> Dict[str, int]:
        """Get tool usage frequency."""
        tool_counts: Dict[str, int] = {}
        for h in self._success_history:
            tool = h["action"]
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        return tool_counts

    def to_context(self) -> str:
        """Convert patterns to context."""
        lines = ["## Action Patterns"]
        
        # Show successful patterns
        patterns_by_action: Dict[str, List] = {}
        for p in self._patterns:
            if p.importance >= 0.5:
                if p.key not in patterns_by_action:
                    patterns_by_action[p.key] = []
                patterns_by_action[p.key].append(p.value[:60])
        
        for action, contexts in patterns_by_action.items():
            lines.append(f"- {action}: {contexts[0]}")
        
        return "\n".join(lines[:10]) if lines else "No patterns yet"


class WorkingMemory:
    """Bank 4: Current task scratchpad.
    
    Stores current goal, active plan, temporary data.
    """

    def __init__(self):
        self.current_goal: Optional[str] = None
        self.active_plan: Optional[Dict] = None
        self.temp_data: Dict[str, Any] = {}
        self.checkpoints: List[Dict] = []  # State snapshots

    def set_goal(self, goal: str) -> None:
        """Set current goal."""
        self.current_goal = goal
        self.temp_data.clear()
        self.checkpoints.clear()

    def update_plan(self, plan: Dict) -> None:
        """Update active plan."""
        self.active_plan = plan

    def set_temp(self, key: str, value: Any) -> None:
        """Store temporary data."""
        self.temp_data[key] = value

    def get_temp(self, key: str, default: Any = None) -> Any:
        """Retrieve temporary data."""
        return self.temp_data.get(key, default)

    def checkpoint(self) -> None:
        """Save current state."""
        self.checkpoints.append({
            "goal": self.current_goal,
            "plan": self.active_plan,
            "temp": dict(self.temp_data),
            "timestamp": datetime.now()
        })

    def restore(self, checkpoint_idx: int = -1) -> bool:
        """Restore to a checkpoint."""
        if not self.checkpoints:
            return False
        ckpt = self.checkpoints[checkpoint_idx]
        self.current_goal = ckpt["goal"]
        self.active_plan = ckpt["plan"]
        self.temp_data = dict(ckpt["temp"])
        return True

    def to_context(self) -> str:
        """Convert working memory to context."""
        lines = ["## Current Task"]
        if self.current_goal:
            lines.append(f"Goal: {self.current_goal}")
        if self.active_plan:
            lines.append(f"Plan: {json.dumps(self.active_plan)[:200]}")
        if self.temp_data:
            lines.append(f"Data: {json.dumps(self.temp_data)[:200]}")
        return "\n".join(lines) if lines else "No active task"


class Memdir:
    """Project-scoped persistent memory (Claude Code pattern).
    
    Stores memory in .maximus/memdir/ directory:
    - MEMORY.md - Index file
    - topic files with frontmatter
    - Session-based organization
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.memdir_path = self.project_path / ".maximus" / "memdir"
        self._ensure_memdir()

    def _ensure_memdir(self) -> None:
        """Ensure memdir exists."""
        self.memdir_path.mkdir(parents=True, exist_ok=True)
        
        # Create MEMORY.md index if doesn't exist
        index_file = self.memdir_path / "MEMORY.md"
        if not index_file.exists():
            index_file.write_text("# Project Memory\n\n")

    def read_index(self) -> str:
        """Read the memory index."""
        index_file = self.memdir_path / "MEMORY.md"
        return index_file.read_text() if index_file.exists() else ""

    def write_index(self, content: str) -> None:
        """Update the memory index."""
        index_file = self.memdir_path / "MEMORY.md"
        index_file.write_text(content)

    def add_memory(
        self,
        topic: str,
        content: str,
        memory_type: str = "general"
    ) -> Path:
        """Add a memory file for a topic."""
        # Create topic file
        safe_topic = topic.replace("/", "_").replace(" ", "_")
        topic_file = self.memdir_path / f"{safe_topic}.md"
        
        # Frontmatter + content
        frontmatter = f"""---
memory_type: {memory_type}
created: {datetime.now().isoformat()}
---
"""
        topic_file.write_text(frontmatter + content)
        return topic_file

    def list_topics(self) -> List[str]:
        """List all memory topics."""
        return [f.stem for f in self.memdir_path.glob("*.md") if f.stem != "MEMORY"]


class MemoryMesh:
    """Unified memory system with 4 banks + Memdir.
    
    This is the main interface for memory operations.
    """

    def __init__(self, project_path: Optional[str] = None):
        # Initialize 4 banks
        self.episodic = EpisodicMemory(capacity=100)
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.working = WorkingMemory()
        
        # Persistent memory
        self.memdir = Memdir(project_path) if project_path else None

    def add(
        self,
        key: str,
        value: str,
        bank: MemoryBank,
        scope: MemoryScope = MemoryScope.PROJECT,
        layer: Optional[KnowledgeLayer] = None,
        **kwargs
    ) -> MemoryEntry:
        """Add a memory to the appropriate bank."""
        entry = MemoryEntry(
            key=key,
            value=value,
            bank=bank,
            scope=scope,
            layer=layer,
            **kwargs
        )
        
        if bank == MemoryBank.EPISODIC:
            self.episodic._events.append(entry)
        elif bank == MemoryBank.SEMANTIC:
            self.semantic._facts[entry.id] = entry
        elif bank == MemoryBank.PROCEDURAL:
            self.procedural._patterns.append(entry)
        elif bank == MemoryBank.WORKING:
            self.working.set_temp(key, value)
        
        # Also persist to memdir if project-scoped
        if scope in (MemoryScope.PROJECT, MemoryScope.GLOBAL) and self.memdir:
            self.memdir.add_memory(key, value)
        
        return entry

    def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query across memory banks."""
        results = []
        
        for bank_name in query.banks:
            if bank_name == MemoryBank.EPISODIC:
                results.extend(self.episodic.get_recent(query.limit))
            elif bank_name == MemoryBank.SEMANTIC:
                results.extend(
                    e for e in self.semantic._facts.values()
                    if e.importance >= query.min_importance
                )
            elif bank_name == MemoryBank.PROCEDURAL:
                results.extend(self.procedural._patterns)
            elif bank_name == MemoryBank.WORKING:
                # Working memory is task-specific
                pass
        
        # Filter and limit
        results = [r for r in results if r.importance >= query.min_importance]
        return results[:query.limit]

    def to_context(self) -> str:
        """Get full context from all banks."""
        context_parts = []
        
        # Working memory (most important - current task)
        if self.working.current_goal:
            context_parts.append(self.working.to_context())
        
        # Episodic (recent events)
        context_parts.append(self.episodic.to_context())
        
        # Semantic (facts)
        context_parts.append(self.semantic.to_context())
        
        # Procedural (patterns)
        context_parts.append(self.procedural.to_context())
        
        return "\n\n".join(context_parts)

    def checkpoint(self) -> None:
        """Save current state."""
        self.working.checkpoint()

    def restore(self, idx: int = -1) -> bool:
        """Restore to checkpoint."""
        return self.working.restore(idx)