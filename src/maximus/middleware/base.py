"""Base middleware class for Maximus.ai."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass


@dataclass
class MiddlewareContext:
    """Context passed through middleware chain."""
    tool_name: str
    args: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Middleware(ABC):
    """Abstract base class for middleware."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process the context through this middleware."""
        pass
    
    def wrap(self, next_func: Callable) -> Callable:
        """Wrap the next function in this middleware."""
        async def wrapped(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            context = MiddlewareContext(tool_name=tool_name, args=args)
            
            try:
                # Process through this middleware
                context = await self.process(context)
                
                # If no error and no result yet, call next
                if context.error is None and context.result is None:
                    context.result = await next_func(tool_name, args)
                    
            except Exception as e:
                context.error = e
                
            # If there's an error, return error dict
            if context.error:
                return {
                    "success": False,
                    "error": str(context.error),
                    "error_type": context.error.__class__.__name__,
                    "tool": tool_name,
                }
                
            return context.result or {"success": False, "error": "No result"}
            
        return wrapped
