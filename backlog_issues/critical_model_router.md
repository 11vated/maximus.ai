# Fix model router stub (wire detectors/scorer/intent; remove hardcoded default)

**Backlog Category**: Critical
**Labels**: intelligence, router, claims
**Estimates**: Complexity 3, Impact 4, Risk 2
**Milestone**: 30-day

**Description**:
intelligence/model_router.py full ... but route() stub 316-326 always qwen GENERAL SIMPLE.

**Changes made**:
- model_router.py: route method replaced with real logic using detector and scorer.

**Acceptance**: route() uses detectors/scorer; tests for intents/complexity; ...

See docs/maximus-execution-plan.md
