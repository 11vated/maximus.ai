# Maximus.ai - Local AI Coding Assistant

## Overview
**100% Free. 100% Local. 100% Capable.**

Maximus.ai is a production-ready local coding assistant with Claude Code-like UX:
- **AI**: Local Ollama - no API costs, no rate limits
- **Entry Point**: Single unified command `python bin/maximus.py`
- **Safety**: 3-layer system (prompt injection → tool wrapper → user confirmation)
- **Hardware**: Automatic detection with Windows-first fallbacks

## v2.0 UX

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
- ✅ **8-State Cognitive Loop**: INIT → PLAN → ACT → OBSERVE → REFLECT → ADAPT → COMMIT → PAUSE
- ✅ **34+ Tools**: read_file, write_file, execute_shell, grep, glob, git, web tools
- ✅ **Tool Safety**: 3-layer system with permission levels
- ✅ **Memory**: Short-term (50 message rolling window) + Long-term (persistent store)
- ✅ **Session Persistence**: Resume previous sessions with --session flag
- ✅ **Event Streaming**: Real-time token-by-token output

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
cd C:\Users\11vat\Desktop\agent007\maximus.ai
pip install -e .
```

### Run
```bash
# Ensure Ollama is running
ollama serve

# Pull model (if not already)
ollama pull qwen2.5-coder:7b

# Start Maximus
python bin/maximus.py
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
| 8-State Cognitive Loop | ✅ Complete | Nexus |
| 32 Tools Registered | ✅ Complete | ClawSpring |
| Middleware Stack | ✅ Complete | Open-SWE |
| Docker Sandbox | ✅ Complete | Nexus |
| Vector Memory | ✅ Complete | Nexus |
| Context Compaction | ✅ Complete | Maximus (enhanced) |
| Multi-Tab UI | ✅ Complete | Maximus (new) |
| Visual Effects | ✅ Complete | Maximus (new) |
| WebSocket Events | ✅ Complete | ClawSpring |
| React Terminal | ✅ Build passes | Maximus (new) |
| Typing Fixed | ✅ Complete | N/A (bug fix) |
| Sub-Agent Spawning | ✅ Complete | Nexus |
| Conversation Branching | ✅ Complete | Maximus (new) |
| MCP Integration | ✅ Complete | Maximus (new) |

## Next Steps (Phase 6+)
- [ ] TUI overhaul with Textual
- [ ] MCP server integration
- [ ] Advanced benchmarking tools

## License
MIT

## Contributing
See CONTRIBUTING.md for development guidelines.
