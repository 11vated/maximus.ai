# Maximus.ai Backlog Item (Medium)

**Title**: Start evals / benchmarks harness (basic loop/KG/MCP cycle tests + SWE-bench subset)

**Description**: Add initial deterministic harness for agent states, tool execution, memory/KG, safety, MCP integration. Include simple eval cases for routing, KG ingest, sandbox. Cross to library research/ benchmarks. Publish "in progress".

**Evidence**: tests/ currently mock-heavy; new KG/MCP integration needs coverage; Phase 2/4 low research; library research/ (ai-agent-benchmark-exploits-2026.md + swe-bench-ai-pentest.md).

**Category**: Medium; Labels: evals, research, harness, claims.

**Estimates**: Complexity 3, Impact 4, Risk 2.

**Acceptance**: At least 3-5 basic eval tests passing (loop turns, KG add/query, MCP tool, safety veto); documented as "harness started".

**Milestone**: 180-day.

**Backlog ref**: From maximus-execution-plan.md (Medium P2) + Phase D / harness items.
