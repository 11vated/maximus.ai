"""Hooks system for Maximus.ai - Event-driven extensibility.

Implements Claude Code pattern:
- 60+ event hooks for lifecycle events
- Pre/post handlers for runs, tools, messages
- Custom hooks via ~/.maximus/hooks/
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HookEvent(str, Enum):
    """Available hook events - Claude Code style."""
    # Run lifecycle
    PRE_RUN = "pre_run"
    POST_RUN = "post_run"
    ON_RUN_ERROR = "on_run_error"
    
    # Tool lifecycle
    PRE_TOOL = "pre_tool"
    POST_TOOL = "post_tool"
    ON_TOOL_ERROR = "on_tool_error"
    ON_TOOL_START = "on_tool_start"
    ON_TOOL_END = "on_tool_end"
    
    # Message lifecycle
    PRE_MESSAGE = "pre_message"
    POST_MESSAGE = "post_message"
    
    # LLM lifecycle
    PRE_LLM = "pre_llm"
    POST_LLM = "post_llm"
    ON_LLM_ERROR = "on_llm_error"
    
    # Agent state
    ON_STATE_CHANGE = "on_state_change"
    ON_PLAN_CREATED = "on_plan_created"
    ON_REFLECTION = "on_reflection"
    
    # Completion
    ON_COMPLETION = "on_completion"
    ON_ABORT = "on_abort"
    
    # User interaction
    ON_PERMISSION_REQUEST = "on_permission_request"
    ON_USER_FEEDBACK = "on_user_feedback"
    
    # Session
    ON_SESSION_START = "on_session_start"
    ON_SESSION_END = "on_session_end"


@dataclass
class HookContext:
    """Context passed to hook handlers."""
    event: HookEvent
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    run_id: Optional[str] = None


@dataclass
class HookResult:
    """Result from hook handler."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    # Whether to continue (for pre-hooks)
    continue_execution: bool = True


class HookHandler(ABC):
    """Base class for hook handlers."""
    
    @abstractmethod
    async def handle(self, context: HookContext) -> HookResult:
        """Handle the hook event."""
        pass


class FunctionHook(HookHandler):
    """Hook that wraps a function."""
    
    def __init__(self, func: Callable):
        self.func = func
    
    async def handle(self, context: HookContext) -> HookResult:
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(context)
            else:
                result = self.func(context)
            
            if result is None:
                return HookResult(success=True, continue_execution=True)
            
            if isinstance(result, bool):
                return HookResult(success=result, continue_execution=result)
            
            if isinstance(result, dict):
                return HookResult(
                    success=result.get("success", True),
                    data=result.get("data"),
                    continue_execution=result.get("continue_execution", True)
                )
            
            return HookResult(success=True)
            
        except Exception as e:
            logger.error(f"Hook handler failed: {e}")
            return HookResult(success=False, error=str(e), continue_execution=True)


class HookManager:
    """Manages all hooks - register, execute, lifecycle."""
    
    def __init__(self):
        self._hooks: Dict[HookEvent, List[HookHandler]] = {e: [] for e in HookEvent}
        self._global_hooks_path = Path.home() / ".maximus" / "hooks"
    
    def register(self, event: HookEvent, handler: HookHandler) -> None:
        """Register a handler for an event."""
        self._hooks[event].append(handler)
    
    def register_function(self, event: HookEvent, func: Callable) -> None:
        """Register a function as a handler."""
        self.register(event, FunctionHook(func))
    
    def unregister(self, event: HookEvent, handler: HookHandler) -> None:
        """Unregister a handler."""
        if handler in self._hooks[event]:
            self._hooks[event].remove(handler)
    
    async def trigger(self, event: HookEvent, context: HookContext) -> HookResult:
        """Trigger all handlers for an event."""
        results = []
        
        for handler in self._hooks[event]:
            try:
                result = await handler.handle(context)
                results.append(result)
                
                # Stop if handler says to stop
                if not result.continue_execution:
                    logger.warning(f"Hook {event.value} requested stop")
                    break
                    
            except Exception as e:
                logger.error(f"Hook {event.value} handler error: {e}")
                results.append(HookResult(success=False, error=str(e)))
        
        # Return first failure or success
        for r in results:
            if not r.success:
                return r
        
        return HookResult(success=True) if results else HookResult(success=True)
    
    async def trigger_pre(self, event: HookEvent, **data) -> bool:
        """Trigger pre-event, return whether to continue."""
        context = HookContext(event=event, data=data)
        result = await self.trigger(event, context)
        return result.continue_execution
    
    async def trigger_post(self, event: HookEvent, **data) -> None:
        """Trigger post-event, ignore result."""
        context = HookContext(event=event, data=data)
        await self.trigger(event, context)
    
    def load_global_hooks(self) -> None:
        """Load hooks from ~/.maximus/hooks/"""
        if not self._global_hooks_path.exists():
            return
        
        for hook_file in self._global_hooks_path.glob("*.py"):
            try:
                # Import hook module
                import importlib.util
                spec = importlib.util.spec_from_file_location(hook_file.stem, hook_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for hook registrations
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr):
                        # Auto-register decorated functions
                        if hasattr(attr, '_hook_event'):
                            self.register_function(attr._hook_event, attr)
                            
            except Exception as e:
                logger.warning(f"Failed to load hook {hook_file}: {e}")
    
    def list_hooks(self) -> Dict[str, int]:
        """List all registered hooks."""
        return {e.value: len(self._hooks[e]) for e in HookEvent}


# Decorator for hooks
def hook(event: HookEvent):
    """Decorator to mark a function as a hook handler."""
    def decorator(func: Callable) -> Callable:
        func._hook_event = event
        return func
    return decorator


# Global hook manager
_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """Get global hook manager."""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager


# Convenience function decorators
def pre_run(func: Callable) -> Callable:
    """Decorator for pre-run hook."""
    return hook(HookEvent.PRE_RUN)(func)

def post_run(func: Callable) -> Callable:
    """Decorator for post-run hook."""
    return hook(HookEvent.POST_RUN)(func)

def pre_tool(func: Callable) -> Callable:
    """Decorator for pre-tool hook."""
    return hook(HookEvent.PRE_TOOL)(func)

def post_tool(func: Callable) -> Callable:
    """Decorator for post-tool hook."""
    return hook(HookEvent.POST_TOOL)(func)

def on_tool_error(func: Callable) -> Callable:
    """Decorator for tool error hook."""
    return hook(HookEvent.ON_TOOL_ERROR)(func)


# Example global hooks that can be loaded
"""
# Example: ~/.maximus/hooks/analytics.py

from maximus.hooks import hook, HookEvent, HookContext, HookResult

@hook(HookEvent.POST_TOOL)
async def log_tool_usage(context: HookContext) -> HookResult:
    tool_name = context.data.get("tool", "unknown")
    print(f"Tool used: {tool_name}")
    return HookResult(success=True)

@hook(HookEvent.ON_COMPLETION)
async def log_completion(context: HookContext) -> HookResult:
    print(f"Run completed: {context.data}")
    return HookResult(success=True)
"""