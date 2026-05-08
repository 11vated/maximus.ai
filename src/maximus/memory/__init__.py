"""Memory systems for Maximus.ai - MemoryMesh + Vector Memory + legacy support."""

from maximus.memory.short_term import ShortTermMemory
from maximus.memory.long_term import LongTermMemory
from maximus.memory.memory_mesh import (
    MemoryMesh,
    MemoryBank,
    MemoryScope,
    KnowledgeLayer,
    MemoryEntry,
    Memdir,
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
    WorkingMemory,
)
from maximus.memory.vector_memory import (
    VectorMemory,
    get_vector_memory,
    MemoryChunk,
)

__all__ = [
    "MemoryMesh",
    "MemoryBank",
    "MemoryScope", 
    "KnowledgeLayer",
    "MemoryEntry",
    "Memdir",
    "ShortTermMemory",
    "LongTermMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "WorkingMemory",
    "VectorMemory",
    "get_vector_memory",
    "MemoryChunk",
]
