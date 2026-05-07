"""Security context for Maximus.ai."""

from __future__ import annotations

from typing import Dict, Any, Optional

from maximus.models import TrustLevel, PermissionLevel


class SecurityContext:
    """Security context for tool execution."""

    def __init__(
        self,
        trust_level: TrustLevel = TrustLevel.BASIC,
        sandbox: Any = None,
        allow_external: bool = False,
    ):
        self.trust_level = trust_level
        self.sandbox = sandbox
        self.allow_external = allow_external
        self.audit_log: list[Dict[str, Any]] = []

    def has_permission(self, level: PermissionLevel) -> bool:
        """Check if context has permission for given level."""
        # Map trust level to allowed permission levels
        trust_map = {
            TrustLevel.UNTRUSTED: [PermissionLevel.SAFE],
            TrustLevel.BASIC: [PermissionLevel.SAFE, PermissionLevel.WRITE],
            TrustLevel.VERIFIED: [PermissionLevel.SAFE, PermissionLevel.WRITE],
            TrustLevel.PRIVILEGED: [PermissionLevel.SAFE, PermissionLevel.WRITE, PermissionLevel.DANGEROUS],
        }

        allowed = trust_map.get(self.trust_level, [])
        return level in allowed

    def log_action(self, tool: str, args: Dict, result: Dict) -> None:
        """Log an action for audit trail."""
        self.audit_log.append({
            "tool": tool,
            "args": args,
            "success": result.get("success", False),
            "timestamp": self._now(),
        })

    def _now(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat()
