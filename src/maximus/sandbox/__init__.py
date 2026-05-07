"""Sandbox management for Maximus.ai."""

from __future__ import annotations

import logging
from typing import Dict, Optional

from maximus.models import AgentConfig

logger = logging.getLogger(__name__)


class Sandbox:
    """Base sandbox interface."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

    def allows_tool(self, tool_name: str) -> bool:
        """Check if tool is allowed in this sandbox."""
        return True

    def cleanup(self) -> None:
        """Cleanup sandbox resources."""
        pass


class LocalSandbox(Sandbox):
    """Local filesystem sandbox (no isolation)."""

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        self.workdir = self.config.workdir

    def allows_tool(self, tool_name: str) -> bool:
        # All local tools allowed
        return True


def get_sandbox(config: Optional[AgentConfig] = None) -> Sandbox:
    """Factory function to get sandbox instance."""
    return LocalSandbox(config)
