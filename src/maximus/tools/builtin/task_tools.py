"""Task and Todo management tools for Maximus.ai."""

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from maximus.tools.base import BaseTool
from maximus.models import ToolMetadata, PermissionLevel


class TodoWriteTool(BaseTool):
    """Write/update todo list for task tracking."""

    def __init__(self):
        metadata = ToolMetadata(
            name="todo_write",
            description="Write or update the todo list for task tracking",
            permission_level=PermissionLevel.SAFE,
            read_only=False,
            local_only=True,
            categories=["task", "memory"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Write todo list to file.

        Args:
            args: Should contain 'todos' list with items having:
                - content: Task description
                - status: pending|in_progress|completed|cancelled
                - priority: high|medium|low
            context: Execution context

        Returns:
            Dict with success status
        """
        try:
            todos = args.get("todos", [])
            workdir = Path(context.get("workdir", "."))

            # Validate todos structure
            validated = []
            for todo in todos:
                validated.append({
                    "content": todo.get("content", ""),
                    "status": todo.get("status", "pending"),
                    "priority": todo.get("priority", "medium"),
                    "created": todo.get("created", datetime.now().isoformat()),
                })

            # Save to .maximus/todos.json
            todo_file = workdir / ".maximus" / "todos.json"
            todo_file.parent.mkdir(parents=True, exist_ok=True)

            with open(todo_file, "w") as f:
                json.dump({"todos": validated, "updated": datetime.now().isoformat()}, f, indent=2)

            return {"success": True, "count": len(validated), "path": str(todo_file)}

        except Exception as e:
            return {"success": False, "error": str(e)}


class TodoReadTool(BaseTool):
    """Read current todo list."""

    def __init__(self):
        metadata = ToolMetadata(
            name="todo_read",
            description="Read the current todo list",
            permission_level=PermissionLevel.SAFE,
            read_only=True,
            local_only=True,
            categories=["task", "memory"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Read todo list from file.

        Returns:
            Dict with todos list
        """
        try:
            workdir = Path(context.get("workdir", "."))
            todo_file = workdir / ".maximus" / "todos.json"

            if not todo_file.exists():
                return {"success": True, "todos": [], "count": 0}

            with open(todo_file, "r") as f:
                data = json.load(f)

            return {"success": True, **data}

        except Exception as e:
            return {"success": False, "error": str(e)}


class TaskCreateTool(BaseTool):
    """Create a new task for sub-agent execution."""

    def __init__(self):
        metadata = ToolMetadata(
            name="task_create",
            description="Create a new task for sub-agent execution",
            permission_level=PermissionLevel.SAFE,
            read_only=False,
            local_only=False,
            categories=["task", "multi_agent"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task.

        Args:
            args: Should contain 'description', optional 'agent_type', 'priority'

        Returns:
            Dict with task ID
        """
        try:
            from maximus.multi_agent.spawner import AgentSpawner, AgentType

            description = args.get("description", "")
            agent_type = args.get("agent_type", "general")
            priority = args.get("priority", "medium")

            if not description:
                return {"success": False, "error": "No task description provided"}

            spawner = AgentSpawner()
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Store task in context for tracking
            tasks = context.get("tasks", {})
            tasks[task_id] = {
                "description": description,
                "agent_type": agent_type,
                "priority": priority,
                "status": "created",
                "created": datetime.now().isoformat(),
            }
            context["tasks"] = tasks

            return {
                "success": True,
                "task_id": task_id,
                "description": description,
                "agent_type": agent_type,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class TaskUpdateTool(BaseTool):
    """Update an existing task status."""

    def __init__(self):
        metadata = ToolMetadata(
            name="task_update",
            description="Update an existing task status",
            permission_level=PermissionLevel.SAFE,
            read_only=False,
            local_only=False,
            categories=["task", "multi_agent"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Update task status.

        Args:
            args: Should contain 'task_id' and 'status'

        Returns:
            Dict with update status
        """
        try:
            task_id = args.get("task_id")
            status = args.get("status", "completed")

            if not task_id:
                return {"success": False, "error": "No task_id provided"}

            tasks = context.get("tasks", {})
            if task_id not in tasks:
                return {"success": False, "error": f"Task {task_id} not found"}

            tasks[task_id]["status"] = status
            tasks[task_id]["updated"] = datetime.now().isoformat()
            context["tasks"] = tasks

            return {"success": True, "task_id": task_id, "status": status}

        except Exception as e:
            return {"success": False, "error": str(e)}


class TaskStopTool(BaseTool):
    """Stop/cancel a running task."""

    def __init__(self):
        metadata = ToolMetadata(
            name="task_stop",
            description="Stop or cancel a running task",
            permission_level=PermissionLevel.WRITE,
            read_only=False,
            local_only=False,
            categories=["task", "multi_agent"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a task.

        Args:
            args: Should contain 'task_id'

        Returns:
            Dict with stop status
        """
        try:
            task_id = args.get("task_id")

            if not task_id:
                return {"success": False, "error": "No task_id provided"}

            tasks = context.get("tasks", {})
            if task_id not in tasks:
                return {"success": False, "error": f"Task {task_id} not found"}

            tasks[task_id]["status"] = "cancelled"
            tasks[task_id]["cancelled_at"] = datetime.now().isoformat()
            context["tasks"] = tasks

            return {"success": True, "task_id": task_id, "status": "cancelled"}

        except Exception as e:
            return {"success": False, "error": str(e)}


class TaskListTool(BaseTool):
    """List all tasks."""

    def __init__(self):
        metadata = ToolMetadata(
            name="task_list",
            description="List all tasks with optional status filter",
            permission_level=PermissionLevel.SAFE,
            read_only=True,
            local_only=False,
            categories=["task", "multi_agent"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """List tasks.

        Args:
            args: Optional 'status' filter

        Returns:
            Dict with tasks list
        """
        try:
            status_filter = args.get("status")
            tasks = context.get("tasks", {})

            result = []
            for task_id, task in tasks.items():
                if status_filter and task.get("status") != status_filter:
                    continue
                result.append({"task_id": task_id, **task})

            return {"success": True, "tasks": result, "count": len(result)}

        except Exception as e:
            return {"success": False, "error": str(e)}
