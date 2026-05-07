"""Todo tool - task tracking (Claude Code pattern)."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from maximus.tools.base import Tool, ToolResult
from maximus.models import PermissionLevel


class TodoWriteTool(Tool):
    """Task tracking - create, update, list tasks."""

    name = "todo_write"
    description = "Create or update tasks in the project task list"
    permission_level = PermissionLevel.SAFE
    read_only = False

    parameters = {
        "action": {
            "type": "string",
            "description": "Action: create, update, delete, list",
            "enum": ["create", "update", "delete", "list"]
        },
        "task": {
            "type": "object",
            "description": "Task data (for create/update)",
            "properties": {
                "id": {"type": "string", "description": "Task ID (for update/delete)"},
                "content": {"type": "string", "description": "Task description"},
                "status": {
                    "type": "string", 
                    "description": "Status: pending, in_progress, completed",
                    "enum": ["pending", "in_progress", "completed"]
                },
                "priority": {
                    "type": "string",
                    "description": "Priority: low, medium, high",
                    "enum": ["low", "medium", "high"]
                },
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
    required_params = ["action"]

    def _get_todo_path(self, context: Dict) -> Path:
        """Get the todo file path."""
        workdir = Path(context.get("workdir", "."))
        return workdir / ".maximus" / "todo.json"

    def _load_todos(self, path: Path) -> List[Dict]:
        """Load todos from file."""
        if path.exists():
            try:
                return json.loads(path.read_text())
            except:
                return []
        return []

    def _save_todos(self, path: Path, todos: List[Dict]) -> None:
        """Save todos to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(todos, indent=2))

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        action = args.get("action")
        task_data = args.get("task", {})
        
        todo_path = self._get_todo_path(context)
        todos = self._load_todos(todo_path)

        if action == "create":
            task_id = task_data.get("id") or f"task_{len(todos) + 1}"
            new_task = {
                "id": task_id,
                "content": task_data.get("content", ""),
                "status": task_data.get("status", "pending"),
                "priority": task_data.get("priority", "medium"),
                "tags": task_data.get("tags", []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            todos.append(new_task)
            self._save_todos(todo_path, todos)
            return ToolResult(success=True, data={"task": new_task})

        elif action == "update":
            task_id = task_data.get("id")
            for todo in todos:
                if todo.get("id") == task_id:
                    if "content" in task_data:
                        todo["content"] = task_data["content"]
                    if "status" in task_data:
                        todo["status"] = task_data["status"]
                    if "priority" in task_data:
                        todo["priority"] = task_data["priority"]
                    todo["updated_at"] = datetime.now().isoformat()
                    self._save_todos(todo_path, todos)
                    return ToolResult(success=True, data={"task": todo})
            return ToolResult(success=False, error=f"Task {task_id} not found")

        elif action == "delete":
            task_id = task_data.get("id")
            todos = [t for t in todos if t.get("id") != task_id]
            self._save_todos(todo_path, todos)
            return ToolResult(success=True, data={"deleted": task_id})

        elif action == "list":
            status_filter = task_data.get("status") if task_data else None
            filtered = [t for t in todos if not status_filter or t.get("status") == status_filter]
            return ToolResult(success=True, data={"tasks": filtered, "total": len(filtered)})

        return ToolResult(success=False, error="Invalid action")


class TodoReadTool(Tool):
    """Read task list."""

    name = "todo_read"
    description = "Read tasks from the project task list"
    permission_level = PermissionLevel.SAFE
    read_only = True

    parameters = {
        "status": {
            "type": "string",
            "description": "Filter by status: pending, in_progress, completed",
            "enum": ["pending", "in_progress", "completed"]
        },
        "priority": {
            "type": "string",
            "description": "Filter by priority: low, medium, high",
            "enum": ["low", "medium", "high"]
        }
    }

    def _get_todo_path(self, context: Dict) -> Path:
        workdir = Path(context.get("workdir", "."))
        return workdir / ".maximus" / "todo.json"

    def _load_todos(self, path: Path) -> List[Dict]:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except:
                return []
        return []

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        todo_path = self._get_todo_path(context)
        todos = self._load_todos(todo_path)

        # Filter
        status_filter = args.get("status")
        priority_filter = args.get("priority")

        if status_filter:
            todos = [t for t in todos if t.get("status") == status_filter]
        if priority_filter:
            todos = [t for t in todos if t.get("priority") == priority_filter]

        return ToolResult(
            success=True,
            data={
                "tasks": todos,
                "total": len(todos),
                "pending": len([t for t in todos if t.get("status") == "pending"]),
                "completed": len([t for t in todos if t.get("status") == "completed"])
            }
        )