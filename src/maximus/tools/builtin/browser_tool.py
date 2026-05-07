"""Browser automation tool - interact with web pages."""

import logging
from typing import Any, Dict

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class BrowserTool(BaseTool):
    """Open and read content from URLs."""

    def __init__(self):
        metadata = ToolMetadata(
            name="browse_url",
            description="Fetch content from a URL (read-only web access).",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=False,  # Uses external web
            categories=["web", "read", "browser"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        url = args.get("url")
        if not url:
            return {"success": False, "error": "Missing 'url' argument"}

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "content": response.text[:10000],  # Limit size
                    "headers": dict(response.headers),
                }
        except ImportError:
            return {"success": False, "error": "httpx not installed. Run: pip install httpx"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"}
            },
            "required": ["url"],
        }
