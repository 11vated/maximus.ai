# Maximus.ai Backlog Item (High)

**Title**: Clean remaining deprecation / async warnings + small polish

**Description**: Address remaining RuntimeWarnings (MCP list_tools) and deprecations (pydantic utcnow, etc.) in core paths. Ensure clean test runs and logs.

**Evidence**: pytest output shows lingering coroutine and deprecation warnings in mcp_wrapper, scheduler, etc.

**Category**: High; Labels: polish, claims, maint.

**Estimates**: Complexity 2, Impact 2, Risk 1.

**Acceptance**: pytest runs with fewer/no new warnings in core; logs clean for agent cycles.

**Milestone**: 90-day.

**Backlog ref**: From execution-plan + Phase C observable.
