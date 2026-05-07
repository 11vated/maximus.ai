"""Web search tool using DuckDuckGo (free, no API key)."""

import logging
from typing import Any, Dict, List

from maximus.models import ToolMetadata
from maximus.tools.base import BaseTool

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo (free, no API key)."""

    def __init__(self):
        metadata = ToolMetadata(
            name="web_search",
            description="Search the web using DuckDuckGo. Free, no API key needed.",
            read_only=True,
            concurrent_safe=True,
            permission_level="safe",
            local_only=False,  # Uses external API
            categories=["web", "search"],
        )
        super().__init__(metadata)

    async def execute(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query")
        max_results = args.get("max_results", 10)

        if not query:
            return {"success": False, "error": "Missing 'query' argument"}

        try:
            from duckduckgo_search import DDGS

            results: List[Dict] = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })

            return {"success": True, "results": results, "count": len(results)}
        except ImportError:
            return {"success": False, "error": "duckduckgo-search not installed. Run: pip install duckduckgo-search"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default: 10)"},
            },
            "required": ["query"],
        }
