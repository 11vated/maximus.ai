# Maximus.ai Architecture Design
**Phase 2 Deliverable**

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INPUT                              │
│                  "maximus" or "maximus --model 14b"          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    ENTRY POINT                               │
│              bin/maximus (shell wrapper)                     │
│  - Parses arguments                                          │
│  - Starts Ollama if needed                                    │
│  - Launches terminal UI                                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 TERMINAL UI (Frontend)                      │
│              maximus/ui/terminal.py                          │
│  - Chat interface (prompt_toolkit/textual)                   │
│  - User input → Backend API                                   │
│  - Response streaming → User                                  │
│  - Session persistence                                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND API                                │
│              maximus/core/api.py                            │
│  - process_message(user_input, session_id)                  │
│  - run_tool(tool_name, params)                               │
│  - Manages session state                                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────────┐
│   TOOL         │ │   LLM       │ │   SAFETY            │
│   REGISTRY     │ │   CLIENT    │ │   CONTROLLER        │
│                │ │             │ │                     │
│ - read_file    │ │ - Ollama    │ │ - Prompt injection  │
│ - write_file   │ │ - Model     │ │ - Tool wrapper      │
│ - execute_shell│ │   selection │ │ - User confirmation  │
│ - grep         │ │ - Streaming │ │                     │
│ - preview_write│ │             │ │                     │
└─────────────────┘ └─────────────┘ └─────────────────────┘
```

---

## 2. Module Boundaries

### 2.1 Entry Point (`bin/maximus`)
```python
#!/bin/bash
# Simple wrapper that:
# 1. Checks --model flag
# 2. Ensures Ollama running (start if not)
# 3. Launches: python -m maximus.ui.terminal
```

### 2.2 Terminal UI (`src/maximus/ui/`)
| File | Responsibility |
|------|----------------|
| `terminal.py` | Main UI loop, input/output |
| `session.py` | Session state, history |
| `render.py` | Response formatting |

### 2.3 Backend Core (`src/maximus/core/`)
| File | Responsibility |
|------|----------------|
| `api.py` | Unified API - single entry point for UI |
| `agent.py` | Tool-calling LLM orchestration |
| `safety.py` | Three-layer safety controller |

### 2.4 Tool Registry (`src/maximus/tools/`)
| File | Responsibility |
|------|----------------|
| `registry.py` | Tool registration, dispatch |
| `builtin/*.py` | Individual tool implementations |
| `preview.py` | preview_write tool for safety |

### 2.5 LLM Client (`src/maximus/utils/`)
| File | Responsibility |
|------|----------------|
| `llm.py` | Ollama client, streaming |
| `model_selector.py` | Hardware-based model selection |

---

## 3. Key API Definitions

### 3.1 Backend API (`maximus/core/api.py`)
```python
class MaximusBackend:
    """Single unified API - the only interface the UI knows about."""
    
    def __init__(self, model: str = None):
        # Initialize with auto-model selection if not specified
    
    def process_message(self, user_input: str, session_id: str = None) -> str:
        """
        Main entry point - takes user message, returns agent response.
        Handles: LLM call, tool execution, safety checks, response streaming.
        """
        pass
    
    def run_tool(self, tool_name: str, params: dict) -> dict:
        """
        Execute a tool (internal use).
        Returns: {"success": bool, "result": any, "error": str}
        """
        pass
    
    def get_session(self, session_id: str) -> Session:
        """Retrieve or create session."""
        pass
    
    def shutdown(self):
        """Clean shutdown."""
        pass
```

### 3.2 Tool Registry (`maximus/tools/registry.py`)
```python
class ToolRegistry:
    """Registry - the ONLY way tools are accessed."""
    
    def register(self, tool: BaseTool):
        """Register a tool."""
        pass
    
    def execute(self, name: str, params: dict, context: dict) -> dict:
        """Execute tool with safety wrapper."""
        pass
    
    def list_tools(self) -> List[str]:
        """List available tool names."""
        pass
    
    def get_schema(self, name: str) -> dict:
        """Get tool schema for LLM."""
        pass
```

### 3.3 Safety Controller (`maximus/core/safety.py`)
```python
class SafetyController:
    """Three-layer safety system."""
    
    def layer1_prompt_injection(self, prompt: str) -> str:
        """Add safety rules to system prompt."""
        pass
    
    def layer2_tool_wrapper(self, tool_name: str, params: dict) -> bool:
        """
        Check if tool call is allowed.
        Returns True if allowed, raises SafetyError if blocked.
        """
        pass
    
    def layer3_user_confirmation(self, action: str) -> bool:
        """
        Ask user for confirmation on destructive actions.
        Returns True if confirmed.
        """
        pass
```

---

## 4. Auto-Config Logic

### 4.1 Hardware Detection (`maximus/utils/hardware.py`)
```python
def detect_hardware() -> dict:
    """
    Returns:
    {
        "ram_gb": int,
        "vram_gb": int,
        "has_gpu": bool,
        "is_apple_silicon": bool,
        "os": "linux" | "darwin" | "windows"
    }
    """
    pass

def select_default_model(hardware: dict) -> str:
    """
    Model selection based on hardware:
    - < 6GB VRAM: qwen2.5-coder:7b
    - 6-8GB VRAM: qwen2.5-coder:14b  
    - > 8GB VRAM: qwen2.5-coder:14b
    - Apple Silicon: qwen2.5-coder:7b
    - No GPU: codellama:7b
    """
    pass
```

### 4.2 Ollama Management
```python
def ensure_ollama_running() -> bool:
    """
    1. Check if Ollama responding on localhost:11434
    2. If not, try to start: subprocess.Popen(["ollama", "serve"])
    3. Wait for up to 10 seconds for startup
    4. Return True if running
    """
    pass
```

---

## 5. Session Persistence

### 5.1 Session Storage
- Location: `~/.local/share/maximus/sessions/`
- Format: JSON files named `{session_id}.json`
- Contents: messages history, selected model, metadata

### 5.2 Session Schema
```json
{
    "session_id": "uuid",
    "created_at": "ISO timestamp",
    "model": "qwen2.5-coder:7b",
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "last_activity": "ISO timestamp"
}
```

---

## 6. Safety Implementation Details

### Layer 1: Prompt Injection
```python
SYSTEM_PROMPT = """You are Maximus, a helpful coding assistant.

CRITICAL RULES:
- Before writing to ANY file, call preview_write with the exact content
- Wait for user confirmation BEFORE making any changes
- Only execute commands you understand

When user asks to write/edit files:
1. Call preview_write with exact content
2. Explain what will happen
3. Wait for their confirmation
"""
```

### Layer 2: Tool Wrapper
```python
async def execute_with_safety(tool_name, params, context):
    # Check if this is a write operation
    if tool_name in ["write_file", "edit_file", "delete_file"]:
        # Require preview_write was called in same turn
        if not context.get("preview_called"):
            raise SafetyError(
                "preview_write must be called before " + tool_name
            )
    
    # Execute tool
    return await tool_registry.execute(tool_name, params)
```

### Layer 3: User Confirmation
```python
def confirm_destructive(action: str) -> bool:
    """Show [y/N] prompt for destructive actions."""
    response = input(f"⚠️  {action}? [y/N] ")
    return response.lower().startswith('y')
```

---

## 7. Unified Entry Point Implementation

### 7.1 The `maximus` command
```bash
#!/bin/bash
# bin/maximus

# Parse --model flag
MODEL_FLAG=""
if [[ "$1" == "--model" || "$1" == "-m" ]]; then
    MODEL_FLAG="--model $2"
    shift 2
fi

# Ensure Ollama running
python -c "from maximus.utils.ollama import ensure_ollama_running; ensure_ollama_running()"

# Launch terminal UI
python -m maximus.ui.terminal $MODEL_FLAG
```

---

## 8. File Structure After Refactoring

```
maximus/
├── bin/
│   └── maximus                    # Entry point script
├── src/maximus/
│   ├── __main__.py               # python -m maximus entry
│   ├── cli.py                    # DEPRECATED (keep for backward compat)
│   ├── core/
│   │   ├── api.py                # NEW: Unified API
│   │   ├── agent.py               # NEW: Agent orchestration
│   │   ├── safety.py             # NEW: Safety controller
│   │   └── loop.py               # Keep: Agent loop (refactored)
│   ├── tools/
│   │   ├── registry.py           # Keep: Tool registry
│   │   ├── preview.py             # NEW: preview_write tool
│   │   └── builtin/              # Keep: Existing tools
│   ├── ui/
│   │   ├── terminal.py           # NEW: Terminal UI
│   │   ├── session.py            # NEW: Session management
│   │   └── render.py             # NEW: Response rendering
│   └── utils/
│       ├── llm.py                # Keep: LLM client
│       ├── ollama.py             # NEW: Ollama management
│       └── hardware.py           # NEW: Hardware detection
├── config/
│   └── default.yaml              # Default config template
└── tests/
    ├── test_api.py               # NEW: API tests
    ├── test_safety.py            # NEW: Safety layer tests
    └── test_hardware.py          # NEW: Model selection tests
```

---

## 9. Migration Path

| Old Component | New Component | Action |
|---------------|---------------|--------|
| `maximus run` | `maximus` | Redirect |
| `maximus chat` | `maximus` | Redirect |
| `maximus models` | Internal only | Remove from help |
| `maximus config` | `~/.config/maximus/` | Move to file |
| `maximus discover` | Internal tool | Remove from CLI |
| `maximus status` | `maximus doctor` | Keep as hidden |

---

**END OF ARCHITECTURE DESIGN**

Ready for Phase 3: Implementation