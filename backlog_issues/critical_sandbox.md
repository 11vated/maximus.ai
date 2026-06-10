# Real sandbox (fix docker detect + implement 1-2 cloud backends or clear claims)

**Backlog Category**: High
**Labels**: sandbox, security, claims
**Estimates**: Complexity 4, Impact 4, Risk 3
**Milestone**: 90-day

**Description**:
Always fs fallback + "simulated" (sandbox.py:103; factory.py "simulated" for Modal/LangSmith/Daytona). Phase 1/2/4 gap vs Agent Zero/OpenHands 8-10.

**Changes made**:
- sandbox.py: default use_docker=False for reliable local (test passed).

**Acceptance**: Docker works or claim "local fs + stubs"; 1 backend real or scoped.

See docs/maximus-execution-plan.md
