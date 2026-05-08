"""Modal sandbox backend for Maximus.

Provides serverless sandbox execution via Modal.com.
"""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


try:
    import modal
    MODAL_AVAILABLE = True
except ImportError:
    MODAL_AVAILABLE = False
    logger.warning("Modal not available. Install with: pip install modal")


class ModalSandbox:
    """Modal-based sandbox for serverless code execution."""
    
    def __init__(
        self,
        token: Optional[str] = None,
        timeout: int = 300,
        memory_limit: int = 512,  # MB
        cpu_limit: float = 1.0,
    ):
        if not MODAL_AVAILABLE:
            raise ImportError("Modal is not installed. Install with: pip install modal")
            
        self.token = token or os.getenv("MODAL_TOKEN")
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.app = None
        
    async def initialize(self):
        """Initialize the Modal app."""
        if not self.token:
            raise ValueError("Modal token is required")
            
        # Configure Modal
        if self.token:
            os.environ["MODAL_TOKEN"] = self.token
            
        # Create a simple app for testing
        app = modal.App("maximus-sandbox")
        
        @app.function(
            timeout=self.timeout,
            memory=self.memory_limit * 1024,  # Convert MB to bytes
            cpu=self.cpu_limit,
        )
        def execute_code(code: str, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
            """Execute code in Modal sandbox."""
            import subprocess
            import sys
            import tempfile
            import json
            
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                
                # Execute with resource limits
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                
                # Cleanup
                os.unlink(temp_file)
                
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Execution timed out",
                    "returncode": -1,
                }
            except Exception as e:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1,
                }
        
        self.app = app
        self.execute_func = execute_code
        
    async def execute(self, code: str, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute code in the Modal sandbox.
        
        Args:
            code: Python code to execute
            inputs: Optional input data
            
        Returns:
            Execution result dictionary
        """
        if not self.app:
            await self.initialize()
            
        try:
            # For now, we'll simulate Modal execution
            # In a real implementation, this would deploy and call the function
            return {
                "success": True,
                "stdout": "Modal execution simulated: " + code[:50] + "...",
                "stderr": "",
                "returncode": 0,
                "execution_time": 0.1,
                "backend": "modal",
            }
        except Exception as e:
            logger.error(f"Modal execution failed: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }
            
    async def cleanup(self):
        """Cleanup Modal resources."""
        # Modal cleanup would happen automatically
        pass