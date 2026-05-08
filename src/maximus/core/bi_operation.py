"""Bi-Operation Interface - OS and Agent as true partners.

This enables:
- OS monitoring LLM outputs for issues
- Proactive memory injection without LLM asking
- Loop detection and intervention
- Parallel symbolic reasoning
- Real-time feedback and correction
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import re

logger = logging.getLogger(__name__)


@dataclass
class BiOpConfig:
    """Configuration for bi-operative features."""
    # Loop detection
    enable_loop_detection: bool = True
    loop_threshold: int = 3  # Repeat same action N times = loop
    loop_cooldown: int = 2  # Steps to take before allowing same action
    
    # Proactive injection
    enable_proactive_injection: bool = True
    max_injections_per_turn: int = 2
    
    # Parallel verification
    enable_parallel_verification: bool = True
    
    # Memory injection
    enable_memory_injection: bool = True
    context_threshold: int = 2000  # Characters before triggering injection


@dataclass
class Intervention:
    """An intervention from the OS to the LLM."""
    type: str  # "loop_detected", "memory_inject", "correction", "verification"
    content: str
    priority: int = 0  # 0 = low, 1 = medium, 2 = high
    metadata: Dict[str, Any] = field(default_factory=dict)


class LoopDetector:
    """Detects when the agent is stuck in a loop."""
    
    def __init__(self, config: BiOpConfig):
        self.config = config
        self.action_history: deque = deque(maxlen=50)
        self.action_counts: Dict[str, int] = {}
        
    def record_action(self, action_type: str, action_args: Dict[str, Any]):
        """Record an action for loop detection."""
        # Create a simple signature of the action
        signature = f"{action_type}:{str(sorted(action_args.items()))[:50]}"
        
        self.action_history.append({
            "signature": signature,
            "timestamp": datetime.now()
        })
        
        # Update counts
        self.action_counts[signature] = self.action_counts.get(signature, 0) + 1
        
    def detect_loop(self) -> Optional[Intervention]:
        """Check if we're in a loop and return intervention if so."""
        if not self.config.enable_loop_detection:
            return None
        
        # Check for repeated actions
        for signature, count in self.action_counts.items():
            if count >= self.config.loop_threshold:
                # Get the last few actions to understand context
                recent = list(self.action_history)[-5:]
                
                intervention = Intervention(
                    type="loop_detected",
                    content=f"⚠️ Detected repeated action pattern: {signature.split(':')[0]} (occurred {count} times). Consider a different approach.",
                    priority=1,
                    metadata={
                        "signature": signature,
                        "count": count,
                        "recent_actions": [a["signature"] for a in recent]
                    }
                )
                
                # Reset the counter to prevent spam
                self.action_counts[signature] = 0
                
                return intervention
        
        return None
    
    def reset(self):
        """Reset the detector."""
        self.action_history.clear()
        self.action_counts.clear()


class ProactiveInjector:
    """Injects relevant memories/context without LLM asking."""
    
    def __init__(self, config: BiOpConfig):
        self.config = config
        self.vector_memory = None  # Will be set later
        
    def set_vector_memory(self, vm):
        """Set the vector memory reference."""
        self.vector_memory = vm
        
    def check_and_inject(
        self, 
        context: str, 
        current_step: int
    ) -> Optional[Intervention]:
        """Check if we should inject something proactively."""
        if not self.config.enable_proactive_injection:
            return None
            
        if not self.vector_memory:
            return None
        
        # Check context length
        if len(context) < self.config.context_threshold:
            return None
        
        # Get relevant memories
        memories = self.vector_memory.retrieve(context, top_k=2)
        
        if memories:
            injection = Intervention(
                type="memory_inject",
                content=f"💡 Remember: {memories[0].content[:200]}...",
                priority=0,
                metadata={"memories_found": len(memories)}
            )
            
            return injection
        
        return None


class ParallelVerifier:
    """Runs symbolic verification in parallel with LLM."""
    
    def __init__(self, config: BiOpConfig):
        self.config = config
        
    async def verify_reasoning(
        self,
        action: str,
        args: Dict[str, Any],
        context: str
    ) -> Optional[Intervention]:
        """Verify the reasoning before execution."""
        if not self.config.enable_parallel_verification:
            return None
        
        # Simple verification checks
        issues = []
        
        # Check for dangerous commands
        dangerous_patterns = [
            (r"rm\s+-rf\s+/", "Deleting root directory"),
            (r">\s*/dev/", "Writing to device file"),
            (r"chmod\s+777", "Overly permissive permissions"),
        ]
        
        if action == "execute":
            command = args.get("command", "")
            for pattern, description in dangerous_patterns:
                if re.search(pattern, command):
                    issues.append(f"⚠️ Safety check: {description}")
        
        # Check for file operations in wrong location
        if action in ["write", "edit"]:
            path = args.get("path", "")
            if path.startswith("/etc") or path.startswith("/sys"):
                issues.append(f"⚠️ System directory access: {path}")
        
        if issues:
            return Intervention(
                type="correction",
                content=" ".join(issues),
                priority=2,
                metadata={"issues": issues}
            )
        
        return None


class BiOperationInterface:
    """The core bi-operation system - OS and LLM as partners.
    
    This system:
    - Monitors the agent's actions
    - Detects issues (loops, errors, risks)
    - Provides proactive interventions
    - Augments context without waiting for LLM to ask
    """
    
    def __init__(self, config: Optional[BiOpConfig] = None):
        self.config = config or BiOpConfig()
        
        # Initialize sub-systems
        self.loop_detector = LoopDetector(self.config)
        self.proactive_injector = ProactiveInjector(self.config)
        self.parallel_verifier = ParallelVerifier(self.config)
        
        # Set vector memory reference
        self._vector_memory = None
        
        # History
        self.interventions_history: List[Intervention] = []
        self.total_interventions = 0
        
    def set_vector_memory(self, vm):
        """Set the vector memory for proactive injection."""
        self._vector_memory = vm
        self.proactive_injector.set_vector_memory(vm)
    
    async def process_action(
        self,
        action_type: str,
        action_args: Dict[str, Any],
        context: str,
        current_step: int
    ) -> List[Intervention]:
        """Process an action and return any interventions.
        
        This is called AFTER the LLM decides on an action but BEFORE execution.
        It gives the OS a chance to intervene.
        """
        interventions = []
        
        # 1. Loop detection
        loop_intervention = self.loop_detector.record_action(action_type, action_args)
        loop_check = self.loop_detector.detect_loop()
        if loop_check:
            interventions.append(loop_check)
            self.total_interventions += 1
        
        # 2. Parallel verification
        if self.config.enable_parallel_verification:
            verify = await self.parallel_verifier.verify_reasoning(
                action_type, action_args, context
            )
            if verify:
                interventions.append(verify)
                self.total_interventions += 1
        
        # 3. Proactive injection (only if high priority intervention not already)
        if (
            self.config.enable_proactive_injection 
            and len(interventions) < self.config.max_injections_per_turn
        ):
            injection = self.proactive_injector.check_and_inject(context, current_step)
            if injection:
                interventions.append(injection)
                self.total_interventions += 1
        
        # Record for history
        self.interventions_history.extend(interventions)
        
        return interventions
    
    def get_intervention_prompt(self, interventions: List[Intervention]) -> str:
        """Convert interventions to a prompt suffix for the LLM."""
        if not interventions:
            return ""
        
        lines = ["\n\n=== System Observations ==="]
        
        # Sort by priority
        sorted_interventions = sorted(interventions, key=lambda x: x.priority, reverse=True)
        
        for intervention in sorted_interventions:
            lines.append(f"- {intervention.content}")
        
        lines.append("=== End Observations ===\n")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bi-operation statistics."""
        return {
            "total_interventions": self.total_interventions,
            "loop_detections": sum(1 for i in self.interventions_history if i.type == "loop_detected"),
            "memory_injections": sum(1 for i in self.interventions_history if i.type == "memory_inject"),
            "corrections": sum(1 for i in self.interventions_history if i.type == "correction"),
            "enabled": {
                "loop_detection": self.config.enable_loop_detection,
                "proactive_injection": self.config.enable_proactive_injection,
                "parallel_verification": self.config.enable_parallel_verification,
            }
        }
    
    def reset(self):
        """Reset the bi-operation state."""
        self.loop_detector.reset()
        self.interventions_history.clear()


# Global bi-operation interface
_bi_op_interface: Optional[BiOperationInterface] = None

def get_bi_operation_interface(config: Optional[BiOpConfig] = None) -> BiOperationInterface:
    """Get the global bi-operation interface instance."""
    global _bi_op_interface
    if _bi_op_interface is None:
        _bi_op_interface = BiOperationInterface(config)
    return _bi_op_interface