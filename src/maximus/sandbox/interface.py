"""Sandbox interface for Maximus.

Defines the common interface for all sandbox backends.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SandboxBackend(ABC):
    """Abstract base class for sandbox backends."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the sandbox backend."""
        pass
    
    @abstractmethod
    async def execute(self, code: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute code in the sandbox.
        
        Args:
            code: Python code to execute
            inputs: Optional input data
            
        Returns:
            Execution result with success, stdout, stderr, etc.
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup sandbox resources."""
        pass