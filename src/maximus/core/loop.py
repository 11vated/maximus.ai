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
from maximus.memory.memory_mesh import (
    MemoryMesh, MemoryBank, MemoryScope, 
    KnowledgeLayer, EpisodicMemory, SemanticMemory
)
from maximus.intelligence.model_router import (
    ModelRouter, get_model_router, TaskIntent, ComplexityLevel
)
from maximus.intelligence.stance import StanceManager, StanceType
from maximus.hooks import (
    HookManager, get_hook_manager, HookEvent, HookContext
)
from maximus.security import (
    get_permission_classifier, CommandCategory
)
from maximus.core.bi_operation import (
    BiOperationInterface, BiOpConfig
)
from maximus.core.evolution import LearningSystem

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

    SYSTEM_PROMPT = """You are Maximus, a coding assistant. Your ONLY job is to call tools to help the user.

RULES:
1. When you need a tool, output EXACTLY: TOOL_START{{"name": "NAME", "arguments": {{"KEY": "VAL"}}}}TOOL_END
2. No other text when calling tools
3. Use lowercase with underscores

EXAMPLES:
"list files" → TOOL_START{{"name": "ls", "arguments": {{"path": "."}}}}TOOL_END
"read file" → TOOL_START{{"name": "read_file", "arguments": {{"path": "file.py"}}}}TOOL_END

Tools: ls, read_file, write_file, edit_file, execute_shell, grep, glob

Task: {goal}

Output:"""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.state = CognitiveState.INIT
        from maximus.tools.builtin import register_builtin_tools
        register_builtin_tools()
        self.registry = get_registry()
        self.llm = LLMClient(config)
        
        # Initialize MemoryMesh - the brain's memory system
        self.memory = MemoryMesh(
            project_path=self.config.workdir if self.config else None
        )
        
        self.messages: List[Dict[str, Any]] = []
        self.model_calls = 0
        self.metrics = LoopMetrics()
        self._max_turns = config.max_model_calls if config and hasattr(config, 'max_model_calls') else 20
        self._current_turn = 0
        self._session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize ModelRouter for intelligent model selection
        self.router = get_model_router()
        self._current_routing = None  # Store routing decision
        
        # Initialize Hooks system for event-driven extensibility
        self.hooks = get_hook_manager()
        self.hooks.load_global_hooks()  # Load custom hooks from ~/.maximus/hooks/
        
        # Initialize Security Classifier for command safety
        self.security = get_permission_classifier()
        
        # Initialize Bi-Operation Interface (OS + Agent partnership)
        self.bi_op = BiOperationInterface(BiOpConfig(
            enable_loop_detection=True,
            enable_proactive_injection=True,
            enable_parallel_verification=True,
            enable_memory_injection=True
        ))
        
        # Initialize Self-Evolution Learning System
        self.learning = LearningSystem()
        
        # Initialize Stance Manager for behavior adaptation
        self.stance_manager = StanceManager()
        
        # Initialize MCP Manager for dynamic tool discovery
        self._mcp_manager = None
        self._mcp_initialized = False
    
    async def _init_mcp_tools(self):
        """Initialize MCP tools and add to registry."""
        if self._mcp_initialized:
            return
            
        try:
            from maximus.mcp.mcp_manager import get_mcp_manager
            mcp_manager = get_mcp_manager()
            await mcp_manager.initialize()
            
            # Get all MCP tools and add them to the tool schema list
            for server_name, server in mcp_manager.servers.items():
                if server.is_running:
                    logger.info(f"MCP server '{server_name}' has {len(server.tools)} tools")
            
            self._mcp_manager = mcp_manager
            self._mcp_initialized = True
            logger.info("MCP tools initialized")
        except Exception as e:
            logger.debug(f"MCP initialization not available: {e}")

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

    def _get_memory_context(self, query: str = "") -> str:
        """Get context from memory banks for LLM.
        
        Includes both standard memory context and vector-based semantic search.
        """
        # Get standard memory context
        standard_ctx = self.memory.to_context()
        
        # Try to add vector memory search for relevant context
        try:
            from maximus.memory.vector_memory import get_vector_memory
            vector_mem = get_vector_memory()
            if vector_mem and query:
                # Search for relevant memories
                results = vector_mem.retrieve(query, top_k=3)
                if results:
                    vector_ctx = "\n## Relevant Past Context\n"
                    for chunk in results:
                        vector_ctx += f"- {chunk.content[:200]}\n"
                    return standard_ctx + vector_ctx if standard_ctx else vector_ctx
        except Exception as e:
            logger.debug(f"Vector memory not available: {e}")
        
        return standard_ctx

    def _build_contextual_prompt(self, goal: str) -> str:
        """Build system prompt with memory context."""
        memory_context = self._get_memory_context(goal)
        
        base_prompt = self.SYSTEM_PROMPT.format(goal=goal)
        
        if memory_context:
            return f"{base_prompt}\n\n## MEMORY CONTEXT\n{memory_context}"
        return base_prompt
    
    def _get_effective_temperature(self) -> float:
        """Get temperature from routing decision, stance, or fall back to config."""
        # Start with routing or config temperature
        base_temp = 0.3  # Default for code tasks
        if self._current_routing:
            base_temp = self._current_routing.temperature
        elif self.config:
            base_temp = 0.3  # Use conservative default
            
        # Apply stance temperature modifier
        try:
            stance_context = self.stance_manager.get_planning_context()
            temp_mod = stance_context.get("temperature_modifier", 0)
            final_temp = base_temp + temp_mod
            # Clamp to valid range
            return max(0.0, min(1.0, final_temp))
        except Exception:
            return base_temp
    
    def _get_effective_model(self) -> Optional[str]:
        """Get model from routing decision or config."""
        if self._current_routing:
            return self._current_routing.model
        # Fall back to config model
        return self.config.model if self.config else None

    async def _stream_text_response(self) -> AsyncGenerator[str, None]:
        """Stream text response from LLM (no tools)."""
        tool_schemas = self._get_tool_schemas()
        
        try:
            async for chunk in self.llm.chat(
                messages=self.messages,
                tools=None,  # No tools for text-only response
                temperature=self._get_effective_temperature(),
                model=self._get_effective_model()
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
        
        # Auto-select stance based on goal
        suggested_stance = self.stance_manager.suggest_stance(goal)
        if suggested_stance != self.stance_manager.current_stance:
            self.stance_manager.switch(suggested_stance, reason=f"Auto-selected for: {goal[:50]}")
            logger.info(f"Stance switched to {suggested_stance.value} for goal: {goal[:50]}")

        # Trigger PRE_RUN hook
        await self.hooks.trigger_pre(
            HookEvent.PRE_RUN,
            goal=goal,
            session_id=self._session_id
        )

        # Store goal in Working Memory
        self.memory.working.set_goal(goal)
        
        # Record session start in Episodic Memory
        self.memory.episodic.add_event(
            "session_start",
            f"Started task: {goal[:100]}",
            {"session_id": self._session_id, "goal": goal}
        )
        
        # Route the task to optimal model based on intent and complexity
        self._current_routing = self.router.route(goal)
        logger.info(f"Routed to model: {self._current_routing.model} "
                   f"(intent: {self._current_routing.intent.value}, "
                   f"complexity: {self._current_routing.complexity.value})")
        
        # Record routing decision in semantic memory
        self.memory.semantic.add_fact(
            key=f"routing_{self._session_id}",
            value=f"Model: {self._current_routing.model}, "
                  f"Intent: {self._current_routing.intent.value}, "
                  f"Complexity: {self._current_routing.complexity.value}",
            layer=KnowledgeLayer.DOMAIN,
            tags=["routing", self._session_id]
        )
        
        # Build contextual prompt with memory
        system_prompt = self._build_contextual_prompt(goal)
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
            
            # Trigger ON_STATE_CHANGE hook
            await self.hooks.trigger_post(
                HookEvent.ON_STATE_CHANGE,
                state=self.state.value,
                turn=self._current_turn,
                session_id=self._session_id
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

                    # Trigger PRE_TOOL hook - can veto execution
                    if not await self.hooks.trigger_pre(
                        HookEvent.PRE_TOOL,
                        tool=tool_call.name,
                        args=tool_call.arguments,
                        session_id=self._session_id,
                        turn=self._current_turn
                    ):
                        result = {"success": False, "error": "Blocked by PRE_TOOL hook"}
                    else:
                        # Execute tool with retry
                        result = await self._execute_tool_with_retry(
                            tool_call.name, 
                            tool_call.arguments
                        )
                    
                    # Bi-Operation: Process action for loop detection and interventions
                    try:
                        interventions = await self.bi_op.process_action(
                            action_type=tool_call.name,
                            action_args=tool_call.arguments,
                            context=str(result)[:500],
                            current_step=self._current_turn
                        )
                        if interventions:
                            # Log interventions
                            for intervention in interventions:
                                logger.info(f"Bi-Operation intervention: {intervention.type} - {intervention.content}")
                    except Exception as e:
                        logger.debug(f"Bi-Operation processing error: {e}")

                    if result.get("success"):
                        self.metrics.successful_tool_calls += 1
                        
                        # Trigger POST_TOOL hook on success
                        await self.hooks.trigger_post(
                            HookEvent.POST_TOOL,
                            tool=tool_call.name,
                            args=tool_call.arguments,
                            result=result,
                            success=True,
                            session_id=self._session_id
                        )
                    else:
                        self.metrics.failed_tool_calls += 1
                        
                        # Trigger ON_TOOL_ERROR hook on failure
                        await self.hooks.trigger_post(
                            HookEvent.ON_TOOL_ERROR,
                            tool=tool_call.name,
                            args=tool_call.arguments,
                            error=result.get("error", "Unknown error"),
                            session_id=self._session_id
                        )

                    # Record to Procedural Memory (learn from tool usage)
                    self.memory.procedural.record_action(
                        action=tool_call.name,
                        context=str(tool_call.arguments)[:200],
                        success=result.get("success", False),
                        result=str(result)[:200] if result else None
                    )
                    
                    # Record significant events to Episodic Memory
                    if not result.get("success", True):
                        self.memory.episodic.add_event(
                            "tool_error",
                            f"Tool {tool_call.name} failed: {result.get('error', 'unknown')}",
                            {"tool": tool_call.name, "args": tool_call.arguments}
                        )

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
                    
                    # Store successful completion in semantic memory
                    self.memory.semantic.add_fact(
                        key=f"task_completed_{self._session_id}",
                        value=f"Completed: {goal[:80]}",
                        layer=KnowledgeLayer.INTENT,
                        tags=["completed", self._session_id]
                    )
                    
                    # Record completion in episodic
                    self.memory.episodic.add_event(
                        "task_completed",
                        f"Task completed successfully: {goal[:80]}",
                        {"session_id": self._session_id}
                    )
                    
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
        
        # Trigger POST_RUN hook
        await self.hooks.trigger_post(
            HookEvent.POST_RUN,
            goal=goal,
            session_id=self._session_id,
            turns=self._current_turn,
            metrics=self.metrics.__dict__,
            success=True
        )
        
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
        
        # Record learning from this task
        try:
            if self.metrics.successful_tool_calls > 0:
                # Collect the steps from this run
                steps = []
                for msg in self.messages:
                    if msg.get("role") == "assistant":
                        # Could extract tool calls from messages
                        pass
                
                self.learning.record_success(
                    goal=self.messages[1].get("content", "") if len(self.messages) > 1 else "",
                    steps=steps,
                    insight=f"Completed in {self._current_turn} turns with {self.metrics.successful_tool_calls} successful tool calls"
                )
        except Exception as e:
            logger.debug(f"Learning recording error: {e}")

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
                temperature=self._get_effective_temperature(),
                model=self._get_effective_model()
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
            
            # Try to extract tool calls from text response
            extracted_calls = self._extract_tool_calls_from_text(full_response)
            if extracted_calls:
                return TurnResult(
                    decision=LoopDecision.TOOL_CALL,
                    tool_calls=extracted_calls,
                    stop_reason=stop_reason
                )
            
            if full_response.strip():
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

    def _extract_tool_calls_from_text(self, text: str) -> List[ToolCall]:
        """Extract tool calls from text responses using the TOOL format."""
        import re
        import json
        
        tool_calls = []
        
        # Match TOOL_START{"name": ...}TOOL_END format
        pattern = r'TOOL_START(\{.*?\})TOOL_END'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for i, match in enumerate(matches):
            try:
                data = json.loads(match)
                if "name" in data:
                    tool_call = ToolCall(
                        id=f"call_{i}",
                        name=data["name"],
                        arguments=data.get("arguments", {})
                    )
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        
        # Also try bare JSON without markers if no TOOL format found
        if not tool_calls:
            pattern = r'\{\s*"name"\s*:\s*"([^"]+)"[^}]+\}'
            matches = re.findall(pattern, text)
            for i, name in enumerate(matches):
                args_pattern = r'\{\s*"name"\s*:\s*"' + re.escape(name) + r'"[^}]+\}'
                args_match = re.search(args_pattern, text, re.DOTALL)
                if args_match:
                    try:
                        data = json.loads(args_match.group())
                        tool_call = ToolCall(
                            id=f"call_{i}",
                            name=name,
                            arguments=data.get("arguments", {})
                        )
                        tool_calls.append(tool_call)
                    except json.JSONDecodeError:
                        continue
        
        return tool_calls

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

        # Security check for shell commands
        if tool_name == "execute_shell":
            command = args.get("command", "")
            allowed, reason = self.security.should_allow(
                command=command,
                tool_name=tool_name
            )
            if not allowed:
                logger.warning(f"Command blocked by security: {reason}")
                # Record blocked command in memory
                self.memory.episodic.add_event(
                    "security_blocked",
                    f"Command blocked: {command[:50]} - {reason}",
                    {"command": command, "reason": reason}
                )
                return {"success": False, "error": f"Security: {reason}"}

        try:
            result = await tool.execute(args, {"workdir": self.config.workdir})
            
            # Record tool result for trust gradient learning
            self.security.record_tool_result(
                tool_name,
                result.get("success", False) if isinstance(result, dict) else False
            )
            
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
        self._event_loop = None

    def __iter__(self):
        return self

    def __next__(self):
        import asyncio
        
        if self._async_gen is None:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
            self._async_gen = self._loop.run_async(self._goal)

        try:
            return self._event_loop.run_until_complete(
                self._async_gen.__anext__()
            )
        except StopAsyncIteration:
            raise StopIteration