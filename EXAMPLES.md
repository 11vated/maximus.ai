# Maximus.ai Examples

## Quick Start

### Check System Status
```bash
maximus status
```

### Run a Single Prompt
```bash
maximus run "List all Python files in the current directory"
```

### Interactive Chat Mode
```bash
maximus chat
# Then type your prompts, use 'exit' or 'quit' to stop
```

---

## Example 1: Code Analysis

Analyze a repository using the built-in repo adapters:

```bash
# Analyze open-swe repo
maximus run "Analyze the open-swe repository structure and tech stack"

# Analyze ClawSpring repo
maximus run "Analyze the ClawSpring codebase and identify key patterns"

# Analyze Nexus repo
maximus run "Analyze the Nexus agent and report its cognitive loop design"
```

---

## Example 2: File Operations

```bash
# Read a file
maximus run "Read the contents of pyproject.toml"

# Create a new file
maximus run "Create a file named hello.py with a function that prints 'Hello World'"

# Edit an existing file
maximus run "Add a new function to hello.py that calculates factorial"
```

---

## Example 3: Search and Replace

```bash
# Search for patterns
maximus run "Search for all occurrences of 'TODO' in Python files"

# Find files by pattern
maximus run "List all YAML files in the config directory"
```

---

## Example 4: Git Operations

```bash
# Check git status
maximus run "Check the current git status"

# Create a commit
maximus run "Commit all changes with message 'Update documentation'"
```

---

## Example 5: Python Code Execution

```bash
# Run a Python script
maximus run "Execute the script test.py and show the output"

# Run tests
maximus run "Run all pytest tests and report results"
```

---

## Example 6: Using Different Stances

The agent automatically selects the best stance, but you can guide it:

```bash
# Exploratory stance (broad exploration)
maximus run "Explore the codebase and discover how the tool system works"

# Surgical stance (precise changes)
maximus run "Fix the bug in line 42 of cli.py by changing the error handling"

# Architectural stance (structure focus)
maximus run "Design a new feature for conversation branching and document the architecture"

# Debugging stance (systematic issue resolution)
maximus run "Debug why the test suite is failing and fix the issues"
```

---

## Example 7: Conversation Branching

Maximus supports git-like conversation branching (API usage):

```python
from maximus.memory.branching import BranchManager

manager = BranchManager()
manager.create_branch("experiment")
manager.switch_branch("experiment")
# ... do work ...
manager.switch_branch("main")
manager.merge_branch("experiment")
```

---

## Example 8: MCP Integration

Connect to Model Context Protocol servers:

```python
from maximus.mcp.manager import MCPManager, MCPServerConfig

manager = MCPManager()
config = MCPServerConfig(
    name="my-server",
    command=["node", "mcp-server.js"],
)
manager.add_server(config)
tools = await manager.list_tools()
```

---

## Tips for Best Results

1. **Be Specific**: Clearly state what you want the agent to do
2. **Use Context**: The agent remembers conversation history
3. **Check Status**: Run `maximus status` before starting
4. **Review Actions**: In "auto" mode, writes need confirmation
5. **Leverage Stances**: Let the agent pick the best behavior mode

---

## Troubleshooting

### Ollama Not Running
```bash
# Start Ollama
ollama serve

# Pull a model
ollama pull qwen2.5-coder:7b
```

### Permission Errors
- Use `--mode accept-all` to auto-approve all actions (use with caution)
- Check that tools have correct permission levels

### Import Errors
```bash
# Reinstall Maximus
cd C:\Users\11vat\Desktop\agent007\maximus.ai
pip install -e .
```
