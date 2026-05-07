"""Quality assessment and self-correction (from Nexus)."""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from maximus.models import AgentConfig, Plan
from maximus.utils.llm import LLMClient


class QualityReport:
    """Quality assessment result."""

    def __init__(
        self,
        met_criteria: List[str],
        unmet_criteria: List[str],
        errors: List[str],
        needs_revision: bool,
        confidence: float,
        suggestions: List[str],
    ):
        self.met_criteria = met_criteria
        self.unmet_criteria = unmet_criteria
        self.errors = errors
        self.needs_revision = needs_revision
        self.confidence = confidence
        self.suggestions = suggestions

    def dict(self) -> dict:
        return {
            "met_criteria": self.met_criteria,
            "unmet_criteria": self.unmet_criteria,
            "errors": self.errors,
            "needs_revision": self.needs_revision,
            "confidence": self.confidence,
            "suggestions": self.suggestions,
        }


class Reflector:
    """Assesses plan execution quality and suggests improvements."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.llm = LLMClient(self.config)

    async def assess(self, plan: Plan, results: List[Dict]) -> QualityReport:
        """Assess plan execution quality."""
        criteria = "\n".join(f"- {c}" for c in plan.success_criteria)

        # Simplify results for the prompt
        results_str = json.dumps(
            [
                {"step": r.get("step_id", ""), "success": r.get("success"), "output": str(r.get("output", ""))[:500]}
                for r in results
            ],
            indent=2,
        )

        prompt = f"""You are a quality assessment expert.

Plan Goal: {plan.goal}

Success Criteria:
{criteria}

Step Results:
{results_str}

Assess and output ONLY valid JSON (no markdown, no explanation):
{{
    "met_criteria": ["..."],
    "unmet_criteria": ["..."],
    "errors": ["..."],
    "needs_revision": false,
    "confidence": 0.95,
    "suggestions": ["..."]
}}"""

        try:
            response = await self.llm.generate(
                model=self.config.model,
                prompt=prompt,
                system="You are a JSON-only quality expert. Output valid JSON only."
            )

            # Extract JSON from response
            text = response.strip()
            if "{" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                json_str = text[start:end]
            else:
                json_str = text

            data = json.loads(json_str)

            return QualityReport(
                met_criteria=data.get("met_criteria", []),
                unmet_criteria=data.get("unmet_criteria", []),
                errors=data.get("errors", []),
                needs_revision=data.get("needs_revision", False),
                confidence=data.get("confidence", 0.5),
                suggestions=data.get("suggestions", []),
            )

        except json.JSONDecodeError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to parse reflector response: {e}")
            # Fallback assessment
            return QualityReport(
                met_criteria=[],
                unmet_criteria=plan.success_criteria,
                errors=[f"Failed to assess: {e}"],
                needs_revision=True,
                confidence=0.0,
                suggestions=["Fix reflector JSON parsing"],
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Reflector error: {e}")
            return QualityReport(
                met_criteria=[],
                unmet_criteria=plan.success_criteria,
                errors=[str(e)],
                needs_revision=True,
                confidence=0.0,
                suggestions=["Check reflector implementation"],
            )

    async def close(self):
        await self.llm.close()
