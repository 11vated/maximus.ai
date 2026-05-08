# Maximus.ai Product Requirements Document
**Phase 1 Deliverable**

---

## 1. Product Vision

Create a seamless, production-ready coding assistant that feels as simple as typing `claude` - where the user types one command and immediately gets a helpful coding partner, with all complexity hidden behind the scenes.

## 2. Target Users

- Software developers who want a local, privacy-first coding assistant
- Users who prefer command-line tools but want polish
- Developers who don't want to manage infrastructure (Ollama, models, etc.)

---

## 3. User Stories

### Story 1: The "Just Start" Experience
> "As a developer, I type `maximus` with no arguments and immediately get a helpful chat prompt where I can discuss my code, ask questions, or request changes - without needing to know anything about models, Ollama, or system configuration."

### Story 2: Automatic Backend Management
> "As a user, I don't want to know that Ollama exists. When I type `maximus`, the system should detect if Ollama is running, start it if needed, and select a good model - all transparently."

### Story 3: Single Command, Multiple Tasks
> "As a user, I want to use the same `maximus` command for everything - simple questions, file edits, running tests, exploring code. I shouldn't need separate commands for different modes."

### Story 4: Safe File Operations
> "When the agent wants to write or modify files, I want to confirm first. The system should ask before any destructive change, not auto-execute."

### Story 5: Hardware-Aware Defaults
> "On my M1 Mac, the system should automatically use a model that runs well. On my GPU Linux box, it should use a larger model. I shouldn't configure this manually."

---

## 4. Functional Requirements

### 4.1 Primary Command (FR-1)
- The command `maximus` (with no arguments) shall start an interactive, persistent chat session
- This is the ONLY command 95% of users should ever need
- Session persists until user types `exit`, `quit`, or presses Ctrl+C

### 4.2 Model Selection (FR-2)
- Users may optionally specify `--model` or `-m` flag: `maximus --model 14b`
- Model selection is an OPT-IN feature, not a requirement
- Available aliases: 7b, 14b, fast, smart, think (mapping to actual Ollama models)

### 4.3 Auto-Backend Management (FR-3)
- On `maximus` startup:
  1. Check if Ollama is running (poll localhost:11434)
  2. If not running, attempt to start `ollama serve` in background
  3. Detect hardware (RAM, GPU, Apple Silicon)
  4. Select default model based on hardware
  5. If user specified `--model`, use that instead

### 4.4 Default Model Selection Logic (FR-4)
| Hardware | Default Model |
|----------|---------------|
| < 6GB VRAM | qwen2.5-coder:7b |
| 6-8GB VRAM | qwen2.5-coder:14b |
| > 8GB VRAM | qwen2.5-coder:14b |
| Apple Silicon | qwen2.5-coder:7b |
| No GPU | codellama:7b |

### 4.5 Terminal UI (FR-5)
- Single chat interface with prompt `>>> `
- Stream agent responses in real-time
- Support Ctrl+C (graceful exit), Ctrl+L (clear screen)
- Show minimal internal state - only conversation, not events/states
- Enable `--verbose` flag for debugging (hidden from normal help)

### 4.6 Safety Layers (FR-6)

**Layer 1 - Prompt Injection:**
- System prompt includes: "Before writing to any file, call preview_write tool and wait for user confirmation"

**Layer 2 - Tool Wrapper:**
- write_file tool checks: was preview_write called in same turn?
- If not: reject with "Preview required before write"

**Layer 3 - User Confirmation:**
- Any destructive action (delete, rm, write) shows `[y/N]` prompt
- Default is NO - user must explicitly approve
- Safe operations (read, grep, ls) auto-approved

### 4.7 Configuration (FR-7)
- All configuration stored in `~/.config/maximus/config.yaml`
- First run creates config with auto-detected model
- User can edit config file directly for customization
- No `maximus config` command needed for normal use

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Startup time: < 3 seconds to first prompt (excluding Ollama cold start)
- Response time: stream within 500ms of model response

### 5.2 Reliability
- Graceful handling if Ollama crashes - allow retry
- Session persistence - resume from last state on restart

### 5.3 User Experience
- No exposed internal state in normal mode
- Error messages should be human-readable, not stack traces
- Help should be minimal - "maximus --help" shows simple usage

---

## 6. Commands to Consolidate

| Old Command | New Behavior |
|-------------|--------------|
| `maximus run` | DEPRECATED - use `maximus` |
| `maximus chat` | DEPRECATED - use `maximus` |
| `maximus models` | REMOVED (diagnostic only, hidden) |
| `maximus config` | REMOVED (use `~/.config/maximus/config.yaml`) |
| `maximus memory` | REMOVED (diagnostic only, hidden) |
| `maximus hooks` | REMOVED (diagnostic only, hidden) |
| `maximus discover` | REMOVED from core, can be tool inside session |
| `maximus status` | Keep as `maximus doctor` (hidden diagnostic) |

---

## 7. Proposed CLI Surface

```
maximus                    # Start interactive session (DEFAULT)
maximus --model <name>    # Use specific model (optional)
maximus --verbose          # Show debug info (optional)
maximus --version          # Show version (optional)
maximus --help             # Show help (minimal)
maximus doctor             # Diagnostic check (hidden)
```

---

## 8. Out of Scope (v1.0)
- Web UI / GUI
- Multi-agent orchestration
- MCP server integration
- Package discovery (can be internal tool)
- Benchmarking tools

---

**END OF PRD**

Ready for Phase 2: Architecture Design