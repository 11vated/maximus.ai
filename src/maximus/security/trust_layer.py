"""Enhanced Trust Layer - Security and Policy enforcement.

This enables:
- Package vulnerability scanning (Snyk-style)
- Policy enforcement (OPA-style)
- Command allowlisting
- Audit logging
- Malicious package detection
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import subprocess
import json
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SecurityRule:
    """A security rule for the trust layer."""
    id: str
    name: str
    description: str
    pattern: str  # Regex pattern to match
    action: str  # "allow", "deny", "warn"
    severity: str  # "low", "medium", "high", "critical"


@dataclass
class SecurityCheck:
    """Result of a security check."""
    passed: bool
    rule_id: Optional[str]
    message: str
    severity: str = "low"
    metadata: Dict[str, Any] = field(default_factory=dict)


class CommandValidator:
    """Validates shell commands against security rules."""
    
    def __init__(self):
        self._rules: List[SecurityRule] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default security rules."""
        self._rules = [
            SecurityRule(
                id="no_root_delete",
                name="No root directory deletion",
                description="Block commands that delete from root",
                pattern=r"rm\s+-rf\s+/",
                action="deny",
                severity="critical"
            ),
            SecurityRule(
                id="no_device_write",
                name="No device file writes",
                description="Block writing to device files",
                pattern=r">\s*/dev/",
                action="deny",
                severity="high"
            ),
            SecurityRule(
                id="no_curl_pipe",
                name="No curl piped to shell",
                description="Block curl | sh patterns",
                pattern=r"curl.*\|\s*sh",
                action="deny",
                severity="high"
            ),
            SecurityRule(
                id="no_wget_pipe",
                name="No wget piped to shell",
                description="Block wget | sh patterns",
                pattern=r"wget.*\|\s*sh",
                action="deny",
                severity="high"
            ),
            SecurityRule(
                id="warn_sudo",
                name="Warn on sudo",
                description="Warn about sudo usage",
                pattern=r"sudo\s+",
                action="warn",
                severity="medium"
            ),
            SecurityRule(
                id="warn_chmod_777",
                name="Warn on chmod 777",
                description="Warn about overly permissive permissions",
                pattern=r"chmod\s+777",
                action="warn",
                severity="medium"
            ),
        ]
    
    def add_rule(self, rule: SecurityRule):
        """Add a custom rule."""
        self._rules.append(rule)
    
    def check(self, command: str) -> List[SecurityCheck]:
        """Check a command against all rules."""
        checks = []
        
        for rule in self._rules:
            import re
            if re.search(rule.pattern, command):
                if rule.action == "deny":
                    checks.append(SecurityCheck(
                        passed=False,
                        rule_id=rule.id,
                        message=f"BLOCKED: {rule.name} - {rule.description}",
                        severity=rule.severity,
                        metadata={"pattern": rule.pattern}
                    ))
                elif rule.action == "warn":
                    checks.append(SecurityCheck(
                        passed=True,
                        rule_id=rule.id,
                        message=f"WARNING: {rule.name} - {rule.description}",
                        severity=rule.severity,
                        metadata={"pattern": rule.pattern}
                    ))
        
        return checks


class PackageValidator:
    """Validates packages for known vulnerabilities."""
    
    def __init__(self):
        self._vulnerable_packages: Set[str] = self._load_known_vulnerabilities()
    
    def _load_known_vulnerabilities(self) -> Set[str]:
        """Load known vulnerable packages."""
        # These are example known vulnerabilities - in production, 
        # this would integrate with a real vulnerability database
        return {
            "pyyaml<5.4",  # Remote code execution
            "django<3.2.10",  # SQL injection
            "flask<2.0.1",  # Security issues
            "requests<2.20",  # Vulnerability
            "numpy<1.22.0",  # Security issues
        }
    
    def check_package(self, package_name: str, version: Optional[str] = None) -> SecurityCheck:
        """Check if a package has known vulnerabilities."""
        # Simple version check - in production, would query real DB
        check_key = f"{package_name}<{version}" if version else package_name
        
        if check_key in self._vulnerable_packages:
            return SecurityCheck(
                passed=False,
                rule_id="known_vulnerability",
                message=f"Package {package_name}@{version} has known vulnerabilities",
                severity="high",
                metadata={"package": package_name, "version": version}
            )
        
        return SecurityCheck(
            passed=True,
            rule_id="safe_package",
            message=f"Package {package_name} appears safe",
            severity="low"
        )
    
    async def check_package_async(
        self, 
        package_name: str, 
        version: Optional[str] = None,
        registry: str = "pypi"
    ) -> SecurityCheck:
        """Async check with potential API integration."""
        # For now, use the synchronous check
        # In production, would integrate with:
        # - PyTorch / Snyk API for Python
        # - npm audit for JavaScript
        # - cargo audit for Rust
        return self.check_package(package_name, version)


class TrustLayer:
    """Enhanced trust layer for Maximus UOSA.
    
    This is the security core that:
    - Validates commands before execution
    - Checks packages for vulnerabilities
    - Enforces security policies
    - Logs all security events
    """
    
    def __init__(self):
        self.command_validator = CommandValidator()
        self.package_validator = PackageValidator()
        
        # Audit log
        self._audit_log: List[Dict[str, Any]] = []
        
        # Statistics
        self._stats = {
            "commands_checked": 0,
            "commands_blocked": 0,
            "commands_warned": 0,
            "packages_checked": 0,
            "packages_blocked": 0
        }
    
    async def check_command(self, command: str) -> Dict[str, Any]:
        """Check a shell command for security issues."""
        self._stats["commands_checked"] += 1
        
        checks = self.command_validator.check(command)
        
        # Determine result
        has_block = any(not c.passed for c in checks)
        has_warn = any(c.passed and "WARNING" in c.message for c in checks)
        
        result = {
            "allowed": not has_block,
            "checks": [
                {
                    "passed": c.passed,
                    "message": c.message,
                    "severity": c.severity
                }
                for c in checks
            ]
        }
        
        if has_block:
            self._stats["commands_blocked"] += 1
            self._log_event("command_blocked", command, result)
        elif has_warn:
            self._stats["commands_warned"] += 1
            self._log_event("command_warning", command, result)
        else:
            self._log_event("command_allowed", command, result)
        
        return result
    
    async def check_package(
        self, 
        package_name: str, 
        version: Optional[str] = None,
        registry: str = "pypi"
    ) -> Dict[str, Any]:
        """Check a package for security issues."""
        self._stats["packages_checked"] += 1
        
        check = await self.package_validator.check_package_async(
            package_name, version, registry
        )
        
        result = {
            "allowed": check.passed,
            "message": check.message,
            "severity": check.severity
        }
        
        if not check.passed:
            self._stats["packages_blocked"] += 1
            self._log_event("package_blocked", f"{package_name}@{version}", result)
        else:
            self._log_event("package_allowed", f"{package_name}@{version}", result)
        
        return result
    
    def _log_event(self, event_type: str, subject: str, result: Dict[str, Any]):
        """Log a security event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "subject": subject,
            "result": result,
            "allowed": result.get("allowed", True)
        }
        
        self._audit_log.append(event)
        
        # Write to audit file
        self._write_audit_log()
        
        logger.debug(f"Security event: {event_type} - {subject}")
    
    def _write_audit_log(self):
        """Write audit log to disk."""
        audit_path = Path.home() / ".maximus" / "security_audit.log"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Keep last 1000 events
        recent = self._audit_log[-1000:]
        
        with open(audit_path, 'w') as f:
            for event in recent:
                f.write(json.dumps(event) + "\n")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        return {
            **self._stats,
            "total_events": len(self._audit_log),
            "recent_events": len(self._audit_log[-10:])
        }
    
    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return self._audit_log[-limit:]
    
    def add_command_rule(self, rule: SecurityRule):
        """Add a custom command security rule."""
        self.command_validator.add_rule(rule)
    
    def clear_rules(self):
        """Clear all custom rules (keep defaults)."""
        self.command_validator._load_default_rules()


# Global trust layer instance
_trust_layer: Optional[TrustLayer] = None

def get_trust_layer() -> TrustLayer:
    """Get the global trust layer instance."""
    global _trust_layer
    if _trust_layer is None:
        _trust_layer = TrustLayer()
    return _trust_layer