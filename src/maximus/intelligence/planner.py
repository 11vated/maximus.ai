"""LLM-based planner for Maximus.ai - decomposed goals into steps.
Uses Ollama locally - 100% free, no API costs.

Pattern from: Nexus (simple command-based), Open-SWE (LangGraph), Claude Code (sophisticated)
"""

import json
import logging
from typing import Any, Dict, List, Optional
from maximus.models import AgentConfig, Plan, Step
from maximus.utils.llm import OllamaClient

logger = logging.getLogger(__name__)

class Planner:
    """Creates execution plans from high-level goals using local Ollama."""
    
    # System prompt for planning
    SYSTEM_PROMPT = """You are an expert software architect planner.
Given a user goal, decompose it into specific, executable steps.
Each step should use a specific tool with clear arguments.

Available tools will be provided. Output ONLY valid JSON in this format:
{
    "analysis": "Brief analysis of the goal",
    "steps": [
        {"id": "1", "tool": "tool_name", "args": {"arg1": "value1"}, "deps": [], "description": "What this step does"}
    ],
    "success_criteria": ["Criterion 1", "Criterion 2"],
    "estimated_complexity": "low|medium|high"
}"""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.llm = OllamaClient(base_url=self.config.ollama_url)
        
    async def create_plan(self, goal: str, available_tools: List[Dict] = None) -> Plan:
        """Decompose goal into structured plan using Ollama."""
        import uuid
        
        # Build tool list for prompt
        tools_str = "Available tools:\n"
        if available_tools:
            for tool in available_tools[:15]:  # Limit to prevent token overflow
                tools_str += f"  - {tool.get('name')}: {tool.get('description', 'No description')}\n"
        else:
            tools_str = "Available tools: read_file, write_file, edit_file, execute_shell, grep, glob, ls, python_runner, etc."
        
        prompt = f"""Goal: {goal}

{tools_str}

Create a step-by-step plan to accomplish this goal.
"""
        
        try:
            response = await self.llm.generate(
                model=self.config.model,
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                temperature=0.2,  # Lower temperature for more deterministic planning
            )
            
            # Extract JSON from response
            text = response.strip()
            
            # Try to find JSON block
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                data = json.loads(json_str)
            else:
                # Try parsing entire response
                data = json.loads(text)
            
            # Convert to Plan model
            steps = []
            for i, s in enumerate(data.get("steps", [])):
                steps.append(Step(
                    id=s.get("id", str(i + 1)),
                    tool=s.get("tool", "execute_shell"),
                    args=s.get("args", {}),
                    deps=s.get("deps", []),
                    timeout=s.get("timeout", 300),
                ))
            
            return Plan(
                id=f"plan_{uuid.uuid4().hex[:8]}",
                goal=goal,
                steps=steps,
                success_criteria=data.get("success_criteria", []),
                risk_flags=self._assess_risks(goal, steps),
                estimated_cost=len(steps) * 0.001,  # Rough estimate
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse planner JSON: {e}\nResponse: {text[:500]}")
            return self._fallback_plan(goal)
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return self._fallback_plan(goal)
    
    def _assess_risks(self, goal: str, steps: List[Dict]) -> List[str]:
        """Assess potential risks in the plan."""
        risks = []
        goal_lower = goal.lower()
        
        # Check for dangerous operations
        dangerous_tools = ["execute_shell", "delete_file", "edit_file"]
        for step in steps:
            if step.get("tool") in dangerous_tools:
                risks.append(f"Uses {step.get('tool')} - review carefully")
        
        # Check for external resources
        if "install" in goal_lower or "pip" in goal_lower:
            risks.append("Package installation - verify packages")
            
        if "delete" in goal_lower or "remove" in goal_lower:
            risks.append("Destructive operation - confirm before executing")
            
        return risks
    
    def _fallback_plan(self, goal: str) -> Plan:
        """Create a simple fallback plan when LLM planning fails."""
        import uuid
        
        # Simple heuristic-based planning
        goal_lower = goal.lower()
        
        if "create" in goal_lower or "new" in goal_lower or "write" in goal_lower:
            steps = [
                Step(id="1", tool="write_file", args={"path": "output.txt", "content": f"# Goal: {goal}\n# Implement me!"}),
            ]
        elif "run" in goal_lower or "execute" in goal_lower or "test" in goal_lower:
            steps = [
                Step(id="1", tool="execute_shell", args={"command": "echo 'Running...'"}),
            ]
        elif "read" in goal_lower or "analyze" in goal_lower or "check" in goal_lower:
            steps = [
                Step(id="1", tool="ls", args={"path": "."}),
            ]
        else:
            steps = [
                Step(id="1", tool="execute_shell", args={"command": "echo 'Processing goal...'"}),
            ]
        
        return Plan(
            id=f"plan_fallback_{uuid.uuid4().hex[:8]}",
            goal=goal,
            steps=steps,
            success_criteria=["Goal processed"],
            risk_flags=["Fallback plan - may need refinement"],
        )
    
    async def reflect_on_plan(self, plan: Plan, results: List[Dict]) -> Dict[str, Any]:
        """Reflect on plan execution and suggest improvements."""
        prompt = f"""Plan goal: {plan.goal}
Steps executed: {len(plan.steps)}
Results: {json.dumps(results, indent=2)[:1000]}

Analyze what went well and what could be improved. Output JSON:
{{
    "success_score": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}"""
        
        try:
            response = await self.llm.generate(
                model=self.config.model,
                prompt=prompt,
                system="You are a reflective analyst. Output only JSON.",
                temperature=0.3,
            )
            
            text = response.strip()
            json_start = text.find('{')
            if json_start >= 0:
                data = json.loads(text[json_start:text.rfind('}')+1])
                return data
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
        
        return {"success_score": 0.5, "issues": [], "suggestions": []}
    
    async def close(self):
        """Cleanup resources."""
        await self.llm.close()
