# Maximus.ai Backlog Item (High)

**Title**: Update deps + declare missing (httpx/psutil top-level; remove unused openai/anthropic or use)

**Description**: Undeclared heavy (httpx/psutil from grep/ollama.py); openai/anthropic declared unused (violates "no external" AGENTS:7). pyproject accurate; "no external" claim or deps updated.

**Evidence**: C:\Users\11vat\Desktop\maximus-ai-audit\pyproject.toml:15-30; grep httpx/psutil 29+; no openai/anthropic calls; Phase 1. (Note: partial clean done earlier by removing openai/anthropic lines.)

**Category**: High; Labels: deps, claims.

**Estimates**: Complexity 2, Impact 3, Risk 2.

**Acceptance**: pyproject accurate; "no external" claim or deps updated.

**Milestone**: 90-day.

**Backlog ref**: From maximus-execution-plan.md (High P1).
