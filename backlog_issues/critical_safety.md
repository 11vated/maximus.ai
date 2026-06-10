# Harden safety layer 3 + enforce everywhere (remove auto-True; add tests)

**Backlog Category**: Critical
**Labels**: safety, security
**Estimates**: Complexity 3, Impact 5, Risk 3
**Milestone**: 30-day

**Description**:
safety.py:121 layer3 often returns True.

**Changes made**:
- loop.py: added safety.layer2_check pre execution validation.

**Acceptance**: Layer3 always prompts in auto; tests; enforcement in api/loop; ...

See docs/maximus-execution-plan.md
