"""Step limit notification middleware - Open-SWE pattern.

Notifies when agent approaches or reaches step limits.
"""

import logging
from typing import Dict, Any
from maximus.middleware.base import Middleware, MiddlewareContext

logger = logging.getLogger(__name__)


class StepLimitMiddleware(Middleware):
    """Notifies when step limit is reached."""
    
    def __init__(self, max_steps: int = 50, warning_threshold: float = 0.8):
        super().__init__("StepLimitMiddleware")
        self.max_steps = max_steps
        self.warning_threshold = warning_threshold
        self.current_step = 0
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Check step limits."""
        self.current_step += 1
        
        # Warning at threshold
        if self.current_step > self.max_steps * self.warning_threshold:
            logger.warning(
                f"Approaching step limit: {self.current_step}/{self.max_steps}"
            )
        
        # Hard limit
        if self.current_step > self.max_steps:
            logger.error(f"Step limit reached: {self.max_steps}")
            context.error = RuntimeError(
                f"Step limit reached ({self.max_steps}). Stopping execution."
            )
            return context
        
        return context
    
    def reset(self):
        """Reset step counter."""
        self.current_step = 0
