"""Maximus Backend API - Unified single entry point.

This is the only interface the UI knows about.
"""
import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

from maximus.utils.llm import LLMClient
from maximus.tools.registry import get_registry, ToolRegistry
from maximus.core.safety import SafetyController
from maximus.models import AgentConfig

logger = logging.getLogger(__name__)


class Session:
    """User session with message history."""
    
    def __init__(self, session_id: str, model: str):
        self.session_id = session_id
        self.model = model
        self.messages: List[Dict[str, str]] = []
        self.created_at = None
        
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "model": self.model,
            "messages": self.messages,
            "created_at": self.created_at
        }


class MaximusBackend:
    """Unified backend API - the single entry point for UI.
    
    Responsibilities:
    - Process user messages through LLM
    - Execute tools safely
    - Manage session state
    - Apply safety layers
    """
    
    def __init__(self, model: str = None):
        self.model = model or "qwen2.5-coder:7b"
        self.llm = LLMClient(AgentConfig(model=self.model))
        self.registry = get_registry()
        self.safety = SafetyController()
        
        # Session management
        self.sessions: Dict[str, Session] = {}
        self.sessions_dir = Path.home() / ".local" / "maximus" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # System prompt
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build system prompt with safety rules."""
        return """You are Maximus, a helpful coding assistant.

CRITICAL RULES:
- Before writing to ANY file, call preview_write with the exact content
- Wait for user confirmation BEFORE making any changes
- Only execute commands you understand
- Be concise and helpful

When user asks to write/edit files:
1. Call preview_write with exact content
2. Explain what will happen
3. Wait for their confirmation
"""
    
    def process_message(self, user_input: str, session_id: str = None) -> str:
        """Main entry point - process user message and return response.
        
        This is the ONLY method the UI should call.
        """
        # Get or create session
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
        else:
            session_id = session_id or str(uuid.uuid4())[:8]
            session = Session(session_id, self.model)
            self.sessions[session_id] = session
            
        # Add user message
        session.add_message("user", user_input)
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + session.messages
        
        # Get LLM response (non-streaming for simplicity)
        try:
            response = self._get_llm_response(messages)
            
            # Add assistant response
            session.add_message("assistant", response)
            
            # Save session
            self._save_session(session)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I encountered an error: {e}"
    
    def _get_llm_response(self, messages: List[Dict]) -> str:
        """Get response from LLM with tool calling."""
        
        # Get tool schemas
        schemas = self.registry.to_schemas()
        
        full_response = ""
        
        # Call LLM with tools
        import asyncio
        async def call_llm():
            nonlocal full_response
            async for chunk in self.llm.chat(messages, tools=schemas):
                if chunk.get("message", {}).get("content"):
                    full_response += chunk["message"]["content"]
                    
                # Check for tool calls
                if "tool_calls" in chunk.get("message", {}):
                    for tc in chunk["message"]["tool_calls"]:
                        tool_name = tc.get("function", {}).get("name", "")
                        tool_args = tc.get("function", {}).get("arguments", {})
                        
                        # Execute tool with safety
                        result = self._execute_tool_safely(tool_name, tool_args)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "content": json.dumps(result),
                            "name": tool_name
                        })
        
        asyncio.run(call_llm())
        
        return full_response if full_response else "I'm ready to help with your code."
    
    def _execute_tool_safely(self, tool_name: str, params: dict) -> dict:
        """Execute tool with safety layers."""
        
        # Layer 2: Tool wrapper safety
        self.safety.layer2_check(tool_name, params, {})
        
        # Execute tool
        tool = self.registry.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            # Import asyncio and run sync tool
            import asyncio
            result = asyncio.run(tool.execute(params, {}))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_tool(self, tool_name: str, params: dict) -> dict:
        """Execute a tool directly (internal use)."""
        return self._execute_tool_safely(tool_name, params)
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID, or create new one if doesn't exist."""
        if session_id not in self.sessions:
            session = Session(session_id, self.model)
            self.sessions[session_id] = session
        return self.sessions.get(session_id)
    
    def _save_session(self, session: Session):
        """Save session to disk."""
        try:
            path = self.sessions_dir / f"{session.session_id}.json"
            with open(path, 'w') as f:
                json.dump(session.to_dict(), f)
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
    
    def shutdown(self):
        """Clean shutdown."""
        # Save all sessions
        for session in self.sessions.values():
            self._save_session(session)
        logger.info("Maximus backend shutdown complete")