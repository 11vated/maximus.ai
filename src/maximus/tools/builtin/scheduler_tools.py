"""Job/task scheduler tool."""

import asyncio
import logging
from typing import Any, Dict
from datetime import datetime

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class SleepTool(BaseTool):
    """Pause execution for specified duration."""

    def __init__(self):
        metadata = ToolMetadata(
            name="sleep",
            description="Pause execution for specified seconds.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["system", "timing"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        seconds = args.get("seconds", 1)
        try:
            seconds = float(seconds)
            await asyncio.sleep(seconds)
            return {"success": True, "slept": seconds}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "description": "Seconds to sleep (default: 1)"}
            },
            "required": [],
        }


class DateTimeTool(BaseTool):
    """Get current date and time."""

    def __init__(self):
        metadata = ToolMetadata(
            name="datetime",
            description="Get current date and time.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=True,
            categories=["system", "info"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            now = datetime.utcnow()
            return {
                "success": True,
                "iso": now.isoformat(),
                "timestamp": now.timestamp(),
                "str": str(now),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}
