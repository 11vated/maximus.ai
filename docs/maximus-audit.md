# Maximus.ai Repository Intelligence Audit (Phase 1)

**As of**: 2026-06-10 (clone snapshot from C:\Users\11vat\Desktop\maximus-ai-audit; last git commit in clone: 2026-05-08)

**Process**: Followed library `.grok/skills/library-status/SKILL.md` (structure exploration via list_dir/grep/read_file/run_terminal on absolute clone paths; coverage/freshness/gaps/risks/strengths/next actions in scannable format) + `AGENTS.md` standards (evidence-only with file:line + tool output citations; "as of" dates; 9-axis lens adapted for subsystems with local-first/AI/MCP/production weighting; multi-hop where applicable via code + docs; no unsubstantiated claims). Leveraged library catalogs lightly for context (e.g., ollama patterns). Subagents used for parallel deep dives (core/MCP/memory/debt + full inventories). All findings cross-referenced from direct tool outputs (list_dir on root/src, 30+ read_file on docs/src files, 15+ targeted grep, run_terminal for metrics/CI/compose).

**Scope note**: Focused exclusively on the provided clone (no remote GitHub API beyond clone metadata). Primary UX path (bin/maximus.py → ui/terminal.py → core/api.py) vs. rich "cognitive" code (core/loop.py + memory/intelligence/mcp) analyzed separately. Claims in README/ARCHITECTURE/PRD/AGENTS.md ("✅ Complete", "v2.0 UX", "100% local") audited against actual implementation.

## Full Repository Map
- **Root**: AGENTS.md (agent guide for "Maximus"), ARCHITECTURE.md (Phase 2 design doc with diagrams + pseudocode), PRD.md (Phase 1 vision + FRs), DEPLOYMENT.md (prod Docker guide), EXAMPLES.md, CONTRIBUTING.md, REACT_TERMINAL_PLAN.md (detailed ambitious React UI spec), README.md (marketing + status table), pyproject.toml (0.1.0, hatch, deps), bin/maximus.py (thin entry), docker-compose*.yml + Dockerfiles (backend/frontend/ollama/nginx), .github/workflows/ci.yml (lint/test/docker + frontend in "maximus-terminal/" — absent from tree), playwright.config.js, nginx.conf, package-lock.json (frontend hints only), hello.py + various root test_*.py, tests/ (unit/integration/e2e/mcp/sandbox/discovery with mocks/conftest), .kilo/plans/ (1 example), docs/ (empty post-audit mkdir).
- **src/maximus/** (95 .py files):
  - Core engine: core/ (loop.py ~787 lines AgentLoop with 8-state/MemoryMesh/router/stance/hooks/bi_op/learning; safety.py 3-layer; api.py MaximusBackend + Session; session_manager.py; actions/evolution/bi_operation/sandbox).
  - Tools: tools/ (registry.py + base.py + builtin/ ~20-31 tools incl. file/git/web/exec/python-runner/browser/test-runner/todo + mcp_wrapper/preview + adapters registration).
  - Memory: memory/ (memory_mesh.py 4 banks + 5 layers + Memdir persistent .maximus/memdir; vector_memory.py optional chroma; short/long/branching/compaction/session_sync).
  - MCP: mcp/ (client.py/connector.py/manager.py/mcp_manager.py — 3 overlapping impls, heavy simulation/mocks).
  - Intelligence: intelligence/ (model_router.py full detector/scorer + stub route; planner.py; reflector.py; stance.py).
  - Multi-agent: multi_agent/ (spawner.py 5 types + wrap AgentLoop).
  - Adapters: adapters/ (hardcoded Analyze*Tool + *Adapter for clawspring/nexus/open-swe; registered as tools).
  - Sandbox: sandbox/ (factory + docker/local + modal/langsmith/daytona stubs "simulated").
  - UI/API: ui/terminal.py (primary chat loop, MCP cmds, sandbox); tui/app.py (uses loop); api/ (FastAPI routes/websocket — partial "not_implemented").
  - Other: discovery/ (pypi mocks + NotImplemented package install), chat/, middleware/ (6 layers base), utils/ (llm.py OllamaClient + httpx; ollama.py hardware detect + ensure), hooks.py (60+ events), models.py (CognitiveState 8-val enum, Stance, ToolMetadata etc.), security/ + security.py.
- **Tests**: 16+ .py (heavy mocks; e2e/integration often skipped; unit on tools/models; mcp/sandbox specific).
- **No frontend source**: Despite CI/Docker/plan/nginx references to "maximus-terminal/" (npm build/test), only package-lock + playwright at root. Grep confirmed no React/TSX/Vite source.

**Architecture diagram (text/Mermaid from ARCHITECTURE.md + code synthesis)**:
```
User Input (bin/maximus.py or python -m)
  ↓
Terminal UI (ui/terminal.py — primary; MCP/sanbox cmds; calls backend)
  ↓
Backend API (core/api.py: MaximusBackend.process_message → LLMClient + registry dispatch + safety layer2)
  OR (secondary/rich path)
AgentLoop (core/loop.py: 8-state INIT→PLAN→ACT→... + MemoryMesh + router + hooks + bi_op + stance + _mcp_init)
  ↓ (shared)
Tools (registry + builtin ~31 + mcp_wrapper) | Memory (MemoryMesh 4 banks + Memdir) | MCP (fragmented) | Intelligence (stub router + planner) | Adapters (hardcoded) | Sandbox (fs + stubs)
  ↓
Ollama (httpx /api/chat + hardware detect) | Optional external (web npx docker)
```
(See full ARCHITECTURE.md for pseudocode diagrams + "Phase 2 Deliverable" note.)

## Technology Stack Inventory
- **Language/Runtime**: Python >=3.11 (pyproject.toml:9); asyncio/pydantic/rich/click/fastapi/uvicorn/httpx/subprocess dominant (grep hits 29+ for httpx alone, undeclared in some cases).
- **Build/Pkg**: hatchling (pyproject:3-4); scripts: maximus=ui.terminal:main, maximus-tui=tui.app:main.
- **LLM**: Ollama primary (utils/ollama.py + llm.py OllamaClient streaming /api/chat + /api/tags; aliases 7b/14b/fast/smart/think → qwen/deepseek/phi); hardware auto-detect (psutil + wmic/sysctl/systeminfo + nvidia-smi fallbacks); openai/anthropic declared but unused (grep no imports/calls).
- **Web/API**: FastAPI (api/__init__.py:28 app + lifespan + CORS + /health + routers); uvicorn; aiohttp; websocket (partial in api/websocket.py); httpx everywhere for Ollama/MCP/HTTP transport.
- **Tools/Exec**: ~31 registered (tools/builtin/__init__.py full register + 20+ files: file_ops/read/write/edit/ls/grep/glob, execute_shell/python_runner/node_runner, git_tools, web_search/fetch (local_only=False), browser_tool, test_runner, todo/task (dupe impls), system/scheduler); mcp_wrapper; preview.
- **Memory**: In-house MemoryMesh (4 banks: episodic/semantic/procedural/working + 5 KnowledgeLayers + lineage + Memdir FS .maximus/memdir/MEMORY.md + topics); optional vector (chromadb or keyword fallback); compaction (TODO); branching/session_sync.
- **MCP**: Ambitious but fragmented (4 modules: stdio/HTTP/JSON-RPC in manager.py; dataclass/sim in mcp_manager.py + client.py; transports real-looking but tools populated via mocks/sims; npx @modelcontextprotocol/* known servers).
- **Multi-agent/Intelligence**: AgentSpawner (5 types + wrap loop); ModelRouter (10 intents + complexity + DEFAULT_MODELS but route() stub always qwen); Planner/Reflector/StanceManager (defined + partial wiring in loop).
- **Sandbox/Security**: Local fs + allowlist + dangerous patterns + audit (core/sandbox.py); factory with real Local + "simulated" Modal/LangSmith/Daytona (warnings + MODAL_AVAILABLE guard); 3-layer SafetyController (preview time window + regex + auto-True layer3 in auto mode); permission/trust levels; hooks (60+ PRE/POST events).
- **UI**: Terminal (prompt_toolkit/textual hints; primary path); tui/ (app.py); ambitious React plan (Xterm.js + Zustand + Framer + themes + Buddy + plugins + state viz) but no source (only plan + package-lock + playwright + Docker/CI references).
- **Testing/Quality**: pytest + asyncio (pyproject + tests/conftest); ruff/mypy (pyproject + CI); playwright e2e (config + CI).
- **Infra/Deploy**: Docker (multi-stage backend/frontend; ollama image); compose (ollama health + backend + frontend + nginx in prod); .github CI (lint/test/docker + frontend continue-on-error); volumes for ollama/sessions; healthchecks.
- **Other**: prometheus (metrics); pygments; tenacity; pyyaml; discovery (pypi mocks + NotImplemented); hooks for extensibility; bi-op/evolution/learning stubs.

**Evidence**: pyproject.toml full read; grep "import httpx|from fastapi|ollama|chromadb|modal|psutil" (29+); tools/builtin/__init__.py:48+ full register list; memory_mesh.py + vector_memory.py reads; mcp/* full; loop.py + api.py; ollama.py:102-203 (detect); ci.yml + compose full reads; list_dir src/maximus.

## Dependency Inventory
- **Core (pyproject.toml:15-30)**: pydantic + settings, rich, click, tenacity, pyyaml, python-dotenv, openai, anthropic, fastapi, uvicorn, aiohttp, prometheus-client, pygments.
- **Optional**: textual (tui), chromadb + duckduckgo-search (vector).
- **Actual/undeclared (grep + runtime traces)**: httpx (pervasive: ollama/llm/web/mcp/discovery/tests — not top-level), psutil (ollama RAM), subprocess (many), re (patterns), json/datetime/typing (stdlib), pathlib.
- **External in tools**: npx (MCP), docker (sandbox), git/python/node runners, web (search/fetch), browser (playwright?).
- **Unused declared**: openai/anthropic (no calls/imports despite LLMClient compat).
- **Test/CI**: pytest/pytest-asyncio/httpx (CI + pyproject), ruff, mypy, hatchling, tree, node/npm (frontend CI).
- **Gaps**: Missing explicit httpx/psutil in [project.dependencies]; version pins loose; no lockfile committed (only package-lock for frontend hints).

**Evidence**: "read_file pyproject.toml:15-36"; "grep result (multiple): httpx in ollama.py:36, llm.py:9, ... 29+"; "read_file ollama.py:102: try: import psutil".

## Runtime Inventory
- **Primary entry**: `python bin/maximus.py` (or `python -m maximus`); thin wrapper → ui/terminal (interactive chat, --model, --verbose, doctor, MCP cmds like "mcp add/list/discover", sandbox cmds).
- **Backend paths**:
  - Default (terminal): core/api.py MaximusBackend (process_message → LLMClient/OllamaClient streaming + registry dispatch + safety layer2; SessionManager disk JSON ~/.local/share/maximus/sessions; simple loop no 8-state).
  - Rich (tui + multi_agent + loop init): core/loop.py AgentLoop (full 8-state + MemoryMesh injection + router + stance + hooks + bi_op + learning + _mcp_init + TOOL_START custom extract or OpenAI tools; run_async generator).
- **LLM**: Ollama (ensure + serve if needed; /api/chat streaming + tools; hardware select default qwen2.5-coder:7b fallback; aliases).
- **Tools**: 31+ registered (file/git/exec/web/browser/test/todo + mcp_wrapper); dispatch with perm/local checks.
- **MCP**: Configured but non-functional (mocks/sims in 3 impls; no real tools populated into registry; npx support).
- **Memory**: MemoryMesh (episodic recent + semantic facts + procedural patterns + working goal/plan/temp + Memdir FS persistent); vector optional; used heavily only in loop path.
- **Sandbox**: Local fs + allowlist + audit (docker detect always falls back).
- **Other runtime**: FastAPI (if /api used); hooks (PRE/POST events); security classifier; partial WS.
- **Hardware**: Auto RAM/VRAM/GPU/Apple/Win fallbacks (psutil + wmic/sysinfo/nvidia-smi).

**Evidence**: "read_file bin/maximus.py + ui/terminal.py:172 (init_backend)"; "read_file core/api.py:140+ (process_message + _execute_tool_safely)"; "read_file core/loop.py:292- (run_async + _init_mcp + MemoryMesh)"; "read_file utils/ollama.py:57- (ensure + detect full)"; "grep local_only=False" (web tools).

## Infrastructure Inventory
- **Docker**: Dockerfile.backend (python slim, pip -e, nonroot, CMD api, /health); .frontend (node build + nginx:alpine + nginx.conf); compose (ollama + backend + frontend; prod adds nginx + certs + sessions vol + health).
- **CI (.github/workflows/ci.yml full)**: lint (ruff/mypy on src/tests); test-python (unit + tools + adapters + spawner; install -e + deps); test-integration (some skipped); test-frontend (maximus-terminal npm ci/lint/build/test — continue-on-error); docker (build backend/frontend).
- **Other**: .env.example; .gitignore; playwright (e2e config + tests/e2e); nginx (proxy); volumes (ollama_data, sessions); healthchecks; nonroot user; resource notes in DEPLOYMENT (8-32GB RAM, GPU recs).
- **Frontend hints**: package-lock + playwright + Docker/CI/REACT_TERMINAL_PLAN (Xterm + Zustand + themes + Buddy + plugins) but **no source tree** (maximus-terminal/ absent; builds would fail).

**Evidence**: "read_file ci.yml:1-120 (full jobs + cd maximus-terminal:89)"; "read_file docker-compose.yml + .prod.yml (ollama health + services)"; "read_file Dockerfile.backend + .frontend"; "list_dir + grep: no maximus-terminal/ or .tsx source".

## MCP Inventory
- **Impls** (4 modules, overlapping/dupe):
  - mcp/client.py + connector.py: MCPClient (url parse, _list_tools mock dict per scheme, call_tool mock); add_server/list_available/auto_discover (hardcoded npx + keyword).
  - mcp_manager.py: MCPServer/MCPTool/MCPClient (start subprocess npx @modelcontextprotocol/*; _simulate init/list/call; auto_discover; global get_mcp_manager).
  - manager.py: "Full" (JSONRPCRequest/Response, StdioTransport (subprocess PIPE json), HTTPTransport (httpx), initialize/tools/list/call_tool/get_prompts/resources; real protocol structure).
- **Wiring/Usage**: loop.py partial _init_mcp_tools (get + initialize + log count; except debug "not available"); terminal MCP cmds (to connector mocks); tests/mcp (AsyncMock heavy); no tools ever reach main registry or _get_tool_schemas.
- **Transports**: Stdio (real subprocess), HTTP (real), SSE (enum only).
- **Known**: npx @modelcontextprotocol/server-* + custom.
- **State**: Ambitious JSON-RPC + multi-transport but non-functional (mocks/sims everywhere; "In a real implementation..." comments).

**Evidence**: "read_file mcp/client.py:82/117 (mock comments)"; "read_file mcp_manager.py:69/84/89 (simulate + empty tools)"; "read_file manager.py:313 (JSONRPC tools/list)"; "read_file loop.py:157-176 (_init_mcp + except)"; "grep MCP in terminal.py:249-302 (handle_mcp_command)".

## AI Model Inventory
- **Primary**: Ollama (utils/ollama.py + llm.py: OllamaClient httpx streaming /api/chat + generate + tools; ensure_ollama_running; list via /api/tags; hardware-aware select).
- **Routing/Intelligence**: intelligence/model_router.py (10 TaskIntent regex detector, ComplexityScorer + bias, DEFAULT_MODELS qwen/deepseek/phi + thinking; ModelRouter with list/check but route() stub: always qwen2.5-coder:7b GENERAL SIMPLE regardless of prompt/intent).
- **Stance/Adapt**: stance.py (StanceType + temperature_modifier + planning_context).
- **Aliases (README/AGENTS)**: 7b/14b/fast/smart/think → specific Ollama tags; --model flag.
- **Fallbacks**: codellama:7b for low RAM; no GPU path.
- **No real multi-model orchestration** beyond router stub + aliases.

**Evidence**: "read_file model_router.py:316-326 (def route stub + hardcoded)"; "read_file ollama.py:125- (ensure + detect + aliases)"; "read_file llm.py (OllamaClient chat)".

## Agent Inventory
- **Core Loop**: models.py (CognitiveState: INIT/PLAN/ACT/OBSERVE/REFLECT/ADAPT/COMMIT/PAUSE enum + Stance 7-val); core/loop.py (AgentLoop: 8-state machine, MemoryMesh, router, stance, hooks (60+ PRE/POST), bi_op, learning, _mcp; custom TOOL_START or tool_calls; metrics; run_async + generator wrapper).
- **Spawner/Multi**: multi_agent/spawner.py (AgentSpec/Result; 5 types (general/coder/reviewer/researcher/tester); spawn/execute_all wrapping AgentLoop + gather history).
- **Intelligence**: planner.py (create_plan + fallback + risks via Ollama JSON); reflector.py (assess + QualityReport); stance + router (above).
- **Adapters (compat shims)**: 3 (clawspring/nexus/open-swe): hardcoded Analyze*Tool (BaseTool returning static "inspired by" patterns) + *Adapter (get_capabilities etc.); registered via builtin.
- **Hooks/Ext**: hooks.py (HookManager + 60+ events like PRE_RUN/POST_TOOL/ON_STATE_CHANGE + load_global_hooks).
- **Primary vs Rich**: Terminal uses simple api backend (no full loop/states/memory); tui + spawner use rich loop.

**Evidence**: "read_file core/loop.py:110- (AgentLoop __init__ + run_async + states)"; "read_file multi_agent/spawner.py:78 (from ...loop import AgentLoop)"; "read_file adapters/nexus_adapter.py:35- (hardcoded result)"; "grep HookEvent" (hooks.py + loop).

## Workflow Inventory
- **Core Cognitive**: core/loop.py (8-state + memory record on every action + PRE/POST hooks + bi_op.process_action + stance).
- **Middleware**: middleware/ (base.py abstract wrap; error_handler/message_queue/sanitize/step_limit — 6 layers per ARCHITECTURE/AGENTS).
- **Tasks/Planning**: tools/builtin/task_tools.py + todo_tool.py (TodoWrite/Read + Task* using BaseTool; .maximus/todos.json); planner/reflector.
- **Benchmark/Eval**: benchmark/benchmark.py; tests heavy on flows.
- **Session/Branch**: chat/session.py + memory/branching + session_sync + session_manager (disk JSON).
- **Other**: hooks for extensibility; bi_op (OS+agent partnership); evolution/learning (stubs).

**Evidence**: "read_file middleware/base.py:22 (Middleware ABC)"; "read_file loop.py:394 (hooks.trigger_pre)"; "read_file tools/builtin/task_tools.py (Todo* impl)".

## API Inventory
- **REST (FastAPI)**: api/__init__.py (app + lifespan tool reg + CORS); routes.py (APIRouter /tools/execute /status; uses AgentLoop in some paths).
- **WebSocket**: api/websocket.py (2 endpoints: /agent (event map), /terminal (echo + "not_implemented" stubs + var bug in /health check)).
- **Internal**: MaximusBackend.process_message/run_tool (api.py); tool registry dispatch; MCP/LLM clients.
- **Health/Status**: /health; maximus status/doctor (terminal/ollama checks).

**Evidence**: "read_file api/__init__.py:28 (FastAPI)"; "read_file websocket.py:186 (not_implemented)"; "read_file routes.py:54 (execute)".

## Database/Memory Inventory
- **In-memory**: MemoryMesh (episodic deque events, semantic dict + tags/layer, procedural patterns + success, working goal/plan/temp/checkpoints + to_context).
- **Persistent**: Memdir (project .maximus/memdir/MEMORY.md index + {topic}.md frontmatter); session JSON (~/.local/share/maximus/sessions/*.json via session_manager).
- **Vector (optional)**: chromadb (or keyword SimpleVectorStore fallback in vector_memory.py; augment_context).
- **No traditional DB**: FS + optional vector store; no SQLAlchemy etc.

**Evidence**: "read_file memory/memory_mesh.py:27-502 (full banks + Memdir + MemoryMesh)"; "read_file vector_memory.py:20 (chromadb try)"; "read_file session_manager.py:38- (disk load)".

## External Service Inventory
- **LLM**: Ollama (localhost:11434; primary/local).
- **Web/Tools**: web_search/fetch (duckduckgo? + httpx; local_only=False), browser_tool (likely playwright), npx (MCP servers), git/python/node exec, docker (sandbox), pypi (discovery).
- **Optional/External in claims**: Modal/LangSmith/Daytona (sandbox "simulated"), chromadb (vector), openai/anthropic (declared unused), nvidia-smi (GPU).
- **No auth/cloud required** for core (local Ollama + fs).

**Evidence**: "grep local_only=False (web tools)"; "read_file discovery/pypi.py (mock + httpx)"; "read_file sandbox/factory.py (Modal etc. stubs)"; "ollama.py nvidia-smi".

## Identified Issues (Dead Code/Unused/Mocks/Incomplete/Technical Debt/Risks)
- **Mocks/Sims (non-functional core claims)**: mcp/* (client.py:82 "# For now, return mock tools"; mcp_manager.py:84/89 "Simulate tool listing/call"; manager.py real protocol but unwired); discovery/pypi.py:83 (_mock_search hardcoded); package_discovery.py:57/60 (NotImplementedError), 81/93 ("simplified mock" + placeholder HTML parse). MCP "✅ Complete" (README:120) but no real tools ever registered/usable.
- **TODOs/Stubs**: memory/compaction.py:246 ("# TODO: Actually call Ollama here" — returns f-string); loop.py:561 (pass in learning); model_router.py:316-326 (route() always hardcoded default despite full detectors/scorer/intent code).
- **Incomplete/Claims Mismatch**: 8-state (loop.py only partial transitions; api path ignores); "Docker Sandbox ✅" (sandbox.py:96-116 always fallback + warning; factory "simulated"); "React Terminal ✅ Build passes" (plan + CI/Docker but no source tree — grep/list_dir confirm absent maximus-terminal/; builds fail); "Vector Memory ✅" / "Sub-Agent Spawning ✅" / "32/34+ Tools" (vector optional/debug; spawner secondary; count ~31 + dupes); "100% local / No external APIs" (AGENTS:7) vs web tools (local_only=False), npx, shell, openai deps.
- **Duplication/Dead**: task_tools.py vs todo_tool.py (old 'Tool' class + different paths); 3x MCP modules (conflicting); core/api.py (simple) vs loop.py (rich) — primary path uses api; legacy cli.py; adapters hardcoded static (no real repo analysis beyond arg); hooks defined 60+ but limited exercise.
- **Undeclared/Deps**: httpx/psutil heavy but missing from pyproject top-level; openai/anthropic unused.
- **Frontend/Infra Debt**: package-lock + playwright + Docker/CI/prod references but no React source (only plan); CI has "continue-on-error:true" on frontend; compose has volumes but prod nginx/certs incomplete for real deploy.
- **Tests/Coverage**: 16 files but mock-heavy (e.g. tests/mcp use AsyncMock; integration often -m "not integration"); root test_*.py suggest early scaffolding.
- **Security/Prod Risks**: Layer3 safety often auto-True ("for automated mode"); dangerous shell regex but exec allowed; no auth on API/WS; sessions FS only; docker always host fs; external web/MCP npx risk; "intelligence" non-op (router stub); version 0.1.0 vs "v2.0" marketing + "100% completion" commit.
- **Other Debt**: discovery NotImplemented install; many logger.debug excepts (mcp/vector/bi-op); session split (api vs loop); no real MCP protocol in active code; partial WS ("not_implemented"); psutil/Win fallbacks brittle.

**Evidence examples** (full list in subagent outputs + greps): "grep result: C:\Users\11vat\Desktop\maximus-ai-audit\src\maximus\memory\compaction.py:246..."; "C:\...mcp\client.py:82..."; "C:\...discovery\package_discovery.py:57..."; "read_file ci.yml:89 (cd maximus-terminal + continue-on-error)"; "read_file model_router.py:321 (hardcoded qwen)"; "AGENTS.md:7 'No external APIs'"; "list_dir + grep: no maximus-terminal source"; "read_file sandbox.py:103 (use_docker=False)".

## Freshness / Gaps vs Vision
- **Freshness**: Most source/docs "as of" clone (2026-05-08 commit); claims in README/ARCH/PRD predate full impl (Phase 2/3 docs note "Ready for Phase 3: Implementation").
- **Gaps/Risks**: High potential (rich cognitive/memory/MCP design aligns with library S-tier local/agent patterns like ollama + local-deep-research + mcp servers) but production readiness low (mocks + stubs + mismatch + missing frontend). Scalability: memory banks good but vector optional + no real multi-node; cost: local but external web/MCP risk; maintainability: dupe + debt + "Phase X" docs.
- **Strengths**: Tool registry + 30+ builtins solid; MemoryMesh ambitious + persistent; hooks extensibility; Ollama/hardware auto; safety intent; multi-agent spawner; aligns with library (could integrate as agent-frameworks entry post-fix + recipes with Semgrep/Graphiti/Coolify/Langfuse).

**Recommended Next (per library-status + AGENTS)**: Fix router (wire detectors), consolidate MCP (pick one real impl + tests), de-dupe tools, stub/fix or remove frontend claims, declare missing deps, harden safety layer3, wire rich loop as default or document split. Re-verify (pytest + docker build). Then use library `research-project`/`update-catalog-entry` + `generate-integration-recipe` for agent-frameworks catalog entry + cross-recipes (Maximus loop + library MCPs/memory/ollama + security/observability/deploy). `hidden-gem-hunt` if stars/activity fit. Re-run adapted library-status. Spawn subagents for Phases 2-7.

**Sources**: All from 2026-06-10 tool calls on clone (list_dir, 30+ read_file, 15+ grep, run_terminal git/CI/compose + subagent parallel deep dives). "Research performed 2026-06-10 using list_dir/read_file/grep/run_terminal on C:\Users\11vat\Desktop\maximus-ai-audit. Metrics as of 2026-05-08 commit." Full subagent reports (inventories + 9-axis + debt with citations) synthesized here; see session logs for raw.

This completes Phase 1 deliverable. Ready for Phase 2 (competitive) + 3 (hidden gems) via skills/subagents. Copy this file to clone/docs/ if desired for the repo.