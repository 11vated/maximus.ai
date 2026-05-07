"""Conversation branching for Maximus.ai - Git-like exploration paths."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import OrderedDict

from pydantic import BaseModel


class BranchCommit(BaseModel):
    """A single commit in a conversation branch."""

    id: str
    parent_id: Optional[str] = None
    timestamp: str
    message: str
    state: str
    goal: str
    plan: Optional[dict] = None
    result: Optional[dict] = None


class Branch(BaseModel):
    """A conversation branch with commit history."""

    name: str
    created_at: str
    head_commit_id: Optional[str] = None
    commits: list[BranchCommit] = []
    is_active: bool = True


class BranchManager:
    """Manages conversation branches with git-like operations."""

    def __init__(self, workdir: str = "."):
        self.workdir = Path(workdir)
        self.branches: dict[str, Branch] = OrderedDict()
        self.current_branch_name: str = "main"
        self._storage_path = self.workdir / ".maximus" / "branches.json"
        self._load()

        if "main" not in self.branches:
            self._create_branch("main", is_initial=True)

    def _load(self) -> None:
        """Load branches from disk."""
        if self._storage_path.exists():
            try:
                data = json.loads(self._storage_path.read_text())
                for name, branch_data in data.get("branches", {}).items():
                    branch = Branch(**branch_data)
                    self.branches[name] = branch
                self.current_branch_name = data.get("current_branch", "main")
            except Exception:
                pass

    def _save(self) -> None:
        """Save branches to disk."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "branches": {name: branch.model_dump() for name, branch in self.branches.items()},
            "current_branch": self.current_branch_name,
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def _create_branch(self, name: str, is_initial: bool = False) -> Branch:
        """Create a new branch."""
        if name in self.branches and not is_initial:
            raise ValueError(f"Branch '{name}' already exists")

        now = datetime.now().isoformat()
        branch = Branch(name=name, created_at=now)
        self.branches[name] = branch
        return branch

    def create_branch(self, name: str, from_commit: Optional[str] = None) -> Branch:
        """Create a new branch from current or specified commit."""
        if name in self.branches:
            raise ValueError(f"Branch '{name}' already exists")

        current = self.get_current_branch()
        new_branch = self._create_branch(name)

        if from_commit:
            source_commit = next((c for c in current.commits if c.id == from_commit), None)
            if source_commit:
                new_branch.commits = [c for c in current.commits if c.timestamp <= source_commit.timestamp]
                new_branch.head_commit_id = from_commit
        else:
            new_branch.commits = current.commits.copy()
            new_branch.head_commit_id = current.head_commit_id

        self._save()
        return new_branch

    def switch_branch(self, name: str) -> Branch:
        """Switch to a different branch."""
        if name not in self.branches:
            raise ValueError(f"Branch '{name}' does not exist")

        self.current_branch_name = name
        self._save()
        return self.branches[name]

    def get_current_branch(self) -> Branch:
        """Get the currently active branch."""
        return self.branches[self.current_branch_name]

    def commit(self, message: str, state: str, goal: str, plan: Optional[dict] = None,
               result: Optional[dict] = None) -> BranchCommit:
        """Create a new commit on the current branch."""
        current = self.get_current_branch()
        commit_id = uuid.uuid4().hex[:8]

        commit = BranchCommit(
            id=commit_id,
            parent_id=current.head_commit_id,
            timestamp=datetime.now().isoformat(),
            message=message,
            state=state,
            goal=goal,
            plan=plan,
            result=result,
        )

        current.commits.append(commit)
        current.head_commit_id = commit_id
        self._save()
        return commit

    def list_branches(self) -> list[dict[str, Any]]:
        """List all branches with metadata."""
        return [
            {
                "name": name,
                "is_active": name == self.current_branch_name,
                "commit_count": len(branch.commits),
                "created_at": branch.created_at,
                "head": branch.head_commit_id,
            }
            for name, branch in self.branches.items()
        ]

    def get_commit_history(self, branch_name: Optional[str] = None, limit: int = 20) -> list[BranchCommit]:
        """Get commit history for a branch."""
        branch = self.branches[branch_name] if branch_name else self.get_current_branch()
        return branch.commits[-limit:]

    def merge_branch(self, source_name: str, target_name: Optional[str] = None) -> None:
        """Merge commits from source branch into target."""
        target_name = target_name or self.current_branch_name
        source = self.branches[source_name]
        target = self.branches[target_name]

        target.commits.extend(source.commits)
        if source.head_commit_id:
            target.head_commit_id = source.head_commit_id

        self._save()

    def delete_branch(self, name: str, force: bool = False) -> None:
        """Delete a branch (cannot delete current or main)."""
        if name == "main":
            raise ValueError("Cannot delete main branch")
        if name == self.current_branch_name and not force:
            raise ValueError("Cannot delete current branch (use force=True)")

        del self.branches[name]
        self._save()

    def get_state_at_commit(self, commit_id: str, branch_name: Optional[str] = None) -> Optional[dict]:
        """Reconstruct agent state at a specific commit."""
        branch = self.branches[branch_name] if branch_name else self.get_current_branch()

        for commit in branch.commits:
            if commit.id == commit_id:
                return {
                    "state": commit.state,
                    "goal": commit.goal,
                    "plan": commit.plan,
                    "result": commit.result,
                    "timestamp": commit.timestamp,
                }
        return None
