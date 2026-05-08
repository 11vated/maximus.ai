"""Self-Evolution Framework - Agent learns from workflows.

This enables Maximus to:
- Record successful tool sequences (workflows)
- Learn from feedback (success/failure)
- Write learned patterns to AGENTS.md
- Improve over time without retraining
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    """A recorded workflow - sequence of tool calls that achieved a goal."""
    id: str
    goal: str  # What the workflow achieves
    steps: List[Dict[str, Any]]  # Tool calls with args
    success_rate: float = 1.0
    times_used: int = 0
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_agents_md_entry(self) -> str:
        """Convert to AGENTS.md format."""
        lines = [
            f"### Workflow: {self.goal}",
            "",
            f"Success rate: {self.success_rate*100:.0f}% ({self.times_used} uses)",
            "",
            "```python",
            "# Steps:"
        ]
        
        for i, step in enumerate(self.steps, 1):
            tool = step.get("tool", "unknown")
            args = step.get("args", {})
            lines.append(f"# {i}. {tool}({args})")
        
        lines.extend([
            "```",
            ""
        ])
        
        return "\n".join(lines)


@dataclass
class LearningEntry:
    """A single learning from interaction."""
    id: str
    type: str  # "success", "failure", "pattern", "insight"
    content: str
    context: str  # What task/goal was being worked on
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


class WorkflowLibrary:
    """Library of learned workflows."""
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            storage_path = str(Path.home() / ".maximus" / "workflows.json")
        
        self.storage_path = Path(storage_path)
        self.workflows: Dict[str, Workflow] = {}
        
        # Load existing workflows
        self._load()
    
    def _load(self):
        """Load workflows from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    
                for wf_data in data.get("workflows", []):
                    wf = Workflow(
                        id=wf_data["id"],
                        goal=wf_data["goal"],
                        steps=wf_data["steps"],
                        success_rate=wf_data.get("success_rate", 1.0),
                        times_used=wf_data.get("times_used", 0),
                        created_at=datetime.fromisoformat(wf_data.get("created_at", datetime.now().isoformat()))
                    )
                    self.workflows[wf.id] = wf
                    
                logger.info(f"Loaded {len(self.workflows)} workflows")
            except Exception as e:
                logger.warning(f"Failed to load workflows: {e}")
    
    def _save(self):
        """Save workflows to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "workflows": [
                {
                    "id": wf.id,
                    "goal": wf.goal,
                    "steps": wf.steps,
                    "success_rate": wf.success_rate,
                    "times_used": wf.times_used,
                    "created_at": wf.created_at.isoformat()
                }
                for wf in self.workflows.values()
            ]
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_workflow(
        self,
        goal: str,
        steps: List[Dict[str, Any]],
        success: bool
    ) -> str:
        """Add a new workflow or update an existing one."""
        # Create signature from steps
        signature = hashlib.md5(
            json.dumps(steps, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        workflow_id = f"wf_{signature}"
        
        if workflow_id in self.workflows:
            # Update existing
            wf = self.workflows[workflow_id]
            wf.times_used += 1
            wf.last_used = datetime.now()
            
            # Update success rate
            total = wf.times_used
            old_successes = wf.success_rate * (total - 1)
            new_total = old_successes + (1 if success else 0)
            wf.success_rate = new_total / total
            
        else:
            # Create new
            wf = Workflow(
                id=workflow_id,
                goal=goal,
                steps=steps,
                success_rate=1.0 if success else 0.0,
                times_used=1
            )
            self.workflows[workflow_id] = wf
        
        self._save()
        return workflow_id
    
    def find_similar(self, steps: List[Dict[str, Any]]) -> List[Workflow]:
        """Find workflows with similar steps."""
        # Simple similarity - check if first step matches
        if not steps:
            return []
        
        first_tool = steps[0].get("tool", "")
        
        similar = []
        for wf in self.workflows.values():
            if wf.steps and wf.steps[0].get("tool") == first_tool:
                similar.append(wf)
        
        # Sort by success rate
        similar.sort(key=lambda w: w.success_rate, reverse=True)
        
        return similar[:5]
    
    def get_best_for_goal(self, goal_keywords: str) -> Optional[Workflow]:
        """Find the best workflow for a goal."""
        best = None
        best_score = 0
        
        for wf in self.workflows.values():
            # Simple keyword matching
            if goal_keywords.lower() in wf.goal.lower():
                score = wf.success_rate * (1 + wf.times_used * 0.1)
                if score > best_score:
                    best_score = score
                    best = wf
        
        return best


class LearningSystem:
    """System that learns from agent interactions."""
    
    def __init__(self):
        self.learnings: List[LearningEntry] = []
        self.workflow_library = WorkflowLibrary()
        
        # Load existing learnings
        self._load_learnings()
    
    def _load_learnings(self):
        """Load learnings from storage."""
        learnings_path = Path.home() / ".maximus" / "learnings.json"
        
        if learnings_path.exists():
            try:
                with open(learnings_path, 'r') as f:
                    data = json.load(f)
                    
                for entry_data in data.get("learnings", []):
                    entry = LearningEntry(
                        id=entry_data["id"],
                        type=entry_data["type"],
                        content=entry_data["content"],
                        context=entry_data["context"],
                        timestamp=datetime.fromisoformat(entry_data.get("timestamp", datetime.now().isoformat()))
                    )
                    self.learnings.append(entry)
                    
                logger.info(f"Loaded {len(self.learnings)} learnings")
            except Exception as e:
                logger.warning(f"Failed to load learnings: {e}")
    
    def _save_learnings(self):
        """Save learnings to storage."""
        learnings_path = Path.home() / ".maximus" / "learnings.json"
        learnings_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "learnings": [entry.to_dict() for entry in self.learnings]
        }
        
        with open(learnings_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_success(
        self,
        goal: str,
        steps: List[Dict[str, Any]],
        insight: Optional[str] = None
    ):
        """Record a successful task completion."""
        # Add to workflow library
        self.workflow_library.add_workflow(goal, steps, success=True)
        
        # Add learning entry
        if insight:
            entry = LearningEntry(
                id=f"learn_{len(self.learnings)}",
                type="success",
                content=insight,
                context=goal
            )
            self.learnings.append(entry)
        
        self._save_learnings()
        
        logger.info(f"Recorded success for: {goal[:50]}...")
    
    def record_failure(
        self,
        goal: str,
        steps: List[Dict[str, Any]],
        error: str
    ):
        """Record a failed task."""
        # Add to workflow library with failure
        self.workflow_library.add_workflow(goal, steps, success=False)
        
        # Add learning entry
        entry = LearningEntry(
            id=f"learn_{len(self.learnings)}",
            type="failure",
            content=f"Failed: {error}",
            context=goal
        )
        self.learnings.append(entry)
        
        self._save_learnings()
        
        logger.warning(f"Recorded failure for: {goal[:50]}... Error: {error}")
    
    def get_insights(self, context: str) -> List[str]:
        """Get relevant insights for a context."""
        relevant = []
        
        for entry in self.learnings[-20:]:  # Last 20 learnings
            if context.lower() in entry.context.lower():
                relevant.append(entry.content)
        
        return relevant[-5:]  # Last 5 relevant
    
    def write_agents_md(self, path: str = ".maximus/AGENTS.md"):
        """Write learnings to AGENTS.md for agent context."""
        agents_path = Path(path)
        
        lines = [
            "# Maximus Learned Workflows & Patterns",
            "",
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## High-Performance Workflows",
            ""
        ]
        
        # Add top workflows
        top_workflows = sorted(
            self.workflow_library.workflows.values(),
            key=lambda w: w.success_rate * (1 + w.times_used * 0.1),
            reverse=True
        )[:10]
        
        for wf in top_workflows:
            if wf.success_rate >= 0.5:  # Only show 50%+ success rate
                lines.append(wf.to_agents_md_entry())
        
        # Add recent learnings
        lines.extend([
            "",
            "## Recent Learnings",
            ""
        ])
        
        for entry in self.learnings[-10:]:
            lines.append(f"- **{entry.type}**: {entry.content} (context: {entry.context[:50]}...)")
        
        # Write to file
        agents_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(agents_path, 'w') as f:
            f.write("\n".join(lines))
        
        logger.info(f"Wrote AGENTS.md to {agents_path}")
        
        return str(agents_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        return {
            "total_workflows": len(self.workflow_library.workflows),
            "total_learnings": len(self.learnings),
            "successes": sum(1 for e in self.learnings if e.type == "success"),
            "failures": sum(1 for e in self.learnings if e.type == "failure"),
            "workflows_with_high_success": sum(
                1 for w in self.workflow_library.workflows.values() 
                if w.success_rate >= 0.8
            )
        }


# Global learning system instance
_learning_system: Optional[LearningSystem] = None

def get_learning_system() -> LearningSystem:
    """Get the global learning system instance."""
    global _learning_system
    if _learning_system is None:
        _learning_system = LearningSystem()
    return _learning_system