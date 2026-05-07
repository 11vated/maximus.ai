"""Context compaction for Maximus.ai - 2-layer pipeline with advanced strategies."""

import re
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from collections import defaultdict

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)


class CompactionRule(BaseModel):
    """A rule for rule-based compaction."""
    
    name: str
    pattern: Optional[str] = None
    max_items: Optional[int] = None
    min_priority: Optional[int] = None
    priority: int = 0
    action: str = "remove"  # remove, summarize, truncate
    

DEFAULT_RULES = [
    CompactionRule(name="max_messages", max_items=50, priority=10),
    CompactionRule(name="remove_debug", pattern=r"DEBUG:|debug:", priority=5, action="remove"),
    CompactionRule(name="keep_tool_results", pattern=r"tool_result|ToolResult", priority=8, action="preserve"),
    CompactionRule(name="summarize_long", pattern=r".{500,}", priority=3, action="truncate"),
]


class MessageImportance:
    """Calculate importance score for messages."""
    
    @staticmethod
    def calculate(message: Dict[str, Any], keywords: List[str]) -> float:
        """Calculate importance score (0.0 to 1.0)."""
        content = str(message.get("content", "")).lower()
        score = 0.0
        
        # Check for important keywords
        for keyword in keywords:
            if keyword.lower() in content:
                score += 0.1
        
        # Role-based importance
        role = message.get("role", "")
        if role == "system":
            score += 0.3
        elif role == "user":
            score += 0.2
        elif role == "assistant" and "tool_calls" in message:
            score += 0.25
        
        # Length penalty (very long messages are less important for context)
        if len(content) > 1000:
            score -= 0.1
        
        return min(max(score, 0.0), 1.0)


class CompactionConfig(BaseModel):
    """Configuration for compaction pipeline."""
    
    max_context_tokens: int = 8000
    rule_based_enabled: bool = True
    ai_summary_enabled: bool = True
    preserve_recent: int = 10
    preserve_important: bool = True
    importance_keywords: List[str] = [
        "error", "fail", "success", "complete", "important",
        "decision", "todo", "fix", "bug", "feature"
    ]
    summary_model: str = "qwen2.5-coder:7b"
    max_summary_length: int = 500


class CompactionManager:
    """2-layer context compaction pipeline with advanced strategies."""
    
    def __init__(self, config: Optional[CompactionConfig] = None):
        self.config = config or CompactionConfig()
        self.rules = DEFAULT_RULES
        self.importance_calculator = MessageImportance()
        self.vector_memory = None
        
        # Initialize vector memory if available
        if CHROMADB_AVAILABLE:
            try:
                self.vector_memory = chromadb.Client(Settings(
                    persist_directory="memory_db",
                    anonymized_telemetry=False,
                ))
                self.collection = self.vector_memory.get_or_create_collection(
                    name="maximus_context",
                    metadata={"description": "Context for compaction"}
                )
                logger.info("Vector memory initialized for compaction")
            except Exception as e:
                logger.warning(f"Vector memory init failed: {e}")
                self.vector_memory = None
                self.collection = None
        else:
            self.collection = None
    
    def compact(self, messages: List[Dict], strategy: str = "auto") -> List[Dict]:
        """Compact messages using the 2-layer pipeline.
        
        Strategies:
        - none: No compaction
        - rule_only: Only rule-based
        - ai_only: Only AI summarization
        - auto: Both layers (default)
        """
        if strategy == "none":
            return messages
        
        compacted = messages
        
        if self.config.rule_based_enabled and strategy in ("rule_only", "auto"):
            compacted = self._rule_based_compact(compacted)
        
        if self.config.ai_summary_enabled and strategy in ("ai_only", "auto"):
            compacted = self._ai_compact(compacted)
        
        # Always apply importance preservation if enabled
        if self.config.preserve_important:
            compacted = self._preserve_important(compacted, messages)
        
        return compacted
    
    def _rule_based_compact(self, messages: List[Dict]) -> List[Dict]:
        """Layer 1: Rule-based compaction."""
        result = messages.copy()
        
        # Sort rules by priority (highest first)
        sorted_rules = sorted(self.rules, key=lambda r: -r.priority)
        
        for rule in sorted_rules:
            if rule.action == "remove":
                result = self._apply_removal_rule(result, rule)
            elif rule.action == "preserve":
                # Mark messages to preserve
                continue
            elif rule.action == "truncate":
                result = self._apply_truncation_rule(result, rule)
        
        # Apply max_items constraint
        for rule in sorted_rules:
            if rule.max_items and len(result) > rule.max_items:
                preserve = self.config.preserve_recent
                # Keep most important from the middle
                important = self._select_important(
                    result[:rule.max_items - preserve],
                    count=rule.max_items - preserve
                )
                result = important + result[-preserve:]
        
        return result
    
    def _apply_removal_rule(self, messages: List[Dict], rule: CompactionRule) -> List[Dict]:
        """Apply a removal rule."""
        if not rule.pattern:
            return messages
        
        return [
            m for m in messages
            if not re.search(rule.pattern, str(m.get("content", "")), re.IGNORECASE)
        ]
    
    def _apply_truncation_rule(self, messages: List[Dict], rule: CompactionRule) -> List[Dict]:
        """Truncate long messages."""
        result = []
        for msg in messages:
            content = str(msg.get("content", ""))
            if len(content) > 500:
                msg_copy = msg.copy()
                msg_copy["content"] = content[:500] + "... [truncated]"
                result.append(msg_copy)
            else:
                result.append(msg)
        return result
    
    def _preserve_important(self, compacted: List[Dict], original: List[Dict]) -> List[Dict]:
        """Ensure important messages from original are preserved."""
        preserved_ids = set(id(m) for m in compacted)
        
        for msg in original:
            if id(msg) not in preserved_ids:
                importance = self.importance_calculator.calculate(
                    msg,
                    self.config.importance_keywords
                )
                if importance > 0.5:
                    compacted.append(msg)
        
        return compacted
    
    def _select_important(self, messages: List[Dict], count: int) -> List[Dict]:
        """Select most important messages."""
        scored = [
            (msg, self.importance_calculator.calculate(msg, self.config.importance_keywords))
            for msg in messages
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [msg for msg, _ in scored[:count]]
    
    def _ai_compact(self, messages: List[Dict]) -> List[Dict]:
        """Layer 2: AI-based summarization with local LLM."""
        if len(messages) <= self.config.preserve_recent:
            return messages
        
        preserve = self.config.preserve_recent
        to_summarize = messages[:-preserve]
        
        # Group messages for summarization
        groups = self._group_messages(to_summarize)
        
        summaries = []
        for group in groups:
            summary_text = self._generate_summary(group)
            summaries.append({
                "role": "system",
                "content": f"[Summary: {summary_text}]",
                "metadata": {"is_summary": True, "original_count": len(group)},
            })
        
        return summaries + messages[-preserve:]
    
    def _group_messages(self, messages: List[Dict], group_size: int = 10) -> List[List[Dict]]:
        """Group messages for batch summarization."""
        groups = []
        for i in range(0, len(messages), group_size):
            groups.append(messages[i:i + group_size])
        return groups
    
    def _generate_summary(self, messages: List[Dict]) -> str:
        """Generate summary using local Ollama model."""
        try:
            # TODO: Actually call Ollama here
            # from maximus.utils.llm import OllamaClient
            # client = OllamaClient()
            # prompt = f"Summarize these messages: {json.dumps(messages)}"
            # return client.generate(self.config.summary_model, prompt)
            return f"Summary of {len(messages)} messages covering key discussion points"
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return f"[Summary of {len(messages)} messages]"
    
    def estimate_tokens(self, messages: List[Dict]) -> int:
        """Estimate token count for messages."""
        total = 0
        for msg in messages:
            content = str(msg.get("content", ""))
            # Rough estimation: 1 token ≈ 4 characters
            total += len(content) // 4
        return total
    
    def needs_compaction(self, messages: List[Dict]) -> bool:
        """Check if messages need compaction."""
        return self.estimate_tokens(messages) > self.config.max_context_tokens
    
    def get_compaction_stats(self, before: List[Dict], after: List[Dict]) -> Dict[str, Any]:
        """Get statistics about compaction results."""
        return {
            "messages_before": len(before),
            "messages_after": len(after),
            "tokens_before": self.estimate_tokens(before),
            "tokens_after": self.estimate_tokens(after),
            "reduction_percent": ((len(before) - len(after)) / len(before) * 100) if before else 0,
        }
