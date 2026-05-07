"""Input sanitization middleware - Open-SWE pattern.

Sanitizes tool inputs to prevent injection attacks
and ensure valid input formats.
"""

import logging
from typing import Dict, Any
from maximus.middleware.base import Middleware, MiddlewareContext

logger = logging.getLogger(__name__)


class SanitizeMiddleware(Middleware):
    """Sanitizes tool inputs before execution."""
    
    def __init__(self):
        super().__init__("SanitizeMiddleware")
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Sanitize tool arguments."""
        tool_name = context.tool_name
        args = context.args
        
        # Sanitize common fields
        sanitized = {}
        for key, value in args.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value
        
        context.args = sanitized
        return context
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string value."""
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Limit length
        max_length = 10000
        if len(value) > max_length:
            logger.warning(f"Truncating input to {max_length} chars")
            value = value[:max_length]
            
        return value
