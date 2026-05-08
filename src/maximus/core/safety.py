"""Safety Controller - Three-layer safety system.

Implements Claude Code-style safety:
- Layer 1: Prompt injection (system prompt rules)
- Layer 2: Tool wrapper (pre-check before execution)
- Layer 3: User confirmation (interactive approval)
"""
import logging

logger = logging.getLogger(__name__)


class SafetyError(Exception):
    """Safety check failed."""
    pass


class SafetyController:
    """Three-layer safety system."""
    
    # Tools that require preview before execution
    PREVIEW_REQUIRED_TOOLS = [
        "write_file",
        "edit_file", 
        "delete_file",
        "move_file",
        "copy_file",
    ]
    
    # Tools that are always safe (no confirmation needed)
    SAFE_TOOLS = [
        "ls",
        "grep",
        "glob",
        "read_file",
        "cat",
        "pwd",
    ]
    
    # Tools that require explicit confirmation
    DESTRUCTIVE_TOOLS = [
        "execute_shell",
        "delete_file",
        "write_file",
        "edit_file",
    ]
    
    def __init__(self):
        self.preview_called = {}  # Track preview_write calls per session
        
    def layer1_prompt_injection(self, prompt: str) -> str:
        """Layer 1: Inject safety rules into system prompt.
        
        This is called when building the initial system prompt.
        Returns modified prompt with safety rules.
        """
        safety_rules = """
CRITICAL RULES:
- Before writing to ANY file, call preview_write with the exact content
- Wait for user confirmation BEFORE making any changes
- Only execute commands you understand

When user asks to write/edit files:
1. Call preview_write with exact content
2. Explain what will happen  
3. Wait for their confirmation
"""
        return f"{prompt}\n{safety_rules}"
    
    def layer2_check(self, tool_name: str, params: dict, context: dict):
        """Layer 2: Tool wrapper - check if tool call is allowed.
        
        This is called BEFORE tool execution.
        Raises SafetyError if tool call is not allowed.
        """
        session_id = context.get("session_id", "default")
        
        # Check if tool requires preview
        if tool_name in self.PREVIEW_REQUIRED_TOOLS:
            # Check if preview was called in this session recently
            last_preview = self.preview_called.get(session_id, 0)
            import time
            current_time = time.time()
            
            # Preview valid for 60 seconds
            if current_time - last_preview > 60:
                raise SafetyError(
                    f"preview_write must be called before {tool_name}. "
                    f"Please call preview_write first to show the planned changes."
                )
        
        # Check for dangerous shell commands
        if tool_name == "execute_shell":
            command = params.get("command", "")
            dangerous_patterns = [
                "rm -rf /",
                "dd if=",
                "mkfs",
                "> /dev/",
                "curl.*\\|.*sh",
                "wget.*\\|.*sh",
            ]
            import re
            for pattern in dangerous_patterns:
                if re.search(pattern, command):
                    raise SafetyError(f"Command blocked: potentially dangerous pattern '{pattern}'")
    
    def layer3_confirm(self, action: str) -> bool:
        """Layer 3: User confirmation for destructive actions.
        
        This is called during tool execution for destructive actions.
        Returns True if user confirms, False otherwise.
        
        Note: In the terminal UI, this should show [y/N] prompt.
        For now, returns True for automated execution (can be enhanced later).
        """
        if action in self.DESTRUCTIVE_TOOLS:
            # For automated mode, we'll allow with warning
            # The actual confirmation happens in the UI layer
            logger.warning(f"Destructive action: {action}")
            return True
        return True
    
    def record_preview(self, session_id: str):
        """Record that preview_write was called for this session."""
        import time
        self.preview_called[session_id] = time.time()


# Global safety controller instance
_safety_controller = None

def get_safety_controller() -> SafetyController:
    """Get global safety controller."""
    global _safety_controller
    if _safety_controller is None:
        _safety_controller = SafetyController()
    return _safety_controller