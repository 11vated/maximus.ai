# Maximus.ai - Local AI Coding Assistant

## Overview
**100% Free (core). Local-first (Ollama). Capable (with opt-in MCP/web for extended reach).**

Maximus.ai is an ambitious local AI coding platform (early 0.1.0, active development) with Claude Code-like UX (core paths 100% local via Ollama; extended MCP/web tools opt-in):
- **AI**: Local Ollama - no API costs, no rate limits
- **Entry Point**: Single unified command `python bin/maximus.py`
- **Safety**: 3-layer system (prompt injection → tool wrapper → user confirmation)
- **Hardware**: Automatic detection with Windows-first fallbacks

## Current UX (Roadmap target: v2.0)

### Single Command Interface
```bash
# Start interactive session (auto-detects hardware)
python bin/maximus.py

# Use specific model
python bin/maximus.py -m 14b

# Model aliases
python bin/maximus.py -m fast   # codellama:7b - quick tasks
python bin/maximus.py -m smart  # qwen2.5-coder:14b - complex code
python bin/maximus.py -m think  # deepseek-r1:7b - reasoning

# Debug mode
python bin/maximus.py --verbose

# Diagnostics
python bin/maximus.py doctor
```

### Deprecated Commands (Hidden)
The following commands are deprecated but still work with warnings:
- `maximus run` → Use `python bin/maximus.py` instead
- `maximus chat` → Use `python bin/maximus.py` instead
- `maximus models` → Use `maximus doctor` instead

## Features

### Core System
- ✅ **8-State Cognitive Loop**: INIT/PLAN/THINK/ACT/VERIFY/COMMIT/PAUSE/REFLECT (core functional in loop.py)
- ~35+ **Tools** (dynamic registry + real MCP integration; read_file, write_file, execute_shell, grep, git, web, system + MCP-wrapped)
- ✅ **Tool Safety**: 3-layer system (layer2 pre-execution enforced; layer3 in UI/auto paths)
- ✅ **Memory**: Short-term + Long-term (MemoryMesh + compaction with Ollama)
- ✅ **Session Persistence**: Basic support
- ✅ **Event Streaming**: Real-time via terminal + hooks (Langfuse-style tracing notes)

### Hardware Detection
- Automatic model selection based on available RAM/GPU
- Windows: Uses wmic/systeminfo for RAM detection
- Falls back to qwen2.5-coder:7b for systems < 16GB RAM

### Safety System
1. **Layer 1**: Prompt injection detection - blocks malicious input
2. **Layer 2**: Tool wrapper - preview required for write operations
3. **Layer 3**: User confirmation - destructive operations need approval

## Quick Start

### Installation
```bash
cd /path/to/maximus.ai   # or your clone of https://github.com/11vated/maximus.ai
pip install -e .
```

### Run (requires Ollama running locally for full LLM cycles)
```bash
# Ensure Ollama is running + model pulled (core is local-first)
ollama serve
ollama pull qwen2.5-coder:7b

# Start Maximus (terminal UI primary; React planned)
python bin/maximus.py
# or: python -m maximus
```

## Architecture

### Key Components
- `bin/maximus.py` - Single entry point
- `src/maximus/core/loop.py` - 8-state agent loop
- `src/maximus/core/safety.py` - 3-layer safety system
- `src/maximus/core/api.py` - Backend API
- `src/maximus/tools/registry.py` - Tool registration
- `src/maximus/ui/terminal.py` - Terminal UI

### Design Patterns
- **Claude Code**: Tool safety, permission system, event streaming
- **Open-SWE**: Middleware stack, LangGraph patterns
- **Nexus**: Cognitive loop, memory system

## Testing

### Python (12 tests passing)
```bash
cd C:\Users\11vat\Desktop\agent007\maximus.ai
pytest tests/e2e/ -v
```

## World-Class Goals - Status

| Feature | Status | Source Pattern |
|---------|--------|---------------|
| 8-State Cognitive Loop | ✅ Core (states + hooks + safety/MCP integration) | loop.py + Nexus patterns |
| ~35+ Tools Registered (dynamic) | Partial / In progress (mocks removed; real MCP manager wired to registry/loop; ~35 incl. builtin + wrappers) | registry + mcp/manager.py |
| Middleware Stack | Partial (core present; full 6-layer aspirational) | middleware/ |
| Docker Sandbox | Local subprocess reliable (default; Docker opt-in via sandbox/) | sandbox.py (post-fix) |
| Vector Memory | Optional (chromadb extra; MemoryMesh primary) | memory/ + vector_memory.py |
| Context Compaction | ✅ (real Ollama summary in compaction.py) | memory/compaction.py |
| Multi-Tab UI | Terminal primary (single-session strong); multi-tab planned | ui/terminal.py |
| Visual Effects | Basic (rich output); advanced planned | ui/ + tui/ |
| WebSocket Events | Partial (api/websocket.py exists; full streaming in terminal) | api/ |
| React Terminal | Planned (see REACT_TERMINAL_PLAN.md + backlog High); CI/Docker refs exist but no source tree | (absent maximus-terminal/) |
| Sub-Agent Spawning | Partial (multi_agent/spawner.py; secondary path) | multi_agent/ |
| Conversation Branching | Partial (memory/branching.py present) | memory/branching.py |
| MCP Integration | Core real (unified manager.py; thin delegates; MCPToolWrapper + register; loop schemas use real list_tools) | mcp/manager.py + tools/mcp_wrapper.py + builtin (mocks removed per Critical backlog) |

## Next Steps (Phase 6+ per execution-plan.md backlog)
- [x] Update stale claims / version / docs mismatch (this pass)
- [ ] Frontend decision (implement minimal TUI enhancements or excise React/CI/Docker refs; High backlog)
- [ ] Full evals/benchmarks harness (Medium)
- [ ] Wire more hidden-gem MCPs + RAG/KG (Phase D: mcp-knowledge-graph etc.)
- [ ] Production polish: real Docker sandbox opt-in, more traces, adapter cleanup
- [ ] Self-improvement loop using library skills + subagents (future-arch)

## License
MIT

## Contributing
See CONTRIBUTING.md for development guidelines.
