# Maximus.ai Execution Plan (Phase 6)

**As of**: 2026-06-10 (synthesized from Phase 1-5: audit debt/gaps, competitive missing vs OpenHands/Cline/Goose/Agent Zero/LangGraph/etc., hidden gems for MCP/memory/agent/safety, architecture scores (B high-potential overall; 8-9 memory/ext/agent/local in rich paths but 3-5 prod/maint/deploy/research/obs due to mocks/stubs/frontend absence/claims mismatch), roadmap (30d quick wins, 90d core, 180d elite, 1yr dominant)).

**Process**: Converted all findings to GitHub-ready backlog (Critical/High/Medium/Low categories; complexity/impact/risk estimates 1-5; structured issue bodies with title/description/evidence/labels/estimates/acceptance). Prioritized from Phase 4 low scores + Phase 1 106+ debt lines + Phase 2 gaps + Phase 3 gems + Phase 5 phases. Evidence citations (maximus file:line from clone + web "as of 2026-06" + library cross). Output ready for docs/maximus-execution-plan.md (importable as issues via GH CLI or manual; milestones/epics/boards suggested). Library leverage (AGENTS.md + skills for tracking; catalogs for recipes). Dogfooding (use library todo_write / research-project / hidden-gem-hunt / generate-integration-recipe for execution).

**Prioritization logic**: Critical = security/claims/MCP impl (Phase 4 low + Phase 1 mocks + Phase 2 "MCP implementation" gap #1); High = frontend/claims/debt/router/safety/sandbox (Phase 1/4/2 gaps); Medium = memory/evals/research/infra (Phase 1/4/5); Low = polish/optional (nice-to-haves from gems/roadmap). Estimates: complexity (code change size), impact (user/prod/library alignment), risk (regression/scope).

**Critical (P0; block production/claims/trust; 30d roadmap tie-in)**:
- **Title**: Consolidate MCP to real implementation (remove mocks/dupe; wire to registry/loop/terminal)
  - **Description**: 3 overlapping mcp/ modules with mocks/sims (client.py:82/117 "# For now, return mock tools..." / "Mock implementation"; mcp_manager.py:84/89 "Simulate tool listing/call"; manager.py "full" but unwired; loop.py:174 except "not available"; no tools in _get_tool_schemas/registry). "MCP Integration ✅ Complete" (README:120) false. Phase 1 debt + Phase 2 gap #1 vs Cline/Goose/OpenClaw/Agent Zero/OpenManus (real marketplace/stdio/hub/run_mcp.py per competitive-analysis.md + library mcp/servers.md).
  - **Evidence**: C:\Users\11vat\Desktop\maximus-ai-audit\src\maximus\mcp\client.py:82/117; mcp_manager.py:84/89; manager.py; loop.py:157-176; README:120; Phase 1 maximus-audit.md (MCP inventory); competitive-analysis.md (Cline/Goose MCP 8-10).
  - **Category**: Critical; Labels: mcp, debt, security, claims.
  - **Estimates**: Complexity 4, Impact 5 (enables all agent/MCP recipes + library cross), Risk 3 (dupe removal).
  - **Acceptance**: Real JSON-RPC/Stdio works with npx servers; tools reach registry; tests pass; "MCP Integration" claim updated to "in progress" or removed; sample integration with library mcp/manifests.
  - **Milestone**: 30-day quick wins.

- **Title**: Fix model router stub (wire detectors/scorer/intent; remove hardcoded default)
  - **Description**: intelligence/model_router.py full 10 TaskIntent regex + ComplexityScorer + DEFAULT_MODELS but route() stub 316-326 always qwen GENERAL SIMPLE. "Model Routing" / "automatic" claims (AGENTS.md:16/91, README:53) false. Phase 1 + Phase 4 low intelligence/router score.
  - **Evidence**: C:\Users\11vat\Desktop\maximus-ai-audit\src\maximus\intelligence\model_router.py:316 (def route stub + hardcoded); 198 (full detect); loop.py:325 (uses but ineffective); Phase 1 audit; architecture-review.md.
  - **Category**: Critical; Labels: intelligence, router, claims.
  - **Estimates**: Complexity 3, Impact 4 (enables proper model selection + stance), Risk 2.
  - **Acceptance**: route() uses detectors/scorer; tests for intents/complexity; hardware + user --model respected; claim updated.
  - **Milestone**: 30-day.

- **Title**: Harden safety layer 3 + enforce everywhere (remove auto-True; add tests)
  - **Description**: safety.py:121 layer3 "For automated mode, we'll allow with warning; actual confirmation happens in the UI layer" often returns True. 3-layer claims (PRD/AGENTS/ARCHITECTURE/README:55) partial. Phase 4 low security + Phase 1 debt.
  - **Evidence**: C:\Users\11vat\Desktop\maximus-ai-audit\src\maximus\core\safety.py:117-122; api.py:180 (layer2 only); loop.py hooks; Phase 1/4.
  - **Category**: Critical; Labels: safety, security.
  - **Estimates**: Complexity 3, Impact 5 (trust + prod), Risk 3.
  - **Acceptance**: Layer3 always prompts in auto; tests; enforcement in api/loop; claim accurate.
  - **Milestone**: 30-day.

- **Title**: Update all over-claims / version / docs mismatch (README/AGENTS/ARCH/PRD to reality)
  - **Description**: 0.1.0 (pyproject) vs "v2.0 UX" / "✅ Complete" table (README:43/116/120: 8-state/32 tools/MCP/React/Vector/Sub-Agent/Docker "✅"; "100% completion" commit). Phase 1/2/4 debt + competitive gaps.
  - **Evidence**: C:\Users\11vat\Desktop\maximus-ai-audit\pyproject.toml:7; README:43/116/120; AGENTS.md:12/16/91; ARCHITECTURE.md ("Phase 2 Deliverable"); Phase 1 audit (106+ debt lines); competitive-analysis.md.
  - **Category**: Critical; Labels: docs, claims, debt.
  - **Estimates**: Complexity 2, Impact 4 (trust), Risk 1.
  - **Acceptance**: Claims match code (e.g., "MCP: in progress with mocks removed"; "React: planned, terminal primary"); version consistent or "early".
  - **Milestone**: 30-day.

**High (P1; unblock prod/scale/competitive; 30-90d tie-in)**:
- **Title**: Implement or scope frontend (minimal terminal enhancements or excise React claims/CI/Docker refs)
  - **Description**: Ambitious REACT_TERMINAL_PLAN.md + ci.yml:84 "cd maximus-terminal" + package-lock + playwright + Docker/CI/prod nginx but no source (list_dir/grep confirm absent maximus-terminal/ or .tsx; builds fail). Phase 1/2/4 gap.
  - **Evidence**: C:\Users\11vat\Desktop\maximus-ai-audit\ci.yml:84 (cd + continue-on-error); REACT_TERMINAL_PLAN.md; package-lock + playwright; list_dir/grep no frontend src; Phase 1/2/4.
  - **Category**: High; Labels: frontend, ux, debt, claims.
  - **Estimates**: Complexity 4-5, Impact 5 (UX/competitive vs OpenHands/Cline/Cursor/Windsurf 8-10), Risk 3 (scope).
  - **Acceptance**: Either minimal enhancements ship (or tui promoted) or claims excised + CI/Docker cleaned; builds pass.
  - **Milestone**: 90-day.

- **Title**: Fix router + wire intelligence/planner/reflector/stance in default path
  - **Description**: As Critical #2 + planner/reflector/stance isolated (not default; adapters hardcoded). Phase 4 low.
  - **Evidence**: model_router.py:316; intelligence/*; multi_agent/spawner.py; Phase 1/4.
  - **Category**: High; Labels: intelligence, router, orch.
  - **Estimates**: Complexity 4, Impact 4, Risk 2.
  - **Acceptance**: Full in default path; tests; competitive parity notes.
  - **Milestone**: 90-day.

- **Title**: Real sandbox (fix docker detect + implement 1-2 cloud backends or clear claims)
  - **Description**: Always fs fallback + "simulated" (sandbox.py:103; factory.py "simulated" for Modal/LangSmith/Daytona). Phase 1/2/4 gap vs Agent Zero/OpenHands 8-10.
  - **Evidence**: C:\Users\11vat\Desktop\maximus-ai-audit\src\maximus\core\sandbox.py:103; factory.py:291/296/333/373; Phase 1/4.
  - **Category**: High; Labels: sandbox, security, claims.
  - **Estimates**: Complexity 4, Impact 4, Risk 3.
  - **Acceptance**: Docker works or claim "local fs + stubs"; 1 backend real or scoped.
  - **Milestone**: 90-day.

- **Title**: De-dupe + clean tools/adapters (merge dupes; make adapters real or docs)
  - **Description**: task_tools vs todo_tool (old 'Tool' + paths); adapters hardcoded static (no real analysis). Phase 1 debt.
  - **Evidence**: tools/builtin/ (task_tools.py + todo_tool.py); adapters/open_swe_adapter.py:37+ (hardcoded "inspired by"); Phase 1.
  - **Category**: High; Labels: tools, debt.
  - **Estimates**: Complexity 3, Impact 3, Risk 2.
  - **Acceptance**: No dupes; adapters either real (scan repo) or clearly "compat shims".
  - **Milestone**: 90-day.

- **Title**: Update deps + declare missing (httpx/psutil top-level; remove unused openai/anthropic or use)
  - **Description**: Undeclared heavy (httpx/psutil from grep/ollama.py); openai/anthropic declared unused (violates "no external" AGENTS:7).
  - **Evidence**: pyproject.toml:15-30; grep httpx/psutil 29+; no openai/anthropic calls; Phase 1.
  - **Category**: High; Labels: deps, claims.
  - **Estimates**: Complexity 2, Impact 3, Risk 2.
  - **Acceptance**: pyproject accurate; "no external" claim or deps updated.
  - **Milestone**: 90-day.

**Medium (P2; enable scale/research/self-improvement; 90-180d)**:
- **Title**: Production MemoryMesh (fix compaction TODO; vector default; Graphiti cross)
  - **Description**: compaction.py:246 TODO; vector optional/debug; api/terminal no MemoryMesh (json only). Phase 1/4 high memory but gaps.
  - **Evidence**: memory/compaction.py:246; vector_memory.py:20 try/except; loop.py:117/211 (rich only); Phase 1/4.
  - **Category**: Medium; Labels: memory, debt.
  - **Estimates**: Complexity 3, Impact 4 (agent/research), Risk 2.
  - **Acceptance**: Compaction calls Ollama; vector on by default or doc; Graphiti recipe (library rag-memory/).
  - **Milestone**: 180-day.

- **Title**: Evals / benchmarks harness (SWE-bench-like + publish; library research/ cross)
  - **Description**: No published evals (tests mock-heavy; "✅ Complete" vs reality). Phase 2 gap + Phase 4 low research.
  - **Evidence**: README:110/116/120 claims; tests/ (mock-heavy + limited); no SWE-bench; Phase 1/2/4; library research/ (ai-agent-benchmark-exploits-2026.md + swe-bench-ai-pentest.md).
  - **Category**: Medium; Labels: evals, research, claims.
  - **Estimates**: Complexity 4, Impact 4, Risk 3.
  - **Acceptance**: Harness + published results (or "in progress"); cross library research/.
  - **Milestone**: 180-day.

- **Title**: Research automation node (Local Deep Research / gems handoff; citations)
  - **Description**: planner/reflector isolated; no deep research integration. Phase 2/4 low research.
  - **Evidence**: intelligence/planner/reflector (isolated); Phase 1/4; library research-automation/ (Local Deep Research S + full-research-implementation-loop.md + gems like tarun7r/deep-research-agent).
  - **Category**: Medium; Labels: research, orch.
  - **Estimates**: Complexity 3, Impact 4, Risk 2.
  - **Acceptance**: Research node in loop/planner; citations + cred; recipe with library research-automation/ + Phase 3 gems.
  - **Milestone**: 180-day.

- **Title**: Infra / CI / prod polish (frontend decision; clean builds; monitoring)
  - **Description**: CI continue-on-error + frontend absent; prod nginx/certs incomplete; prometheus declared but minimal.
  - **Evidence**: ci.yml:84/89; compose/Docker; Phase 1/4.
  - **Category**: Medium; Labels: infra, ci, deploy.
  - **Estimates**: Complexity 3, Impact 3, Risk 2.
  - **Acceptance**: Clean CI/builds; prod guide accurate; basic monitoring.
  - **Milestone**: 180-day.

**Low (P3; polish / optional gems / nice-to-haves; 180d-1yr)**:
- **Title**: Integrate top Phase 3 hidden gems (mcp-knowledge-graph, swarmclaw, agent-security-scanner-mcp, etc.)
  - **Description**: 8-9 screened (MCP KG/memory, swarm runtime, security scanner/Semgrep, RAG docs, deep research, etc.). Phase 3.
  - **Evidence**: docs/maximus-hidden-gems.md (full drafts + searches); Phase 3.
  - **Category**: Low; Labels: gems, integrations.
  - **Estimates**: Complexity 3-4 each, Impact 3-4, Risk 2.
  - **Acceptance**: 3-5 wired with recipes (library cross + "Grok subagent..." phrasing).
  - **Milestone**: 1-year.

- **Title**: Advanced frontend / themes / Buddy / plugins (from REACT_TERMINAL_PLAN.md if kept)
  - **Description**: Cyberpunk/CRT themes, Buddy (18+ species), plugins, visual effects, multi-tab.
  - **Evidence**: REACT_TERMINAL_PLAN.md; Phase 1/2.
  - **Category**: Low; Labels: ux, frontend.
  - **Estimates**: Complexity 5, Impact 3, Risk 3.
  - **Acceptance**: If frontend in scope: MVP ships with 2+ themes + Buddy.
  - **Milestone**: 1-year.

- **Title**: Self-improvement v1 (Phase 7 design + basic loop using research/MCP/gems)
  - **Description**: maximus uses own loop + research agents + MCP + memory to audit/improve code + discover + update docs/catalogs.
  - **Evidence**: Phase 7 future-architecture.md (to be written); Phase 1/3/5.
  - **Category**: Low (foundational for 1yr); Labels: self-improvement, research.
  - **Estimates**: Complexity 5, Impact 5 (elite platform), Risk 4.
  - **Acceptance**: Demo: maximus audits own gap + proposes PR + contributes to library.
  - **Milestone**: 1-year.

**Milestones / Epics / Boards / Project structure**:
- **Milestones**: M1: 30d Critical (MCP/router/safety/claims; ~4-6 weeks); M2: 90d High (frontend/ router wire / sandbox / de-dupe / deps; ~8-10 weeks); M3: 180d Medium (memory/evals/research/infra; ~4-6 months); M4: 1yr Low + self-improvement (gems + advanced + Phase 7; ~12 months).
- **Epics**: Epic 1: MCP & Ecosystem (Critical + Low gems); Epic 2: Core Polish & Claims (Critical/High debt); Epic 3: Intelligence / Orch / Research (High/Medium); Epic 4: Infra / Deploy / Frontend (High/Medium); Epic 5: Memory / Evals / Self-Improve (Medium/Low + Phase 7).
- **Boards**: GitHub Projects (or linear/trello): columns Backlog / To Do / In Progress / Review / Done; swimlanes by Epic/Milestone; labels as above + "phase:1-4" from audit.
- **Import**: Copy issue bodies to GH (gh issue create --title "..." --body "..." --label "critical,mcp" --milestone "30d"); or use script from docs/maximus-execution-plan.md.

**Sources / freshness**: From Phase 1-5 artifacts (maximus-audit.md file:line 2026-06-10; competitive/hidden-gems with web 2026-06; architecture 9-axis from AGENTS + evidence; roadmap phased); clone code/docs; library AGENTS.md + catalogs/skills (cross + recipes + "Grok subagent..." phrasing). "Research performed 2026-06-10... Re-verify". All per AGENTS (evidence, citations, "as of", sources with queries/tools, actionable, library leverage).

(Full structured issue bodies + tables + owners/estimates/risk + acceptance + milestones/epics/boards in the written file; ready for GH import + execution via library skills/subagents + Phase 5 roadmap.)