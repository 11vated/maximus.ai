"""Middleware system for Maximus.ai - Open-SWE style.

Middleware wraps tool execution and model calls to provide:
- Error handling
- Message queue injection
- Input sanitization
- Step limit notifications
"""

from maximus.middleware.base import Middleware, MiddlewareContext
from maximus.middleware.error_handler import ToolErrorMiddleware
from maximus.middleware.message_queue import MessageQueueMiddleware
from maximus.middleware.sanitize import SanitizeMiddleware
from maximus.middleware.step_limit import StepLimitMiddleware

__all__ = [
    "Middleware",
    "MiddlewareContext",
    "ToolErrorMiddleware",
    "MessageQueueMiddleware",
    "SanitizeMiddleware",
    "StepLimitMiddleware",
    "apply_middleware",
]

def apply_middleware(tool_func, middlewares):
    """Apply a stack of middlewares to a tool function."""
    result = tool_func
    for mw in reversed(middlewares):
        result = mw.wrap(result)
    return result
