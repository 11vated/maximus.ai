"""Model intelligence for Maximus.ai - Model router, thinking models.

Implements Nexus pattern:
- Intent detection (10 categories)
- Task complexity scoring (TRIVIAL → EXPERT)
- Model routing based on task type
- Thinking model for reasoning tasks
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskIntent(str, Enum):
    """Task intent categories."""
    CODE_GENERATION = "code_generation"
    CODE_EDIT = "code_edit"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    RESEARCH = "research"
    EXPLORATION = "exploration"
    REVIEW = "review"
    TESTING = "testing"
    REFACTORING = "refactoring"
    GENERAL = "general"


class ComplexityLevel(str, Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class ModelConfig:
    """Configuration for a model."""
    name: str
    provider: str = "ollama"
    max_tokens: int = 8192
    recommended_for: List[TaskIntent] = field(default_factory=list)
    is_thinking: bool = False
    temperature: float = 0.7


@dataclass
class RoutingDecision:
    """Routing decision result."""
    model: str
    intent: TaskIntent
    complexity: ComplexityLevel
    reasoning: str
    temperature: float = 0.7


# Default model registry
DEFAULT_MODELS = {
    # Code-focused models
    "qwen2.5-coder:7b": ModelConfig(
        name="qwen2.5-coder:7b",
        recommended_for=[TaskIntent.CODE_GENERATION, TaskIntent.CODE_EDIT, TaskIntent.REFACTORING],
        temperature=0.3
    ),
    "qwen2.5-coder:14b": ModelConfig(
        name="qwen2.5-coder:14b",
        recommended_for=[TaskIntent.CODE_GENERATION, TaskIntent.CODE_EDIT, TaskIntent.REFACTORING],
        temperature=0.3
    ),
    "deepseek-coder:6.7b": ModelConfig(
        name="deepseek-coder:6.7b",
        recommended_for=[TaskIntent.CODE_GENERATION, TaskIntent.CODE_EDIT],
        temperature=0.3
    ),
    # Thinking models (for reasoning)
    "deepseek-r1:7b": ModelConfig(
        name="deepseek-r1:7b",
        recommended_for=[TaskIntent.DEBUGGING, TaskIntent.ARCHITECTURE, TaskIntent.RESEARCH],
        is_thinking=True,
        temperature=0.5
    ),
    "deepseek-r1:14b": ModelConfig(
        name="deepseek-r1:14b",
        recommended_for=[TaskIntent.DEBUGGING, TaskIntent.ARCHITECTURE, TaskIntent.RESEARCH],
        is_thinking=True,
        temperature=0.5
    ),
    # Fast models (for simple tasks)
    "llama3.2:3b": ModelConfig(
        name="llama3.2:3b",
        recommended_for=[TaskIntent.GENERAL, TaskIntent.EXPLORATION],
        max_tokens=4096,
        temperature=0.7
    ),
    "phi3.5:3.8b": ModelConfig(
        name="phi3.5:3.8b",
        recommended_for=[TaskIntent.GENERAL, TaskIntent.EXPLORATION],
        max_tokens=4096,
        temperature=0.7
    ),
}


class IntentDetector:
    """Detects task intent from user input."""
    
    # Intent patterns
    INTENT_PATTERNS = {
        TaskIntent.CODE_GENERATION: [
            r"create\s+(\w+\s+)?(function|class|component|file)",
            r"write\s+(code|a|some)\s+",
            r"implement\s+",
            r"build\s+",
            r"make\s+",
            r"generate\s+",
            r"add\s+(new\s+)?(feature|function)",
            r"how\s+to\s+make",
        ],
        TaskIntent.CODE_EDIT: [
            r"edit\s+",
            r"modify\s+",
            r"change\s+",
            r"update\s+",
            r"fix\s+",
            r"replace\s+",
            r"rename\s+",
        ],
        TaskIntent.DEBUGGING: [
            r"debug\s+",
            r"(why|why\s+is|why\s+does)\s+.*not\s+(work|working)",
            r"(fix|solve)\s+(the\s+)?(bug|error|issue|problem)",
            r"trace\s+",
            r"stack\s+trace",
            r"exception",
            r"error\s+",
        ],
        TaskIntent.ARCHITECTURE: [
            r"design\s+",
            r"architecture",
            r"structure",
            r"how\s+should\s+i",
            r"best\s+(practice|way|approach)",
            r"pattern",
            r"refactor.*to",
            r"migrate",
        ],
        TaskIntent.RESEARCH: [
            r"find\s+(information|docs|documentation)",
            r"search\s+for",
            r"look\s+up",
            r"what\s+is\s+",
            r"explain\s+",
            r"how\s+does\s+",
            r"understand\s+",
            r"learn\s+about",
        ],
        TaskIntent.EXPLORATION: [
            r"(show|list|get)\s+(me\s+)?(all\s+)?(the\s+)?files",
            r"explore",
            r"find\s+(all|where)",
            r"search\s+",
            r"grep",
            r"look\s+(at|for)",
        ],
        TaskIntent.REVIEW: [
            r"(review|check|analyze)\s+(the\s+)?(code|file)",
            r"review",
            r"audit",
            r"assess",
            r"evaluate",
            r"best\s+practices",
        ],
        TaskIntent.TESTING: [
            r"test\s+",
            r"write\s+(test|spec)",
            r"add\s+test",
            r"unit\s+test",
            r"integration\s+test",
            r"run\s+test",
            r"verify\s+",
        ],
        TaskIntent.REFACTORING: [
            r"refactor",
            r"clean\s+up",
            r"simplify",
            r"improve\s+(the\s+)?(code|structure)",
            r"remove\s+duplicat",
            r"optimize\s+",
        ],
    }
    
    def detect(self, prompt: str) -> TaskIntent:
        """Detect intent from prompt."""
        prompt_lower = prompt.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return intent
        
        return TaskIntent.GENERAL


class ComplexityScorer:
    """Scores task complexity."""
    
    # Complexity indicators
    COMPLEX_INDICATORS = [
        # File count
        r"(\d+)\s+files?",
        r"multiple\s+files?",
        r"several\s+files?",
        
        # Technical terms
        r"database",
        r"api\s+",
        r"auth",
        r"security",
        r"concurrent",
        r"async",
        r"distributed",
        
        # Scope
        r"entire\s+",
        r"whole\s+",
        r"complete\s+",
        r"system",
        
        # Frameworks
        r"react",
        r"django",
        r"fastapi",
        r"kubernetes",
        r"docker",
    ]
    
    SIMPLE_INDICATORS = [
        r"simple",
        r"basic",
        r"just\s+",
        r"one\s+file",
        r"small\s+",
        r"quick",
        r"easy",
    ]
    
    def score(self, prompt: str, intent: TaskIntent) -> ComplexityLevel:
        """Score complexity of the task."""
        prompt_lower = prompt.lower()
        
        complex_count = sum(
            1 for pattern in self.COMPLEX_INDICATORS
            if re.search(pattern, prompt_lower)
        )
        
        simple_count = sum(
            1 for pattern in self.SIMPLE_INDICATORS
            if re.search(pattern, prompt_lower)
        )
        
        # Adjust based on intent
        intent_complexity = {
            TaskIntent.ARCHITECTURE: 2,
            TaskIntent.DEBUGGING: 1,
            TaskIntent.REFACTORING: 1,
            TaskIntent.CODE_GENERATION: 1,
            TaskIntent.CODE_EDIT: 0,
            TaskIntent.TESTING: 0,
            TaskIntent.EXPLORATION: -1,
            TaskIntent.RESEARCH: -1,
            TaskIntent.REVIEW: 0,
            TaskIntent.GENERAL: 0,
        }
        
        score = complex_count - simple_count + intent_complexity.get(intent, 0)
        
        if score <= -2:
            return ComplexityLevel.TRIVIAL
        elif score == -1:
            return ComplexityLevel.SIMPLE
        elif score == 0:
            return ComplexityLevel.MODERATE
        elif score == 1:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.EXPERT


class ModelRouter:
    """Routes tasks to optimal models based on intent and complexity."""
    
    def __init__(self, models: Optional[Dict[str, ModelConfig]] = None):
        self.models = models or DEFAULT_MODELS
        self.intent_detector = IntentDetector()
        self.complexity_scorer = ComplexityScorer()
        self._default_model = "qwen2.5-coder:7b"
        self._thinking_model = "deepseek-r1:7b"
        
    def set_default_model(self, model: str) -> None:
        """Set default model."""
        if model in self.models:
            self._default_model = model
            
    def set_thinking_model(self, model: str) -> None:
        """Set thinking model for reasoning tasks."""
        if model in self.models:
            self._thinking_model = model
    
    def route(self, prompt: str) -> RoutingDecision:
        """Route prompt to optimal model."""
        
        # Detect intent
        intent = self.intent_detector.detect(prompt)
        
        # Score complexity
        complexity = self.complexity_scorer.score(prompt, intent)
        
        # Select model based on intent
        if intent in (TaskIntent.DEBUGGING, TaskIntent.ARCHITECTURE, TaskIntent.RESEARCH):
            # Use thinking model for reasoning tasks
            model_config = self.models.get(self._thinking_model, self.models[self._default_model])
            reasoning = f"Routed to thinking model for {intent.value} task"
        elif complexity in (ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE):
            # Use fast model for simple tasks
            for name, config in self.models.items():
                if intent in config.recommended_for and config.max_tokens <= 4096:
                    model_config = config
                    break
            else:
                model_config = self.models.get("llama3.2:3b", self.models[self._default_model])
            reasoning = f"Simple task - using fast model"
        else:
            # Use coding model for complex tasks
            for name, config in self.models.items():
                if intent in config.recommended_for and not config.is_thinking:
                    model_config = config
                    break
            else:
                model_config = self.models[self._default_model]
            reasoning = f"Routed to coding model for {intent.value} ({complexity.value})"
        
        return RoutingDecision(
            model=model_config.name,
            intent=intent,
            complexity=complexity,
            reasoning=reasoning,
            temperature=model_config.temperature
        )
    
    def list_available_models(self) -> List[Dict]:
        """List all available models."""
        return [
            {
                "name": name,
                "provider": config.provider,
                "max_tokens": config.max_tokens,
                "is_thinking": config.is_thinking,
                "recommended_for": [i.value for i in config.recommended_for],
            }
            for name, config in self.models.items()
        ]
    
    async def check_model_available(self, model: str) -> bool:
        """Check if model is available in Ollama."""
        from maximus.utils.llm import OllamaClient
        try:
            client = OllamaClient()
            models = await client.list_models()
            return model in models
        except Exception:
            return False


# Global router
_model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get global model router."""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router