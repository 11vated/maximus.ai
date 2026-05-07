"""Message queue middleware - Open-SWE pattern.

Checks for queued messages (e.g. follow-up comments)
and injects them before the next model call.
"""

import logging
from typing import Dict, Any, List
from maximus.middleware.base import Middleware, MiddlewareContext

logger = logging.getLogger(__name__)


class MessageQueueMiddleware(Middleware):
    """Injects queued messages into conversation before model calls."""
    
    def __init__(self, queue_store: Dict[str, List[Dict]] = None):
        super().__init__("MessageQueueMiddleware")
        self.queue_store = queue_store or {}
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Check for queued messages for this tool/context."""
        # For now, just pass through
        # In full implementation, this would check for messages
        # queued for the current thread/session
        return context
    
    def enqueue_message(self, session_id: str, message: Dict[str, Any]):
        """Add a message to the queue for a session."""
        if session_id not in self.queue_store:
            self.queue_store[session_id] = []
        self.queue_store[session_id].append(message)
        logger.info(f"Queued message for session {session_id}")
    
    def get_queued_messages(self, session_id: str) -> List[Dict]:
        """Get and clear queued messages for a session."""
        messages = self.queue_store.pop(session_id, [])
        logger.info(f"Retrieved {len(messages)} queued messages for {session_id}")
        return messages
