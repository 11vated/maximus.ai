"""Project context detection and injection.

Automatically detects project type and builds context for the AI.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ProjectInfo:
    """Detected project information."""
    project_type: str  # python, node, go, rust, java, etc.
    root: Path
    language: str
    build_system: Optional[str]
    test_framework: Optional[str]
    dependencies: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    structure: Dict[str, Any] = field(default_factory=dict)
    
    def to_context(self) -> str:
        """Convert to context string for AI."""
        lines = [f"## Project: {self.project_type}", ""]
        lines.append(f"**Language**: {self.language}")
        
        if self.build_system:
            lines.append(f"**Build System**: {self.build_system}")
        
        if self.test_framework:
            lines.append(f"**Test Framework**: {self.test_framework}")
        
        if self.dependencies:
            lines.append(f"**Dependencies**: {', '.join(self.dependencies[:10])}")
        
        if self.entry_points:
            lines.append(f"**Entry Points**: {', '.join(self.entry_points)}")
        
        if self.structure:
            lines.append("")
            lines.append("### Structure")
            for key, val in self.structure.items():
                lines.append(f"- {key}: {val}")
        
        return "\n".join(lines)


class ProjectDetector:
    """Auto-detect project type and configuration."""
    
    # Project type markers
    PROJECT_MARKERS = {
        "python": {
            "files": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile"],
            "dirs": ["src", "tests", "venv", ".venv"],
            "marker": "python"
        },
        "node": {
            "files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
            "dirs": ["src", "dist", "node_modules", "__tests__"],
            "marker": "node"
        },
        "go": {
            "files": ["go.mod", "go.sum"],
            "dirs": ["cmd", "internal", "pkg"],
            "marker": "go"
        },
        "rust": {
            "files": ["Cargo.toml", "Cargo.lock"],
            "dirs": ["src", "tests", "examples"],
            "marker": "rust"
        },
        "java": {
            "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "dirs": ["src/main", "src/test", "target"],
            "marker": "java"
        },
        "csharp": {
            "files": ["*.csproj", "*.sln"],
            "dirs": ["src", "tests"],
            "marker": "csharp"
        },
    }
    
    TEST_FRAMEWORKS = {
        "python": ["pytest", "unittest", "tox", "nose"],
        "node": ["jest", "mocha", "vitest", "tap"],
        "go": ["testing", "ginkgo", "testify"],
        "rust": ["cargo test", "rusty-hook"],
        "java": ["junit", "testng", "spock"],
    }
    
    def __init__(self, workdir: str = "."):
        self.root = Path(workdir).resolve()
    
    def detect(self) -> ProjectInfo:
        """Detect project type and gather information."""
        
        # Check for each project type
        for project_type, markers in self.PROJECT_MARKERS.items():
            if self._has_project_files(markers["files"]):
                return self._build_project_info(project_type, markers)
        
        # Default to generic project
        return ProjectInfo(
            project_type="generic",
            root=self.root,
            language="unknown",
            build_system=None,
            test_framework=None
        )
    
    def _has_project_files(self, files: List[str]) -> bool:
        """Check if any of the marker files exist."""
        for f in files:
            # Handle glob patterns
            if "*" in f:
                matches = list(self.root.glob(f))
                if matches:
                    return True
            elif (self.root / f).exists():
                return True
        return False
    
    def _build_project_info(self, project_type: str, markers: Dict) -> ProjectInfo:
        """Build full project info."""
        
        build_system = self._detect_build_system(project_type)
        test_framework = self._detect_test_framework(project_type)
        dependencies = self._detect_dependencies(project_type)
        entry_points = self._detect_entry_points(project_type)
        structure = self._detect_structure(markers["dirs"])
        
        # Map to language name
        lang_map = {
            "python": "Python",
            "node": "JavaScript/TypeScript",
            "go": "Go",
            "rust": "Rust",
            "java": "Java",
            "csharp": "C#"
        }
        
        return ProjectInfo(
            project_type=project_type,
            root=self.root,
            language=lang_map.get(project_type, "Unknown"),
            build_system=build_system,
            test_framework=test_framework,
            dependencies=dependencies,
            entry_points=entry_points,
            structure=structure
        )
    
    def _detect_build_system(self, project_type: str) -> Optional[str]:
        """Detect build system."""
        if project_type == "python":
            if (self.root / "pyproject.toml").exists():
                return "pyproject.toml (PEP 517)"
            elif (self.root / "setup.py").exists():
                return "setup.py"
            elif (self.root / "requirements.txt").exists():
                return "requirements.txt"
        
        elif project_type == "node":
            if (self.root / "package.json").exists():
                return "npm"
            elif (self.root / "yarn.lock").exists():
                return "yarn"
            elif (self.root / "pnpm-lock.yaml").exists():
                return "pnpm"
        
        elif project_type == "go":
            return "go modules"
        
        elif project_type == "rust":
            return "Cargo"
        
        elif project_type == "java":
            if (self.root / "pom.xml").exists():
                return "Maven"
            elif (self.root / "build.gradle").exists():
                return "Gradle"
        
        return None
    
    def _detect_test_framework(self, project_type: str) -> Optional[str]:
        """Detect test framework."""
        if project_type == "python":
            if (self.root / "pytest.ini").exists() or (self.root / "pyproject.toml").exists():
                if (self.root / "pyproject.toml").exists():
                    try:
                        content = (self.root / "pyproject.toml").read_text()
                        if "pytest" in content:
                            return "pytest"
                    except:
                        pass
            for f in ["test_*.py", "*_test.py"]:
                if list(self.root.glob(f"tests/{f}")) or list(self.root.glob(f)):
                    return "unittest"
        
        elif project_type == "node":
            if (self.root / "package.json").exists():
                try:
                    pkg = json.loads((self.root / "package.json").read_text())
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "jest" in deps:
                        return "Jest"
                    elif "mocha" in deps:
                        return "Mocha"
                    elif "vitest" in deps:
                        return "Vitest"
                except:
                    pass
        
        return None
    
    def _detect_dependencies(self, project_type: str) -> List[str]:
        """Detect main dependencies."""
        if project_type == "python":
            if (self.root / "requirements.txt").exists():
                try:
                    content = (self.root / "requirements.txt").read_text()
                    return [line.strip().split("==")[0].split(">=")[0] 
                           for line in content.split("\n") 
                           if line.strip() and not line.startswith("#")][:10]
                except:
                    pass
        
        elif project_type == "node":
            if (self.root / "package.json").exists():
                try:
                    pkg = json.loads((self.root / "package.json").read_text())
                    deps = list(pkg.get("dependencies", {}).keys())[:10]
                    return deps
                except:
                    pass
        
        return []
    
    def _detect_entry_points(self, project_type: str) -> List[str]:
        """Detect entry points."""
        entry_points = []
        
        if project_type == "python":
            for f in ["main.py", "app.py", "run.py", "server.py"]:
                if (self.root / f).exists():
                    entry_points.append(f)
            # Check for __main__.py
            if (self.root / "__main__.py").exists():
                entry_points.append("__main__.py")
        
        elif project_type == "node":
            if (self.root / "package.json").exists():
                try:
                    pkg = json.loads((self.root / "package.json").read_text())
                    if "main" in pkg:
                        entry_points.append(pkg["main"])
                    if "scripts" in pkg:
                        for script in ["start", "dev", "build"]:
                            if script in pkg["scripts"]:
                                entry_points.append(f"npm run {script}")
                except:
                    pass
        
        elif project_type == "go":
            for f in (self.root / "cmd").glob("*/*.go") if (self.root / "cmd").exists() else []:
                entry_points.append(str(f.relative_to(self.root)))
        
        return entry_points
    
    def _detect_structure(self, marker_dirs: List[str]) -> Dict[str, str]:
        """Detect directory structure."""
        structure = {}
        
        for d in marker_dirs:
            path = self.root / d
            if path.exists() and path.is_dir():
                # Count files in directory
                try:
                    count = len(list(path.rglob("*")))
                    structure[d] = f"{count} files"
                except:
                    structure[d] = "exists"
        
        # Add common directories
        for d in ["docs", "config", "scripts", "bin"]:
            path = self.root / d
            if path.exists():
                structure[d] = "exists"
        
        return structure
    
    def get_git_info(self) -> Dict[str, Any]:
        """Get git repository information."""
        import subprocess
        
        info = {}
        
        # Check if git exists
        git_dir = self.root / ".git"
        if not git_dir.exists():
            return info
        
        try:
            # Branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info["branch"] = result.stdout.strip()
            
            # Status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
                staged = [l for l in lines if l.startswith(" M") or l.startswith("A ")]
                modified = [l for l in lines if l.startswith(" M")]
                info["staged"] = len(staged)
                info["modified"] = len(modified)
            
            # Remote
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info["remote"] = result.stdout.strip()
                
        except Exception:
            pass
        
        return info


def detect_project(workdir: str = ".") -> ProjectInfo:
    """Convenience function to detect project."""
    detector = ProjectDetector(workdir)
    return detector.detect()


def get_project_context(workdir: str = ".") -> str:
    """Get full project context string."""
    detector = ProjectDetector(workdir)
    info = detector.detect()
    context = info.to_context()
    
    # Add git info
    git_info = detector.get_git_info()
    if git_info:
        context += "\n\n## Git Status\n"
        if "branch" in git_info:
            context += f"**Branch**: {git_info['branch']}\n"
        if "staged" in git_info:
            context += f"**Staged**: {git_info['staged']} files\n"
        if "modified" in git_info:
            context += f"**Modified**: {git_info['modified']} files\n"
        if "remote" in git_info:
            context += f"**Remote**: {git_info['remote']}\n"
    
    return context