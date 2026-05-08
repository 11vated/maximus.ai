"""Security system for Maximus.ai - Classifier-based permissions.

Implements Claude Code pattern:
- Classifier-based auto-approval (learns from confirmations)
- Command safety classification
- AGENTS.md enforcement
- Trust gradient learning
"""

import re
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum

from maximus.models import TrustLevel, PermissionLevel

logger = logging.getLogger(__name__)


class CommandCategory(str, Enum):
    """Command safety categories."""
    SAFE = "safe"
    NEEDS_CONFIRMATION = "needs_confirmation"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


@dataclass
class CommandClassification:
    """Classification result for a shell command."""
    category: CommandCategory
    confidence: float
    reasons: List[str] = field(default_factory=list)
    matched_pattern: Optional[str] = None


@dataclass
class TrustGradient:
    """Trust progression over time - learns from user feedback."""
    accepted_patterns: Dict[str, int] = field(default_factory=dict)  # pattern -> count
    rejected_patterns: Dict[str, int] = field(default_factory=dict)  # pattern -> count
    tool_success_rates: Dict[str, List[bool]] = field(default_factory=dict)  # tool -> [success]
    last_updated: datetime = field(default_factory=datetime.now)
    
    def record_acceptance(self, pattern: str) -> None:
        """Record a user accepted pattern."""
        self.accepted_patterns[pattern] = self.accepted_patterns.get(pattern, 0) + 1
        self.last_updated = datetime.now()
        
    def record_rejection(self, pattern: str) -> None:
        """Record a user rejected pattern."""
        self.rejected_patterns[pattern] = self.rejected_patterns.get(pattern, 0) + 1
        self.last_updated = datetime.now()
        
    def record_tool_result(self, tool: str, success: bool) -> None:
        """Record tool execution result."""
        if tool not in self.tool_success_rates:
            self.tool_success_rates[tool] = []
        self.tool_success_rates[tool].append(success)
        # Keep only last 100 results
        if len(self.tool_success_rates[tool]) > 100:
            self.tool_success_rates[tool] = self.tool_success_rates[tool][-100:]
        self.last_updated = datetime.now()
    
    def get_tool_success_rate(self, tool: str) -> float:
        """Get success rate for a tool."""
        results = self.tool_success_rates.get(tool, [])
        if not results:
            return 0.5
        return sum(results) / len(results)
    
    def should_auto_approve(self, pattern: str) -> bool:
        """Determine if pattern should be auto-approved."""
        accept_count = self.accepted_patterns.get(pattern, 0)
        reject_count = self.rejected_patterns.get(pattern, 0)
        
        # Auto-approve if accepted 3+ times and never rejected
        if accept_count >= 3 and reject_count == 0:
            return True
        # Auto-approve if accept ratio > 80%
        total = accept_count + reject_count
        if total > 0 and accept_count / total > 0.8:
            return True
        return False


class CommandClassifier:
    """ML-free classifier for shell command safety.
    
    Uses pattern matching to classify commands.
    """
    
    # Dangerous patterns - will block
    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s+/(?:\s|$)",  # rm -rf /
        r":\(\)\{:\|:&\};:",       # Fork bomb
        r"dd\s+if=.*of=/dev/sd",   # Direct disk write
        r">\s*/dev/sd",            # Direct device write
        r"curl.*\|\s*sh",          # Curl piped to shell
        r"wget.*\|\s*sh",          # Wget piped to shell
    ]
    
    # Needs confirmation patterns
    CONFIRMATION_PATTERNS = [
        # Destructive
        r"rm\s+-rf?\s+",
        r"rmdir\s+",
        r"del\s+",
        r"rm\s+",  # Any rm
        # Network
        r"nc\s+",
        r"netcat\s+",
        r"nmap\s+",
        r"ssh\s+",
        r"scp\s+",
        r"ftp\s+",
        # System
        r"chmod\s+777",
        r"chown\s+",
        r"kill\s+-9",
        r"pkill\s+",
        r"reboot",
        r"shutdown",
        r"init\s+",
        # Filesystem
        r"mkfs",
        r"dd\s+",
        r">\s+/proc",
        # Environment
        r"export\s+.*PASSWORD",
        r"export\s+.*KEY",
        r"export\s+.*SECRET",
        # Git dangerous
        r"git\s+push\s+--force",
        r"git\s+push\s+--force-with-lease",
        r"git\s+reset\s+--hard",
    ]
    
    # Safe patterns - auto-allow
    SAFE_PATTERNS = [
        r"^ls$",
        r"ls\s",
        r"^cat$",
        r"cat\s",
        r"grep\s",
        r"find\s",
        r"git\s+(status|log|diff|show|branch)",
        r"git\s+(clone|pull|fetch)",
        r"pwd",
        r"echo\s",
        r"head\s",
        r"tail\s",
        r"wc\s",
        r"sort\s",
        r"uniq\s",
        r"npm\s+(install|run|test|build)",
        r"pip\s+(install|list|show)",
        r"python\s+",
        r"node\s+",
        r"go\s+(run|build|test)",
        r"cargo\s+(build|run|test)",
        r"make\s+",
        r"docker\s+(ps|images|logs)",
    ]

    def __init__(self):
        self._blocked_re = [re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS]
        self._confirm_re = [re.compile(p, re.IGNORECASE) for p in self.CONFIRMATION_PATTERNS]
        self._safe_re = [re.compile(p, re.IGNORECASE) for p in self.SAFE_PATTERNS]

    def classify(self, command: str) -> CommandClassification:
        """Classify a shell command."""
        command = command.strip()
        
        # Check blocked
        for pattern, regex in zip(self.BLOCKED_PATTERNS, self._blocked_re):
            if regex.search(command):
                return CommandClassification(
                    category=CommandCategory.BLOCKED,
                    confidence=1.0,
                    reasons=[f"Matched blocked pattern: {pattern}"],
                    matched_pattern=pattern
                )
        
        # Check safe
        for pattern, regex in zip(self.SAFE_PATTERNS, self._safe_re):
            if regex.search(command):
                return CommandClassification(
                    category=CommandCategory.SAFE,
                    confidence=0.9,
                    reasons=[f"Matched safe pattern: {pattern}"],
                    matched_pattern=pattern
                )
        
        # Check confirmation
        for pattern, regex in zip(self.CONFIRMATION_PATTERNS, self._confirm_re):
            if regex.search(command):
                return CommandClassification(
                    category=CommandCategory.NEEDS_CONFIRMATION,
                    confidence=0.8,
                    reasons=[f"Matched confirmation pattern: {pattern}"],
                    matched_pattern=pattern
                )
        
        # Default: needs confirmation
        return CommandClassification(
            category=CommandCategory.NEEDS_CONFIRMATION,
            confidence=0.5,
            reasons=["Unknown command - requires user confirmation"]
        )


class AgentsMDLoader:
    """Load and enforce AGENTS.md rules (Open-SWE pattern)."""
    
    def __init__(self):
        self.rules: Dict[str, Any] = {}
        self.tool_restrictions: Dict[str, bool] = {}  # tool -> allowed
        self.required_checks: List[str] = []
        
    def load_from_file(self, path: str) -> bool:
        """Load AGENTS.md from file."""
        agents_file = Path(path)
        
        # Check multiple locations
        possible_paths = [
            agents_file,
            agents_file.parent / "AGENTS.md",
            Path.cwd() / "AGENTS.md",
            Path.cwd().parent / "AGENTS.md",
        ]
        
        for file_path in possible_paths:
            if file_path.exists():
                content = file_path.read_text()
                self._parse_agents_md(content)
                logger.info(f"Loaded AGENTS.md from {file_path}")
                return True
        
        return False
    
    def _parse_agents_md(self, content: str) -> None:
        """Parse AGENTS.md content into rules."""
        lines = content.split("\n")
        
        current_section = ""
        for line in lines:
            line = line.strip()
            
            # Section headers
            if line.startswith("#"):
                current_section = line.replace("#", "").strip().lower()
                continue
            
            # Skip empty lines and comments
            if not line or line.startswith("//") or line.startswith("#"):
                continue
            
            # Parse sections
            if "tool" in current_section or "allowed" in current_section:
                # Tool restrictions: - tool_name or + tool_name
                if line.startswith(("+", "-")):
                    enabled = line.startswith("+")
                    tool_name = line[1:].strip()
                    self.tool_restrictions[tool_name] = enabled
                    
            elif "check" in current_section or "verify" in current_section:
                # Required checks before action
                if line.startswith("-") or line.startswith("*"):
                    check = line.lstrip("-* ").strip()
                    if check:
                        self.required_checks.append(check)
                        
            elif "rule" in current_section or "limit" in current_section:
                # General rules
                self.rules[current_section] = self.rules.get(current_section, [])
                self.rules[current_section].append(line)
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if tool is allowed by AGENTS.md."""
        if not self.tool_restrictions:
            return True  # No restrictions
        return self.tool_restrictions.get(tool_name, True)
    
    def get_required_checks(self) -> List[str]:
        """Get required checks before execution."""
        return self.required_checks.copy()
    
    def get_rules(self, section: str) -> List[str]:
        """Get rules for a section."""
        return self.rules.get(section, [])
    
    def to_context(self) -> str:
        """Convert rules to context for LLM."""
        if not self.tool_restrictions and not self.required_checks:
            return ""
        
        parts = []
        
        if self.tool_restrictions:
            parts.append("## AGENTS.md Tool Restrictions")
            for tool, allowed in self.tool_restrictions.items():
                parts.append(f"- {'+' if allowed else '-'}{tool}")
        
        if self.required_checks:
            parts.append("\n## Required Checks")
            for check in self.required_checks:
                parts.append(f"- {check}")
        
        return "\n".join(parts)


class PermissionClassifier:
    """Unified permission system with classifier + AGENTS.md."""
    
    def __init__(self):
        self.classifier = CommandClassifier()
        self.trust_gradient = TrustGradient()
        self.agents_md = AgentsMDLoader()
        self._permission_mode = "auto"  # auto, ask, bypass
        
    def set_permission_mode(self, mode: str) -> None:
        """Set permission mode: auto, ask, bypass."""
        self._permission_mode = mode
        
    def set_agents_md_path(self, path: str) -> None:
        """Set path to AGENTS.md."""
        self.agents_md.load_from_file(path)
    
    def check_command(self, command: str) -> CommandClassification:
        """Check a shell command."""
        return self.classifier.classify(command)
    
    def should_allow(
        self,
        command: Optional[str] = None,
        tool_name: Optional[str] = None,
        trust_level: TrustLevel = TrustLevel.BASIC
    ) -> tuple[bool, str]:
        """Determine if operation should be allowed."""
        
        # Bypass mode = allow all
        if self._permission_mode == "bypass":
            return True, "bypass_mode"
        
        # Ask mode = always ask
        if self._permission_mode == "ask":
            return False, "ask_mode"
        
        # Check tool in AGENTS.md
        if tool_name and not self.agents_md.is_tool_allowed(tool_name):
            return False, f"blocked_by_agents_md"
        
        # Check command safety
        if command:
            classification = self.classifier.classify(command)
            
            if classification.category == CommandCategory.BLOCKED:
                return False, f"blocked: {classification.reasons[0]}"
            
            if classification.category == CommandCategory.SAFE:
                # Check if learned to auto-approve
                pattern = classification.matched_pattern or command[:50]
                if self.trust_gradient.should_auto_approve(pattern):
                    return True, "auto_approved_from_learned"
                return True, f"safe: {classification.matched_pattern}"
            
            # Needs confirmation
            return False, f"needs_confirmation: {classification.reasons[0]}"
        
        # Default allow
        return True, "default"
    
    def record_feedback(self, accepted: bool, pattern: str) -> None:
        """Record user feedback for learning."""
        if accepted:
            self.trust_gradient.record_acceptance(pattern)
        else:
            self.trust_gradient.record_rejection(pattern)
    
    def record_tool_result(self, tool: str, success: bool) -> None:
        """Record tool execution result."""
        self.trust_gradient.record_tool_result(tool, success)
    
    def save_state(self, path: str) -> None:
        """Save trust gradient to file."""
        state = {
            "accepted_patterns": self.trust_gradient.accepted_patterns,
            "rejected_patterns": self.trust_gradient.rejected_patterns,
            "tool_success_rates": {
                k: v for k, v in self.trust_gradient.tool_success_rates.items()
            },
            "last_updated": self.trust_gradient.last_updated.isoformat(),
        }
        Path(path).write_text(json.dumps(state, indent=2))
    
    def load_state(self, path: str) -> None:
        """Load trust gradient from file."""
        if not Path(path).exists():
            return
        try:
            state = json.loads(Path(path).read_text())
            self.trust_gradient.accepted_patterns = state.get("accepted_patterns", {})
            self.trust_gradient.rejected_patterns = state.get("rejected_patterns", {})
            self.trust_gradient.tool_success_rates = state.get("tool_success_rates", {})
            last_updated = state.get("last_updated")
            if last_updated:
                self.trust_gradient.last_updated = datetime.fromisoformat(last_updated)
        except Exception as e:
            logger.warning(f"Failed to load trust gradient: {e}")


# Global permission classifier
_permission_classifier: Optional[PermissionClassifier] = None


def get_permission_classifier() -> PermissionClassifier:
    """Get global permission classifier."""
    global _permission_classifier
    if _permission_classifier is None:
        _permission_classifier = PermissionClassifier()
    return _permission_classifier


# === Enhanced Trust Layer (UOSA Phase 4) ===

import asyncio
from dataclasses import dataclass
from typing import Set

@dataclass
class SecurityRule:
    """A security rule for the trust layer."""
    id: str
    name: str
    description: str
    pattern: str
    action: str
    severity: str


@dataclass
class SecurityCheck:
    """Result of a security check."""
    passed: bool
    rule_id: str = ""
    message: str = ""
    severity: str = "low"


class EnhancedTrustLayer:
    """Enhanced trust layer for UOSA - command validation and package scanning."""
    
    def __init__(self):
        self._rules = self._load_rules()
        self._stats = {
            "commands_checked": 0,
            "commands_blocked": 0,
            "packages_checked": 0,
            "packages_blocked": 0
        }
        # Load known vulnerable packages
        self._vulnerable = {"pyyaml<5.4", "django<3.2.10", "flask<2.0.1"}
    
    def _load_rules(self):
        import re
        return [
            ("no_root_delete", r"rm\s+-rf\s+/", "deny", "critical"),
            ("no_device_write", r">\s*/dev/", "deny", "high"),
            ("no_curl_pipe", r"curl.*\|\s*sh", "deny", "high"),
            ("warn_sudo", r"sudo\s+", "warn", "medium"),
        ]
    
    async def check_command(self, command: str) -> dict:
        """Check command against security rules."""
        self._stats["commands_checked"] += 1
        
        for rule_id, pattern, action, severity in self._rules:
            import re
            if re.search(pattern, command):
                if action == "deny":
                    self._stats["commands_blocked"] += 1
                    return {"allowed": False, "message": f"Blocked: {rule_id}", "severity": severity}
                elif action == "warn":
                    return {"allowed": True, "message": f"Warning: {rule_id}", "severity": severity}
        
        return {"allowed": True}
    
    async def check_package(self, package: str, version: str = None) -> dict:
        """Check package for vulnerabilities."""
        self._stats["packages_checked"] += 1
        
        check_key = f"{package}<{version}" if version else package
        if check_key in self._vulnerable:
            self._stats["packages_blocked"] += 1
            return {"allowed": False, "message": f"Vulnerable: {package}"}
        
        return {"allowed": True}
    
    def get_stats(self):
        return self._stats


_enhanced_trust: EnhancedTrustLayer = None

def get_enhanced_trust_layer() -> EnhancedTrustLayer:
    global _enhanced_trust
    if _enhanced_trust is None:
        _enhanced_trust = EnhancedTrustLayer()
    return _enhanced_trust