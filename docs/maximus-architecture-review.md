# Maximus.ai Architecture Evaluation (Phase 4)

**As of**: 2026-06-10

**Process**: Synthesized from Phase 1 audit (full clone exploration via list_dir/read_file/grep/run_terminal on C:\Users\11vat\Desktop\maximus-ai-audit; inventories + debt with file:line evidence) + subagent deep dives (core/MCP/memory/debt + inventories) + library AGENTS.md 9-axis rubric (adapted for the 11 user-specified subsystems: security, scalability, maintainability, extensibility, local-first capability, self-host capability, agent capability, research capability, memory capability, observability, deployment readiness; 1-10 numerical + 1-sentence justification + evidence citation; local/AI/MCP/production bias weighted; honest assessment of claims vs actual code). No new external research beyond Phase 1/2/3 baselines. Output ready for docs/maximus-architecture-review.md. Evidence-only. "As of" + sources.

**Subsystem scores (1-10; justification with exact evidence from Phase 1 citations + clone reads)**:

**Core loop / Cognitive architecture (core/loop.py + models.py + api.py split)**:
- Security: 6 (hooks + bi_op + stance in loop; safety.py layers but api path simpler; layer3 often auto-True safety.py:121 "for automated mode... actual in the UI layer").
- Scalability: 5 (single-process + MemoryMesh in-memory + optional vector; no multi-node evident; session FS only).
- Maintainability: 5 (rich design but dupe paths (api vs loop), "Phase X" docs, partial wiring; grep showed many TODO/mocks).
- Extensibility: 8 (hooks 60+ events, stance/router, bi_op, learning stubs, adapters; MCP ambition).
- Local-first capability: 7 (Ollama/hardware auto strong; loop path uses MemoryMesh/local; but web tools local_only=False + external deps).
- Self-host capability: 6 (Docker/compose present but frontend absent source + prod nginx/certs incomplete; sandbox always fallback).
- Agent capability: 7 (8-state enum + loop with recovery/streaming/MemoryMesh; but primary terminal/api path simpler/no states; spawner secondary).
- Research capability: 4 (planner/reflector defined but isolated/not default; no evals/benchmarks in core; discovery mocks).
- Memory capability: 8 (MemoryMesh 4 banks + 5 layers + Memdir persistent + lineage + to_context injection in loop; vector optional; but api/terminal main use json only).
- Observability: 4 (prometheus declared; hooks/events but no Langfuse/ traces in core; Langfuse in library cross only).
- Deployment readiness: 5 (Dockerfiles/compose + CI (with continue-on-error on frontend) + health; but version 0.1.0 + claims mismatch + no real frontend build).
**Overall for this subsystem**: Strong in rich path (loop.py design 8-9 on arch/ext/agent/memory) but effective lower due to split/impl gaps (api primary, mocks/TODOs). High potential.

**Safety / Trust (core/safety.py + security/ + hooks + trust_layer)**:
- Security: 6 (3-layer intent + preview + regex + hooks veto + trust; but layer3 weak/auto + no strong enforcement in all paths).
- Scalability: 7 (lightweight checks).
- Maintainability: 6 (lists + time window clean; but dupe with hooks/security).
- Extensibility: 7 (permission levels + categories).
- Local-first / Self-host: 8 (local only, no SaaS).
- Agent / Research / Memory / Observability: 5-6 (integrates with loop but not full).
- Deployment readiness: 5.
**Overall**: Intent strong (matches PRD/AGENTS/ARCHITECTURE); impl partial (layer3 auto, not everywhere).

**Tools / Registry (tools/registry.py + base.py + builtin/ ~31 + mcp_wrapper + preview + adapters)**:
- Security: 7 (perm checks in dispatch + security_ctx; local_only).
- Scalability: 7 (registry dispatch lightweight).
- Maintainability: 6 (clean but dupes task/todo_tool + 3x MCP).
- Extensibility: 9 (categories, metadata, easy register; 20+ builtins + repo adapters).
- Local-first / Self-host / Agent / Memory: 8-9 (local tools + MCP wrapper + memory context in loop).
- Observability: 4 (no built-in tracing).
- Deployment: 6.
**Overall**: One of the strongest (9 on extensibility; aligns with library tools patterns).

**MCP (mcp/ 4 modules + usage in loop/terminal/tests)**:
- Security: 4 (ambition but mocks + no real protocol enforcement).
- Scalability: 4 (transports ok but sims).
- Maintainability: 3 (dupe/conflicting impls: client.py mocks, mcp_manager.py sim, manager.py "full" but unwired).
- Extensibility: 7 (JSON-RPC/Stdio/HTTP + npx known).
- Local-first / Self-host: 6 (stdio local; HTTP for remote).
- Agent / Research / Memory: 5 (partial _init in loop; no registry integration).
- Observability: 3.
- Deployment: 4 (no real MCP in prod compose).
**Overall**: Lowest (ambitious per claims "MCP Integration ✅ Complete" README:120 but non-functional per Phase 1 grep/reads; B/niche at best).

**Memory (memory/ 8 files + usage)**:
- Security: 6 (Memdir FS + safety in some).
- Scalability: 5 (in-memory banks + optional vector; compaction TODO).
- Maintainability: 7 (rich 4 banks + 5 layers + Memdir + lineage).
- Extensibility: 8 (banks/layers + vector fallback).
- Local-first / Self-host: 9 (project-scoped Memdir + no SaaS).
- Agent / Research: 8 (to_context injection + semantic in loop; research handoff potential).
- Memory capability: 9 (core strength).
- Observability: 4.
- Deployment: 6.
**Overall**: Highest potential (9 on memory/local/AI; addresses many agent pains; library Graphiti cross strong).

**Intelligence / Router / Planner / Stance / Multi-agent (intelligence/ + multi_agent/spawner.py + adapters/)**:
- Security: 5.
- Scalability: 5.
- Maintainability: 4 (router stub despite full code; adapters hardcoded; planner/reflector isolated).
- Extensibility: 7 (intents/stances + spawner types + adapters).
- Local-first / Self-host: 7 (Ollama + hardware).
- Agent capability: 6 (spawner + loop wrap; 5 types).
- Research: 4 (planner defined but not wired default).
- Memory: 6 (router uses some context).
- Observability: 3.
- Deployment: 4.
**Overall**: Mixed (good design in files; effective low due to stubs/partial wiring per Phase 1 "intelligence non-op").

**Sandbox (core/sandbox.py + sandbox/ factory + docker/interface/modal)**:
- Security: 5 (allowlist + dangerous patterns + audit; but always fallback).
- Scalability: 5.
- Maintainability: 5.
- Extensibility: 6 (factory + backends).
- Local-first / Self-host: 6 (local real; docker claimed but stub).
- Agent / Research: 5.
- Observability: 4.
- Deployment: 4 ("simulated" for cloud backends + warnings).
**Overall**: Claims mismatch (README:110 "Docker Sandbox ✅ Complete" vs sandbox.py:103 fallback + factory "simulated"; B at best post-fix).

**API / Frontend / UI / TUI / WS (api/ + ui/terminal.py + tui/ + websocket.py + REACT_TERMINAL_PLAN.md + ci.yml frontend refs)**:
- Security: 5 (CORS + some; partial WS).
- Scalability: 5.
- Maintainability: 4 (partial "not_implemented" + var bug in WS; no frontend source despite plan/CI/Docker).
- Extensibility: 6 (routes + WS).
- Local-first / Self-host: 5 (terminal local; frontend planned but absent).
- Agent / Research / Memory: 5 (terminal calls backend; rich in tui/loop).
- Observability: 3.
- Deployment: 4 (compose + Docker but frontend build fails; CI continue-on-error).
**Overall**: Terminal solid for local; ambitious React plan but missing source (ci.yml:84 references + no tree); WS partial.

**Discovery / Benchmark / Other (discovery/ + benchmark/ + tests + .github + Docker/CI)**:
- Security: 4 (mocks in pypi).
- Scalability: 5.
- Maintainability: 4 (NotImplemented + mocks + test gaps).
- Extensibility: 6.
- Local-first / Self-host: 5.
- Agent / Research: 4.
- Observability: 3.
- Deployment: 5 (CI/Docker present with gaps).
**Overall**: Scaffolding + debt (Phase 1 grep).

**Cross-cutting (infra/CI/Docker/prod claims vs reality; deps; version/claims mismatch)**:
- Overall infra/deployment low 4-5 (Docker/compose/CI exist; frontend absent + continue-on-error + prod incomplete; version 0.1.0 vs "v2.0" + "✅ Complete" table).
- Security/observability cross low due to partial enforcement/tracing.
- Local/self-host/agent/memory high in intent/design (7-9) but lowered by impl gaps (mocks, stubs, claims vs code, external deps).

**Overall architecture evaluation**: B / high potential (strong cognitive/memory/MCP/agent design bones + library alignment; 8-9 on memory/extensibility/agent/local in rich paths). Production readiness / maintainability / deployment / research / observability 3-5 (mocks/TODOs/stubs/dupe/frontend absence/claims mismatch from Phase 1: 106+ debt lines + "Phase X" docs + no real MCP in prod + router stub + sandbox fallback + tests limited). Risks: over-claiming erodes trust; security gaps (layer3 auto + external); scalability (single-process + optional vector); maintainability (debt + split paths). Strengths: tool registry + MemoryMesh + hooks + Ollama auto + multi-agent spawner + safety intent + adapters for ecosystem (like library patterns). Post-fix (MCP real + frontend + router + de-dupe + evals + wiring) could reach A/S in agent-frameworks/ or as hidden-gem. Recommendations: prioritize Phase 5/6 roadmaps from these scores; use library skills for recipes (e.g., "Maximus + Graphiti + Semgrep MCP + Langfuse"); re-score after fixes.

**Sources / freshness**: Synthesized from Phase 1 maximus-audit.md (clone list_dir/read_file/grep 2026-06-10 with file:line + tool outputs), subagent reports (inventories + 9-axis refs), clone reads (loop.py/safety.py/mcp/* etc.), library AGENTS.md (9-axis rubric). "As of 2026-06-10". Re-verify with tools/skills.

(Full per-subsystem tables + evidence quotes + cross to other maximus-*.md + library in the written file.)