"""WebFetch tool - fetch web content."""

import asyncio
from typing import Any, Dict, Optional

import httpx

from maximus.tools.base import BaseTool
from maximus.models import PermissionLevel, ToolMetadata


class ToolResult:
    """Simple result wrapper."""
    def __init__(self, success: bool, data: Optional[Dict] = None, error: Optional[str] = None):
        self.success = success
        self.data = data or {}
        self.error = error


class WebFetchTool(BaseTool):
    """Fetch content from URLs.
    
    Supports:
    - HTML pages
    - JSON APIs
    - Plain text
    - GitHub raw files
    - Download limit: 1MB
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="web_fetch",
            description="Fetch content from a URL (HTML, JSON, text, GitHub raw)",
            permission_level=PermissionLevel.SAFE,
            read_only=True,
            local_only=False
        )
        super().__init__(metadata)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={
                "User-Agent": "Maximus/1.0 (AI Coding Assistant)"
            }
        )
        self.parameters = {
            "url": {"type": "string", "description": "URL to fetch"},
            "max_bytes": {"type": "integer", "description": "Max bytes (default 1MB)", "default": 1048576},
            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
        }
        self.required_params = ["url"]

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        url = args.get("url")
        max_bytes = args.get("max_bytes", 1048576)
        timeout = args.get("timeout", 30)

        if not url:
            return ToolResult(success=False, error="No URL provided")

        # Validate URL
        if not url.startswith(("http://", "https://")):
            return ToolResult(success=False, error="URL must start with http:// or https://")

        try:
            response = await asyncio.wait_for(
                self._client.get(url),
                timeout=timeout
            )
            response.raise_for_status()

            content = response.text
            
            # Limit content size
            if len(content) > max_bytes:
                content = content[:max_bytes] + f"\n... [truncated at {max_bytes} bytes]"

            # Detect content type
            content_type = response.headers.get("content-type", "").lower()
            
            if "json" in content_type:
                data_type = "json"
            elif "html" in content_type:
                data_type = "html"
            else:
                data_type = "text"

            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "data_type": data_type,
                    "content": content,
                    "size_bytes": len(content),
                    "headers": dict(response.headers)
                }
            )

        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Request timed out after {timeout}s")
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"HTTP {e.response.status_code}: {e.response.reason_phrase}")
        except Exception as e:
            return ToolResult(success=False, error=f"Fetch failed: {str(e)}")

    async def close(self):
        await self._client.aclose()