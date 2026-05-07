"""Agent loop - Tool-calling LLM loop with streaming and error recovery.

This implements Claude Code's approach:
- LLM decides when to call tools in a loop
- Results fed back to LLM until completion
- Retry logic, fallbacks, correction cycles
- Streaming tool execution interleaved with text
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from maximus.models import (
    AgentConfig, CognitiveState, Event, EventType, Output, Step, Plan
)
from maximus.tools.registry import get_registry
from maximus.utils.llm import LLMClient

logger = logging.getLogger(__name__)


class LoopDecision(str, Enum):
    """What the LLM decided in this turn."""
    TOOL_CALL = "tool_call"
    RESPOND = "respond"
    ERROR = "error"


@dataclass
class ToolCall:
    """Represents a single tool call from the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class TurnResult:
    """Result of a single LLM turn."""
    decision: LoopDecision
    tool_calls: List[ToolCall] = field(default_factory=list)
    content: str = ""
    error: Optional[str] = None
    stop_reason: Optional[str] = None


@dataclass 
class LoopMetrics:
    """Metrics for the agent loop."""
    total_turns: int = 0
    total_tool_calls: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    total_tokens: int = 0
    total_retry_attempts: int = 0


class AgentLoop:
    """Tool-calling LLM agent loop - Claude Code style.
    
    Key differences from pre-planned execution:
    1. LLM decides when to call tools (not pre-planned)
    2. Loop continues until LLM responds without tools
    3. Error recovery with retry logic
    4. Streaming tool results
    """

    SYSTEM_PROMPT = """You are Maximus, an AI coding assistant. You have access to tools to help you complete tasks.

AVAILABLE TOOLS:
- read_file: Read file contents (path: string, offset?: number, limit?: number)
- write_file: Write content to file (path: string, content: string)
- edit_file: Edit file with replacement (path: string, old: string, new: string)
- ls: List directory (path: string)
- glob: Find files by pattern (pattern: string, path?: string)
- grep: Search files (pattern: string, path?: string, context?: number)
- execute_shell: Run shell command (command: string, timeout?: number)
- git_status: Check git status
- git_diff: Show git diff (file?: string)
- git_log: Show commit history (count?: number)

GUIDELINES:
1. Use tools to inspect code before editing
2. Execute shell commands to run code, tests, linters
3. Think step-by-step: understand, implement, verify
4. If something fails, analyze the error and try a different approach
5. When you have the answer, provide a clear summary

The user wants you to accomplish: {goal}

Remember: Think carefully, use tools strategically, and verify your work."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.state = CognitiveState.INIT
        from maximus.tools.builtin import register_builtin_tools
        register_builtin_tools()
        self.registry = get_registry()
        self.llm = LLMClient(config)
        self.messages: List[Dict[str, Any]] = []
        self.model_calls = 0
        self.metrics = LoopMetrics()
        self._max_turns = config.max_model_calls if config and hasattr(config, 'max_model_calls') else 20
        self._current_turn = 0

    def _build_system_prompt(self, goal: str) -> str:
        """Build the system prompt with current goal."""
        return self.SYSTEM_PROMPT.format(goal=goal)

    def _get_tool_schemas(self) -> List[Dict]:
        """Get tool definitions in Ollama format."""
        tool_names = self.registry.list_tools()
        schemas = []
        for tool_name in tool_names:
            tool = self.registry.get(tool_name)
            if not tool:
                continue
            schema = {
                "type": "function",
                "function": {
                    "name": tool.metadata.name,
                    "description": tool.metadata.description or f"Execute {tool_name}",
                    "parameters": {
                        "type": "object",
                        "properties": getattr(tool, 'parameters', {}),
                        "required": getattr(tool, 'required_params', [])
                    }
                }
            }
            schemas.append(schema)
        return schemas

    async def _stream_text_response(self) -> AsyncGenerator[str, None]:
        """Stream text response from LLM (no tools)."""
        tool_schemas = self._get_tool_schemas()
        
        try:
            async for chunk in self.llm.chat(
                messages=self.messages,
                tools=None,  # No tools for text-only response
                temperature=self.config.temperature
            ):
                if "message" in chunk:
                    msg = chunk["message"]
                    if "content" in msg and msg["content"]:
                        yield msg["content"]
                
                if chunk.get("done", False):
                    break
        except Exception as e:
            logger.error(f"LLM stream failed: {e}")
            yield f"[Error: {e}]"

    def run(self, goal: str) -> "AgentLoopGenerator":
        """Main entry point for sync execution."""
        return AgentLoopGenerator(self, goal)

    async def run_async(self, goal: str) -> AsyncGenerator[Event, None]:
        """Tool-calling LLM loop - the core execution engine."""
        self.state = CognitiveState.INIT
        self._current_turn = 0
        self.messages = []
        self.metrics = LoopMetrics()
        
        yield Event(type=EventType.STATE_CHANGE, data={"state": "init", "goal": goal})

        # Initialize with system prompt and user goal
        system_prompt = self._build_system_prompt(goal)
        self.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": goal}
        ]

        # Main tool-calling loop
        while self._current_turn < self._max_turns:
            self._current_turn += 1
            self.state = CognitiveState.PLAN
            yield Event(
                type=EventType.STATE_CHANGE, 
                data={"state": "thinking", "turn": self._current_turn}
            )

            # Get LLM response with tools
            turn_result = await self._get_llm_response()

            if turn_result.error:
                yield Event(
                    type=EventType.ERROR,
                    data={"error": turn_result.error, "turn": self._current_turn}
                )
                # Retry logic - try again
                if self.metrics.total_retry_attempts < 3:
                    self.metrics.total_retry_attempts += 1
                    continue
                break

            self.metrics.total_turns += 1

            # Handle tool calls
            if turn_result.decision == LoopDecision.TOOL_CALL:
                for tool_call in turn_result.tool_calls:
                    self.metrics.total_tool_calls += 1
                    yield Event(
                        type=EventType.TOOL_START,
                        data={
                            "tool": tool_call.name,
                            "args": tool_call.arguments,
                            "call_id": tool_call.id,
                            "turn": self._current_turn
                        }
                    )

                    # Execute tool with retry
                    result = await self._execute_tool_with_retry(
                        tool_call.name, 
                        tool_call.arguments
                    )

                    if result.get("success"):
                        self.metrics.successful_tool_calls += 1
                    else:
                        self.metrics.failed_tool_calls += 1

                    # Add tool result to messages
                    tool_result_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    }
                    self.messages.append(tool_result_message)

                    yield Event(
                        type=EventType.TOOL_END,
                        data={
                            "tool": tool_call.name,
                            "result": result,
                            "success": result.get("success", False)
                        }
                    )

            # Handle LLM response without tool calls (completion)
            elif turn_result.decision == LoopDecision.RESPOND:
                # Stream text in real-time
                async for text_chunk in self._stream_text_response():
                    if text_chunk:
                        yield Event(
                            type=EventType.TEXT_CHUNK,
                            data={"text": text_chunk}
                        )
                
                # Check stop reason
                if turn_result.stop_reason in ("eos", "stop", "length"):
                    self.state = CognitiveState.COMMIT
                    break

            # Check for error decision
            elif turn_result.decision == LoopDecision.ERROR:
                if turn_result.error:
                    yield Event(
                        type=EventType.ERROR,
                        data={"error": turn_result.error}
                    )

        # Finalize
        self.state = CognitiveState.PAUSE
        
        output = Output(
            id=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type="report",
            content=f"Completed in {self._current_turn} turns. "
                   f"Tools: {self.metrics.successful_tool_calls} success, "
                   f"{self.metrics.failed_tool_calls} failed."
        )
        
        yield Event(type=EventType.TURN_DONE, data={
            "output": output.dict(),
            "metrics": {
                "turns": self.metrics.total_turns,
                "tool_calls": self.metrics.total_tool_calls,
                "successful": self.metrics.successful_tool_calls,
                "failed": self.metrics.failed_tool_calls,
                "retries": self.metrics.total_retry_attempts
            }
        })

    async def _get_llm_response(self) -> TurnResult:
        """Get LLM response with tool calling (non-generator)."""
        self.model_calls += 1
        tool_schemas = self._get_tool_schemas()

        try:
            full_response = ""
            tool_calls: List[ToolCall] = []
            stop_reason = None
            
            async for chunk in self.llm.chat(
                messages=self.messages,
                tools=tool_schemas if tool_schemas else None,
                temperature=self.config.temperature
            ):
                # Handle Ollama streaming format
                if "message" in chunk:
                    msg = chunk["message"]
                    
                    if "content" in msg and msg["content"]:
                        content = msg["content"]
                        full_response += content
                    
                    # Check for tool calls in response
                    if "tool_calls" in msg:
                        for tc in msg["tool_calls"]:
                            tool_call = ToolCall(
                                id=tc.get("id", f"call_{len(tool_calls)}"),
                                name=tc.get("function", {}).get("name", ""),
                                arguments=tc.get("function", {}).get("arguments", {})
                            )
                            tool_calls.append(tool_call)

                # Handle done signal
                if chunk.get("done", False):
                    stop_reason = chunk.get("done_reason", "")
                    break

            # Determine decision
            if tool_calls:
                return TurnResult(
                    decision=LoopDecision.TOOL_CALL,
                    tool_calls=tool_calls,
                    stop_reason=stop_reason
                )
            elif full_response.strip():
                return TurnResult(
                    decision=LoopDecision.RESPOND,
                    content=full_response.strip(),
                    stop_reason=stop_reason
                )
            else:
                return TurnResult(
                    decision=LoopDecision.RESPOND,
                    content="(No response)",
                    stop_reason=stop_reason
                )

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return TurnResult(
                decision=LoopDecision.ERROR,
                error=str(e)
            )

    async def _execute_tool_with_retry(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """Execute a tool with retry logic."""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await self._execute_tool(tool_name, arguments)
                
                # Check if result indicates an error that warrants retry
                if isinstance(result, dict) and not result.get("success", True):
                    error_msg = result.get("error", "")
                    # Retry on transient errors
                    if any(err in error_msg.lower() for err in ["timeout", "connection", "temporary"]):
                        last_error = result
                        await asyncio.sleep(1 * (attempt + 1))  # Backoff
                        continue
                
                return result
                
            except Exception as e:
                last_error = {"success": False, "error": str(e)}
                if attempt < max_retries:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
        
        return last_error or {"success": False, "error": "Max retries exceeded"}

    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool."""
        tool = self.registry.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}

        try:
            result = await tool.execute(args, {"workdir": self.config.workdir})
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"success": False, "error": str(e)}


class AgentLoopGenerator:
    """Synchronous wrapper for AgentLoop."""

    def __init__(self, loop: AgentLoop, goal: str):
        self._loop = loop
        self._goal = goal
        self._async_gen = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._async_gen is None:
            import asyncio
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())
            self._async_gen = self._loop.run_async(self._goal)

        import asyncio
        try:
            return asyncio.get_event_loop().run_until_complete(
                self._async_gen.__anext__()
            )
        except StopAsyncIteration:
            raise StopIteration