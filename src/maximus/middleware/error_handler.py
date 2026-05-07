"""Tool error handling middleware - Open-SWE pattern.

Wraps all tool calls in try/except so unhandled exceptions
are returned as error payloads instead of crashing the agent.
"""

import logging
from typing import Dict, Any
from maximus.middleware.base import Middleware, MiddlewareContext

logger = logging.getLogger(__name__)


class ToolErrorMiddleware(Middleware):
    """Normalize tool execution errors into predictable payloads."""
    
    def __init__(self):
        super().__init__("ToolErrorMiddleware")
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Log errors but let the wrapper handle exceptions."""
        # The actual error handling is done in the wrap method
        # This just adds logging
        if context.error:
            logger.error(
                f"Tool {context.tool_name} failed: {context.error}",
                extra={"tool": context.tool_name, "args": context.args}
            )
        return context
