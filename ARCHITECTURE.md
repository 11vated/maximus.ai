# Maximus.ai Architecture

## Overview
Maximus.ai is a 100% free, unlimited, and capable coding agent built by merging patterns from:
- **open-swe** (LangChain) - Middleware stack, cloud sandbox patterns
- **collection-claude-code-source-code** (ClawSpring) - Event streaming, tool registry, memory layers
- **Nexus** - 8-state cognitive loop, stance system, local-first architecture

## Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Maximus.ai Agent                        │
├─────────────────────────────────────────────────────────────┤
│  Triggers: CLI / Local File / Git Hooks (no cloud)         │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Middleware   │───▶│ Cognitive    │───▶│ Planner      │  │
│  │ (6-layer)  │    │ Loop (8-state│    │ (Ollama LLM) │  │
│  └─────────────┘    └──────────────┘    └──────────────┘  │
│                           │                     │             │
│                           ▼                     ▼             │
│                    ┌──────────────┐   ┌──────────────┐     │
│                    │ Memory       │   │ Executor      │     │
│                    │ (Dual-scope) │   │ (Tool        │     │
│                    └──────────────┘   │  Dispatch)   │     │
│                           │           └──────────────┘     │
│                           ▼                     ▼             │
│                    ┌──────────────┐   ┌──────────────┐     │
│                    │ Tools        │◀──│ Reflector     │     │
│                    │ (26+ local)  │   │ (Quality      │     │
│                    └──────────────┘   │  Assessment)  │     │
│                                        └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Cognitive Loop (`core/loop.py`)
- **8 States**: INIT → PLAN → ACT → OBSERVE → REFLECT → ADAPT → COMMIT → PAUSE
- **Event Streaming**: TextChunk, ThinkingChunk, ToolStart, ToolEnd, TurnDone, StateChange
- **Hybrid Design**: Nexus state machine + ClawSpring event streaming

### 2. Tool System (`tools/`)
- **Base**: `BaseTool` ABC with metadata (name, permission_level, local_only)
- **Registry**: Global `ToolRegistry` with register/dispatch/schema generation
- **29 Builtin Tools**:
  - File: `read_file`, `write_file`, `edit_file`, `move_file`, `copy_file`, `delete_file`, `create_dir`
  - Search: `grep`, `glob`, `web_search`, `browse_url`
  - Execution: `execute_shell`, `run_python`, `run_node`, `run_tests`
  - Git: `git_status`, `git_diff`, `git_add`, `git_commit`, `git_push`
  - System: `ls`, `sleep`, `datetime`, `env_info`, `system_info`, `list_processes`
  - Repo Analysis: `analyze_open_swe`, `analyze_clawspring`, `analyze_nexus`
- **Permission Levels**: `safe` (auto-approve), `write` (confirm), `dangerous` (strict check)
- **Safety**: `execute_shell` checks against SAFE_COMMANDS whitelist

### 3. Memory Systems (`memory/`)
- **ShortTermMemory**: Rolling window (last 50 messages) via `deque`
- **LongTermMemory**: Persistent store at `~/.maximus/memory/`
  - File-based: `MEMORY.md` injection into prompts (ClawSpring pattern)
  - Optional: ChromaDB vector store for semantic search

### 4. Intelligence Layer (`intelligence/`)
- **Planner**: LLM-based task decomposition (Nexus pattern)
  - Converts goals into ordered `Step` objects with dependencies
  - Outputs JSON with steps, success_criteria, risk_flags
- **Reflector**: Quality assessment (Nexus pattern)
  - Evaluates plan execution against success criteria
  - Provides confidence scores and revision suggestions

### 5. LLM Client (`utils/llm.py`)
- **OllamaClient**: 100% free local inference via Ollama API
  - Models: `qwen2.5-coder:7b`, `deepseek-coder-v2:16b`, etc.
  - Endpoints: `/api/chat` (streaming), `/api/generate` (non-streaming)
- **LLMClient**: Unified client supporting Ollama (default) + OpenAI (optional)
  - Routes to appropriate backend based on model name

### 6. Middleware Stack (`middleware/`)
- **SanitizeInputsMiddleware**: Prevent injection in tool inputs
- **RateLimitMiddleware**: Enforce `max_model_calls` limit
- **AuditLogMiddleware**: Log all actions for audit trail
- **Pluggable**: Additional middleware can be added to the 6-layer stack

### 7. CLI (`cli.py`)
- **Commands**:
  - `maximus run "prompt"`: Execute a single prompt
  - `maximus chat`: Interactive chat session
  - `maximus status`: Check Ollama, Python, directories
- **Rich Output**: Formatted panels, colored text, progress indicators

### 8. Stance System (`intelligence/stance.py`) - NEW
- **7 Behavior Modes**: exploratory, methodical, creative, surgical, architectural, debugging, learning
- **Adaptive**: Auto-suggests stance based on goal keywords
- **Planning Context**: Modifies temperature, iteration count, reflection depth
- **StanceManager**: Switch stances dynamically during execution

### 9. Conversation Branching (`memory/branching.py`) - NEW
- **Git-like Branches**: Create, switch, merge, delete branches
- **Commit History**: Track state, goals, plans, results per commit
- **BranchManager**: Persistent storage at `.maximus/branches.json`
- **State Reconstruction**: Replay agent state at any commit

### 10. MCP Integration (`mcp/manager.py`) - NEW
- **Model Context Protocol**: Connect to MCP-compatible servers
- **Tool Discovery**: List tools from MCP servers dynamically
- **MCPManager**: Manage multiple MCP server connections
- **Async Support**: Full async/await support for tool execution

### 11. Context Compaction (`memory/compaction.py`) - NEW
- **2-Layer Pipeline**: Rule-based (Layer 1) + AI Summary (Layer 2)
- **Rule-Based**: Pattern matching, max items, priority system
- **AI Summarization**: Compress old messages while preserving recent context
- **CompactionManager**: Configurable token limits and preservation rules

## Data Flow

### Planning Phase
```
User Prompt → Orchestrator → Middleware → Planner (LLM) → Plan (steps + criteria)
```

### Execution Phase
```
Plan → AgentLoop (state=ACT) → Executor → ToolRegistry → Tool.execute() → Result
```

### Reflection Phase
```
Results → Reflector (LLM) → QualityReport (confidence, needs_revision) → Decision
```

## Design Principles

1. **100% Free**: No paid APIs, all local (Ollama)
2. **100% Unlimited**: No rate limits, no usage caps
3. **100% Capable**: Full agent loop, planning, reflection, memory
4. **Local-First**: All processing on-device, no cloud dependencies
5. **Safety-First**: Permission levels, dangerous command blocking, audit logs
6. **Extensible**: Plugin architecture for tools, middleware, adapters

## Security Model

### Permission Levels
- **safe**: Read-only operations, auto-approved (e.g., `read_file`, `grep`, `ls`)
- **write**: Modifies files, requires confirmation in "auto" mode (e.g., `write_file`, `git_commit`)
- **dangerous**: High-risk operations, strict checks (e.g., `execute_shell`, `delete_file`)

### Trust Levels (from Nexus)
- **untrusted**: All actions require approval
- **basic**: Safe operations auto-approved
- **verified**: Write operations auto-approved
- **privileged**: All actions auto-approved

### Safety Mechanisms
- `execute_shell` whitelist: Only safe commands (ls, git, python, etc.)
- Middleware chain for cross-cutting concerns
- Audit logging for all actions
- Local-only enforcement (tools marked `local_only=True`)

## Future Enhancements

1. **SWE-bench Integration**: Benchmark agent performance
2. **TUI Interface**: Textual-based terminal UI (from Nexus)
3. **Hook System**: Event-driven extensions (from Nexus)
4. **Multi-Agent Orchestration**: Parallel agent execution (from ClawSpring)
5. **Docker Support**: Optional containerized deployment
6. **Sub-Agent Spawning**: Specialized agent types (from ClawSpring)

## File Structure
```
maximus.ai/
├── src/maximus/
│   ├── core/            # Agent loop, models
│   │   ├── __init__.py
│   │   └── loop.py      # 8-state cognitive loop
│   ├── tools/           # Tool system
│   │   ├── base.py      # BaseTool ABC
│   │   ├── registry.py  # ToolRegistry
│   │   ├── builtin/     # 29 builtin tools
│   │   └── __init__.py
│   ├── memory/          # Memory systems
│   │   ├── short_term.py
│   │   ├── long_term.py
│   │   ├── branching.py # Conversation branching (NEW)
│   │   ├── compaction.py # Context compaction (NEW)
│   │   └── __init__.py
│   ├── intelligence/    # Planner, Reflector
│   │   ├── planner.py
│   │   ├── reflector.py
│   │   ├── stance.py    # Stance system (NEW)
│   │   └── __init__.py
│   ├── adapters/        # Repo-specific adapters
│   │   ├── open_swe_adapter.py
│   │   ├── clawspring_adapter.py
│   │   ├── nexus_adapter.py
│   │   └── __init__.py
│   ├── mcp/            # MCP integration (NEW)
│   │   ├── manager.py
│   │   └── __init__.py
│   ├── middleware/      # Middleware stack
│   │   ├── base.py
│   │   └── __init__.py
│   ├── utils/           # LLM client, config
│   │   ├── llm.py
│   │   └── __init__.py
│   ├── cli.py           # CLI entry point
│   ├── __init__.py
│   └── __main__.py     # python -m maximus support (NEW)
├── tests/
│   ├── unit/           # 16+ unit tests
│   ├── test_repo_adapters.py  # 10 adapter tests (NEW)
│   ├── test_integration.py    # 8 integration tests (NEW)
│   └── conftest.py
├── docs/                # Documentation
├── scripts/             # Install, verify scripts
├── pyproject.toml      # Package config
├── README.md           # User documentation
├── ARCHITECTURE.md     # This file
├── AGENTS.md           # AI agent guide
└── .env.example        # Configuration template
```

## Quick Start

```bash
# Install Ollama
ollama serve  # Start Ollama server
ollama pull qwen2.5-coder:7b  # Pull model

# Install Maximus.ai
cd C:\Users\11vat\Desktop\agent007\maximus.ai
pip install -e .

# Run
maximus run "List all Python files"
maximus chat  # Interactive mode
maximus status  # Check system
```

## License
MIT
