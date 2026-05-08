"""Benchmark System - Test and measure Maximus agent capabilities.

This enables:
- Running evaluation tasks
- Measuring success rates
- Tracking performance over time
- Comparing configurations
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import time
import statistics

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkTask:
    """A single benchmark task."""
    id: str
    name: str
    description: str
    prompt: str
    expected_outcome: str
    category: str  # "code_gen", "debugging", "refactoring", "analysis"
    difficulty: str  # "easy", "medium", "hard"


@dataclass
class BenchmarkResult:
    """Result of running a benchmark task."""
    task_id: str
    success: bool
    duration_ms: float
    error: Optional[str] = None
    steps_taken: int = 0
    tools_used: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class BenchmarkSuite:
    """A collection of benchmark tasks."""
    
    def __init__(self, name: str):
        self.name = name
        self.tasks: List[BenchmarkTask] = []
    
    def add_task(self, task: BenchmarkTask):
        """Add a task to the suite."""
        self.tasks.append(task)
    
    def get_by_category(self, category: str) -> List[BenchmarkTask]:
        """Get tasks by category."""
        return [t for t in self.tasks if t.category == category]
    
    def get_by_difficulty(self, difficulty: str) -> List[BenchmarkTask]:
        """Get tasks by difficulty."""
        return [t for t in self.tasks if t.difficulty == difficulty]


class BenchmarkRunner:
    """Runs benchmarks and tracks results."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.suites: Dict[str, BenchmarkSuite] = {}
        
        # Load default benchmarks
        self._load_default_benchmarks()
    
    def _load_default_benchmarks(self):
        """Load default benchmark tasks."""
        
        # Code Generation Suite
        code_gen = BenchmarkSuite("Code Generation")
        
        code_gen.add_task(BenchmarkTask(
            id="cg_1",
            name="Simple Function",
            description="Write a function to calculate factorial",
            prompt="Write a Python function that calculates the factorial of a number",
            expected_outcome="Function that correctly calculates factorial",
            category="code_gen",
            difficulty="easy"
        ))
        
        code_gen.add_task(BenchmarkTask(
            id="cg_2",
            name="REST API Endpoint",
            description="Create a Flask API endpoint",
            prompt="Create a Flask API endpoint that returns JSON with the current timestamp",
            expected_outcome="Working Flask endpoint",
            category="code_gen",
            difficulty="medium"
        ))
        
        code_gen.add_task(BenchmarkTask(
            id="cg_3",
            name="Data Processing",
            description="Process CSV and compute statistics",
            prompt="Write a Python script that reads a CSV file, computes mean and median for each column, and writes results to a new file",
            expected_outcome="Script that correctly processes data",
            category="code_gen",
            difficulty="medium"
        ))
        
        self.suites["code_generation"] = code_gen
        
        # Debugging Suite
        debugging = BenchmarkSuite("Debugging")
        
        debugging.add_task(BenchmarkTask(
            id="dbg_1",
            name="Find Bug",
            description="Find and fix a logical error",
            prompt="The following function is supposed to check if a number is prime but has a bug. Find and fix it:\ndef is_prime(n):\n    for i in range(2, n):\n        if n % i == 0:\n            return True\n    return False",
            expected_outcome="Corrected function",
            category="debugging",
            difficulty="easy"
        ))
        
        self.suites["debugging"] = debugging
        
        # Refactoring Suite
        refactoring = BenchmarkSuite("Refactoring")
        
        refactoring.add_task(BenchmarkTask(
            id="ref_1",
            name="Improve Readability",
            description="Refactor unclear code",
            prompt="Refactor this code to be more readable:\ndef f(x):\n    r=[]\n    for i in x:\n        if i%2==0:r.append(i*i)\n    return r",
            expected_outcome="More readable code",
            category="refactoring",
            difficulty="easy"
        ))
        
        self.suites["refactoring"] = refactoring
        
        # Analysis Suite
        analysis = BenchmarkSuite("Analysis")
        
        analysis.add_task(BenchmarkTask(
            id="ana_1",
            name="Code Review",
            description="Analyze code for issues",
            prompt="Analyze this code and identify potential issues:\nimport os\ndef get_user(path):\n    return open(path).read()",
            expected_outcome="Identified security issues",
            category="analysis",
            difficulty="medium"
        ))
        
        self.suites["analysis"] = analysis
    
    async def run_task(
        self,
        task: BenchmarkTask,
        execute_fn: Callable[[str], Any]
    ) -> BenchmarkResult:
        """Run a single benchmark task."""
        start_time = time.time()
        
        try:
            # Execute the task
            result = await execute_fn(task.prompt)
            
            duration = (time.time() - start_time) * 1000
            
            # Simple success check - in production, would be more sophisticated
            success = result is not None and len(str(result)) > 0
            
            return BenchmarkResult(
                task_id=task.id,
                success=success,
                duration_ms=duration,
                steps_taken=1  # Simplified
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            return BenchmarkResult(
                task_id=task.id,
                success=False,
                duration_ms=duration,
                error=str(e)
            )
    
    async def run_suite(
        self,
        suite_name: str,
        execute_fn: Callable[[str], Any]
    ) -> Dict[str, Any]:
        """Run an entire benchmark suite."""
        suite = self.suites.get(suite_name)
        if not suite:
            return {"error": f"Suite not found: {suite_name}"}
        
        results = []
        
        for task in suite.tasks:
            result = await self.run_task(task, execute_fn)
            results.append(result)
            self.results.append(result)
        
        # Calculate statistics
        total = len(results)
        passed = sum(1 for r in results if r.success)
        durations = [r.duration_ms for r in results]
        
        return {
            "suite": suite_name,
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": passed / total if total > 0 else 0,
            "avg_duration_ms": statistics.mean(durations) if durations else 0,
            "results": [
                {
                    "task_id": r.task_id,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "error": r.error
                }
                for r in results
            ]
        }
    
    async def run_all(
        self,
        execute_fn: Callable[[str], Any]
    ) -> Dict[str, Any]:
        """Run all benchmark suites."""
        all_results = {}
        
        for suite_name in self.suites.keys():
            suite_result = await self.run_suite(suite_name, execute_fn)
            all_results[suite_name] = suite_result
        
        # Summary
        total_tasks = sum(r["total"] for r in all_results.values())
        total_passed = sum(r["passed"] for r in all_results.values())
        
        return {
            "summary": {
                "total_tasks": total_tasks,
                "passed": total_passed,
                "success_rate": total_passed / total_tasks if total_tasks > 0 else 0
            },
            "suites": all_results
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get benchmark statistics."""
        if not self.results:
            return {"total_runs": 0}
        
        passed = sum(1 for r in self.results if r.success)
        durations = [r.duration_ms for r in self.results]
        
        return {
            "total_runs": len(self.results),
            "passed": passed,
            "failed": len(self.results) - passed,
            "success_rate": passed / len(self.results),
            "avg_duration_ms": statistics.mean(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations)
        }
    
    def export_results(self, path: str):
        """Export results to JSON file."""
        results_path = Path(path)
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_stats(),
            "results": [
                {
                    "task_id": r.task_id,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
        with open(results_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported benchmark results to {results_path}")


# Global benchmark runner
_benchmark_runner: Optional[BenchmarkRunner] = None

def get_benchmark_runner() -> BenchmarkRunner:
    """Get the global benchmark runner instance."""
    global _benchmark_runner
    if _benchmark_runner is None:
        _benchmark_runner = BenchmarkRunner()
    return _benchmark_runner