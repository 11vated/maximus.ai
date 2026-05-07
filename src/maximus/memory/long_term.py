"""Long-term memory - persistent store (from ClawSpring + Nexus)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from maximus.models import MemoryEntry, MemoryScope

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Persistent memory store (file-based from ClawSpring, optional ChromaDB)."""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            home = Path.home()
            self.storage_path = home / ".maximus" / "memory"
        else:
            self.storage_path = Path(storage_path)

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._index_file = self.storage_path / "MEMORY.md"
        self._use_vector = False

        # Try to use ChromaDB if available
        try:
            import chromadb
            self._chroma_client = chromadb.Client(chromadb.config.Settings(
                persist_directory=str(self.storage_path / "chroma")
            ))
            self._collection = self._chroma_client.get_or_create_collection("maximus_memory")
            self._use_vector = True
            logger.info("Using ChromaDB for long-term memory")
        except ImportError:
            logger.info("ChromaDB not available, using file-based storage")
            self._chroma_client = None
            self._collection = None

    def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        if self._use_vector and self._collection:
            self._collection.add(
                documents=[entry.value],
                metadatas=[{
                    "key": entry.key,
                    "scope": entry.scope.value,
                    "provenance": entry.provenance,
                    "confidence": entry.confidence,
                }],
                ids=[entry.id],
            )
        else:
            # File-based storage
            self._append_to_file(entry)

    def search(self, query: str, k: int = 5) -> List[MemoryEntry]:
        """Search long-term memory."""
        if self._use_vector and self._collection:
            results = self._collection.query(query_texts=[query], n_results=k)
            return self._results_to_entries(results)
        else:
            return self._search_file_based(query, k)

    def _append_to_file(self, entry: MemoryEntry) -> None:
        """Append entry to MEMORY.md file (ClawSpring pattern)."""
        with open(self._index_file, "a", encoding="utf-8") as f:
            f.write(f"\n## {entry.key}\n")
            f.write(f"Scope: {entry.scope.value} | Confidence: {entry.confidence}\n")
            f.write(f"Provenance: {entry.provenance}\n")
            f.write(f"Timestamp: {entry.timestamp.isoformat()}\n")
            f.write(f"\n{entry.value}\n")

    def _search_file_based(self, query: str, k: int) -> List[MemoryEntry]:
        """Simple search in file-based storage."""
        if not self._index_file.exists():
            return []

        results = []
        query_lower = query.lower()

        with open(self._index_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple split by "## " to get entries
        entries = content.split("\n## ")
        for entry_text in entries[1:]:  # Skip header
            if query_lower in entry_text.lower() and len(results) < k:
                # Parse basic info
                lines = entry_text.split("\n")
                key = lines[0].strip()
                results.append(MemoryEntry(
                    id=str(hash(entry_text)),
                    key=key,
                    value=entry_text[:500],
                    scope=MemoryScope.PROJECT,
                ))

        return results

    def _results_to_entries(self, results: dict) -> List[MemoryEntry]:
        """Convert ChromaDB results to MemoryEntry objects."""
        entries = []
        if results and "documents" in results:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if "metadatas" in results else {}
                entries.append(MemoryEntry(
                    id=results["ids"][0][i],
                    key=metadata.get("key", "unknown"),
                    value=doc,
                    scope=MemoryScope(metadata.get("scope", "project")),
                    provenance=metadata.get("provenance", ""),
                    confidence=metadata.get("confidence", 1.0),
                ))
        return entries

    def export_index(self) -> str:
        """Export memory index as markdown (for system prompt injection)."""
        if self._index_file.exists():
            return self._index_file.read_text(encoding="utf-8")
        return ""
