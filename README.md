# Maximus.ai - World-Class Coding Agent

## Overview
**100% Free. 100% Unlimited. 100% Capable.**

Maximus.ai is a world-class coding agent built entirely with free, local tools:
- **Backend**: Python >=3.11 with 32 registered tools
- **Frontend**: React + TypeScript with advanced terminal UI
- **AI**: Local Ollama (qwen2.5-coder:7b) - no API costs
- **Architecture**: Hybrid of Nexus + Open-SWE + Claude Code patterns

## Features

### Backend (Python - 171 tests passing)
- ✅ **8-State Cognitive Loop**: INIT → PLAN → ACT → OBSERVE → REFLECT → ADAPT → COMMIT → PAUSE
- ✅ **32 Tools Registered**: read_file, write_file, execute_shell, grep, git tools, web_search, etc.
- ✅ **Middleware Stack**: ToolError, MessageQueue, Sanitize, StepLimit (Open-SWE pattern)
- ✅ **Memory System**: Short-term (rolling window) + Long-term (ChromaDB optional)
- ✅ **Context Compaction**: 2-layer pipeline (rule-based + AI summary)
- ✅ **Sub-Agent Spawning**: 5 agent types (general, coder, reviewer, researcher, tester)
- ✅ **Conversation Branching**: Git-like branches + commit history
- ✅ **MCP Integration**: Model Context Protocol support
- ✅ **Stance System**: 7 behavior modes (exploratory, methodical, etc.)
- ✅ **Sandbox Integration**: Docker-based isolated execution (Nexus pattern)
- ✅ **Session Memory Sync**: Persistent sessions across tabs

### Frontend (React - Build passing)
- ✅ **Multi-Tab Support**: Create/switch/close tabs with independent sessions
- ✅ **Visual Effects**: Particle background, glitch, scanlines, CRT curve
- ✅ **4 Themes**: Cyberpunk Neon, Retro CRT, Minimalist, Data-Driven
- ✅ **WebSocket Integration**: Real-time agent state updates
- ✅ **Command Line**: Fixed contentEditable input (working)
- ✅ **Agent Visualizer**: Shows current cognitive state
- ✅ **TypeScript Build**: Clean compilation (332KB JS bundle)

## Quick Start

### Backend
```bash
# Install
cd C:\Users\11vat\Desktop\agent007\maximus.ai
pip install -e .

# Start Ollama (in another terminal)
ollama serve

# Pull model
ollama pull qwen2.5-coder:7b

# Run CLI
maximus "create a hello world script"

# Start API server
python -m uvicorn maximus.api.routes:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd C:\Users\11vat\Desktop\agent007\maximus.ai\maximus-terminal
npm install
npm run dev  # Dev server at http://localhost:5173
npm run build  # Production build
```

## Architecture

### Hybrid Design (Best of 3 Repos)
1. **Nexus**: 8-state cognitive loop, Docker sandbox, vector memory
2. **Open-SWE**: Middleware stack, LangGraph patterns, webhook integrations
3. **Claude Code**: Event streaming, tool safety, permission system

### Key Files
- `src/maximus/core/loop.py` - 8-state agent loop
- `src/maximus/tools/registry.py` - Tool registration (32 tools)
- `src/maximus/middleware/` - Open-SWE middleware stack
- `src/maximus/memory/compaction.py` - 2-layer context compaction
- `src/maximus/api/websocket.py` - Real-time event streaming
- `maximus-terminal/src/components/` - React terminal components

## Testing

### Python (171 tests passing)
```bash
cd C:\Users\11vat\Desktop\agent007\maximus.ai
pytest tests/ -v
```

### React (2 tests passing)
```bash
cd C:\Users\11vat\Desktop\agent007\maximus.ai\maximus-terminal
npx vitest run
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

## Next Steps (Phase 3-4)
- [ ] Virtual scrolling for terminal output
- [ ] Error boundaries + retry logic
- [ ] E2E tests with Playwright
- [ ] Docker Compose for full stack
- [ ] Production deployment guide

## License
MIT

## Contributing
See CONTRIBUTING.md for development guidelines.
