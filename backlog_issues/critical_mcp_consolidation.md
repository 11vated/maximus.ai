# Consolidate MCP to real implementation (remove mocks/dupe; wire to registry/loop/terminal)

**Backlog Category**: Critical
**Labels**: mcp, debt, security, claims
**Estimates**: Complexity 4, Impact 5, Risk 3
**Milestone**: 30-day quick wins

**Description** (from execution plan):
3 overlapping mcp/ modules with mocks/sims (client.py:82/117 ...). "MCP Integration ✅ Complete" (README:120) false.

**Changes made**:
- manager.py: added global get_mcp_manager
- mcp/__init__.py: unified exports to full real manager
- mcp_manager.py: overwritten to delegate (mocks removed)
- client.py: overwritten to delegate (mocks removed)
- connector.py: updated to use real manager and transports
- loop.py: import and _init_mcp_tools and _get_tool_schemas updated to use real and include MCP tools in schemas

**Acceptance**: Real JSON-RPC/Stdio works; tools reach registry; tests pass; claim updated.

See docs/maximus-execution-plan.md for full.
