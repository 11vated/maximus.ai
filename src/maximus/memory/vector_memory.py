"""Vector-based memory system for unlimited context retrieval.

This extends MemoryMesh with:
- Chroma/LanceDB vector storage
- Semantic similarity search
- Context augmentation for LLM prompts
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib

logger = logging.getLogger(__name__)

# Try to import vector DB - fallback to simple implementation if not available
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available, using simple vector fallback")


@dataclass
class MemoryChunk:
    """A retrievable chunk of memory."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    last_accessed: datetime = None
    access_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class SimpleVectorStore:
    """Simple in-memory vector store fallback when ChromaDB unavailable.
    
    Uses simple keyword matching as a fallback.
    """
    
    def __init__(self, collection_name: str = "maximus-memory"):
        self.collection_name = collection_name
        self.chunks: Dict[str, MemoryChunk] = {}
        
    def add(self, chunk: MemoryChunk):
        """Add a memory chunk."""
        self.chunks[chunk.id] = chunk
        
    def search(self, query: str, top_k: int = 5) -> List[MemoryChunk]:
        """Search using simple keyword matching."""
        query_words = set(query.lower().split())
        
        scored = []
        for chunk in self.chunks.values():
            # Simple scoring based on word overlap
            content_words = set(chunk.content.lower().split())
            score = len(query_words & content_words) / max(len(query_words), 1)
            
            if score > 0:
                # Boost by recency and access count
                recency_boost = 1.0 + (chunk.access_count * 0.1)
                scored.append((chunk, score * recency_boost))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Update access times
        for chunk, _ in scored[:top_k]:
            chunk.last_accessed = datetime.now()
            chunk.access_count += 1
        
        return [chunk for chunk, _ in scored[:top_k]]
    
    def delete(self, chunk_id: str):
        """Delete a chunk by ID."""
        if chunk_id in self.chunks:
            del self.chunks[chunk_id]
    
    def count(self) -> int:
        """Count total chunks."""
        return len(self.chunks)


class VectorMemory:
    """Vector-based memory system for retrieval-augmented generation.
    
    This provides "unlimited context" by:
    1. Storing memories as embeddable chunks
    2. Retrieving only the most relevant chunks per query
    3. Augmenting LLM context with retrieved memories
    """
    
    def __init__(
        self, 
        collection_name: str = "maximus-memory",
        persist_directory: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize vector store
        if CHROMADB_AVAILABLE and persist_directory:
            try:
                self.client = chromadb.PersistentClient(path=persist_directory)
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": "Maximus agent memory"}
                )
                self.use_chroma = True
                logger.info(f"ChromaDB initialized at {persist_directory}")
            except Exception as e:
                logger.warning(f"ChromaDB init failed: {e}, using fallback")
                self.use_chroma = False
                self.collection = SimpleVectorStore(collection_name)
        else:
            self.use_chroma = False
            self.collection = SimpleVectorStore(collection_name)
        
        # Configuration
        self.top_k = 10  # Number of memories to retrieve
        self.max_context_length = 4000  # Max chars to add to context
    
    def add_memory(
        self,
        content: str,
        memory_type: str = "general",  # "tool_use", "conversation", "code", "error"
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new memory to the vector store."""
        # Generate ID
        content_hash = hashlib.md5(content.encode()).hexdigest()
        chunk_id = f"{memory_type}_{content_hash[:8]}_{datetime.now().timestamp()}"
        
        chunk = MemoryChunk(
            id=chunk_id,
            content=content,
            metadata=metadata or {"type": memory_type},
            created_at=datetime.now()
        )
        
        # Add to collection
        if self.use_chroma:
            try:
                self.collection.add(
                    ids=[chunk_id],
                    documents=[content],
                    metadatas=[chunk.metadata]
                )
            except Exception as e:
                logger.error(f"Failed to add to ChromaDB: {e}")
        else:
            self.collection.add(chunk)
        
        logger.debug(f"Added memory: {chunk_id} ({memory_type})")
        return chunk_id
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[MemoryChunk]:
        """Retrieve the most relevant memories for a query."""
        top_k = top_k or self.top_k
        
        if self.use_chroma:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=top_k
                )
                
                chunks = []
                if results and results.get("ids"):
                    for i, chunk_id in enumerate(results["ids"][0]):
                        chunks.append(MemoryChunk(
                            id=chunk_id,
                            content=results["documents"][0][i],
                            metadata=results["metadatas"][0][i] if results.get("metadatas") else None
                        ))
                return chunks
            except Exception as e:
                logger.error(f"ChromaDB query failed: {e}")
        
        # Fallback to simple search
        return self.collection.search(query, top_k)
    
    def augment_context(
        self, 
        query: str, 
        current_context: str = ""
    ) -> str:
        """Augment the current context with relevant memories.
        
        This is the key function for "unlimited context" - it retrieves
        relevant memories and appends them to the LLM's context window.
        """
        memories = self.retrieve(query)
        
        if not memories:
            return current_context
        
        # Build augmented context
        memory_section = "\n\n=== Relevant Memories ===\n"
        
        total_length = len(memory_section)
        included_memories = []
        
        for chunk in memories:
            # Check if we have room
            if total_length + len(chunk.content) > self.max_context_length:
                break
                
            memory_entry = f"[{chunk.metadata.get('type', 'unknown')}] {chunk.content}"
            included_memories.append(memory_entry)
            total_length += len(memory_entry) + 2
        
        if included_memories:
            memory_section += "\n".join(included_memories)
            memory_section += "\n=== End Memories ===\n\n"
            
            return current_context + memory_section
        
        return current_context
    
    def add_tool_use_memory(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        success: bool
    ):
        """Add a memory about tool usage for future reference."""
        content = f"Used tool '{tool_name}' with args {args}. Result: {result}. Success: {success}"
        
        self.add_memory(
            content=content,
            memory_type="tool_use",
            metadata={
                "tool": tool_name,
                "success": success,
                "args": json.dumps(args)[:200]
            }
        )
    
    def add_conversation_memory(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None
    ):
        """Add a memory from conversation."""
        self.add_memory(
            content=f"{role}: {content}",
            memory_type="conversation",
            metadata={"role": role, "session": session_id}
        )
    
    def add_error_memory(
        self,
        error: str,
        context: str,
        recovery: Optional[str] = None
    ):
        """Add a memory about an error and recovery."""
        content = f"Error: {error}. Context: {context}"
        if recovery:
            content += f". Recovery: {recovery}"
            
        self.add_memory(
            content=content,
            memory_type="error",
            metadata={"error": error[:100]}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        count = self.collection.count() if self.use_chroma else self.collection.count()
        
        return {
            "total_memories": count,
            "vector_store": "chroma" if self.use_chroma else "simple",
            "collection_name": self.collection_name
        }
    
    def clear(self):
        """Clear all memories."""
        if self.use_chroma:
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name
                )
            except Exception as e:
                logger.error(f"Failed to clear ChromaDB: {e}")
        else:
            self.collection = SimpleVectorStore(self.collection_name)
        
        logger.info("Memory cleared")


# Global vector memory instance
_vector_memory: Optional[VectorMemory] = None

def get_vector_memory(
    persist_directory: Optional[str] = None
) -> VectorMemory:
    """Get the global vector memory instance."""
    global _vector_memory
    if _vector_memory is None:
        _vector_memory = VectorMemory(persist_directory=persist_directory)
    return _vector_memory