"""Sandbox integration for Maximus.ai - Nexus Docker pattern.

Provides safe, isolated execution environments for agent operations.
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DockerSandbox:
    """Docker-based sandbox for safe code execution."""
    
    def __init__(
        self,
        image: str = "python:3.11-slim",
        workspace_path: str = "workspace",
        network_enabled: bool = False,
        memory_limit: str = "512m",
        cpu_limit: str = "1.0",
    ):
        self.image = image
        self.workspace_path = Path(workspace_path)
        self.network_enabled = network_enabled
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.container_id = None
        self.audit_log = []
        
        self._ensure_workspace()
        self._check_docker()
    
    def _ensure_workspace(self):
        """Create workspace directory if it doesn't exist."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
    
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info(f"Docker available: {result.stdout.strip()}")
                return True
            return False
        except FileNotFoundError:
            logger.warning("Docker not found. Sandbox will be disabled.")
            return False
        except Exception as e:
            logger.error(f"Docker check failed: {e}")
            return False
    
    def start(self) -> Dict[str, Any]:
        """Start a new sandbox container."""
        if not self._check_docker():
            return {
                "status": "error",
                "error": "Docker not available",
            }
        
        try:
            # Build docker command
            cmd = [
                "docker", "run",
                "-d",  # Detached mode
                "--rm",  # Auto-remove on stop
                "-v", f"{self.workspace_path.absolute()}:/workspace",
                "--memory", self.memory_limit,
                "--cpus", self.cpu_limit,
            ]
            
            if not self.network_enabled:
                cmd.extend(["--network", "none"])
            
            cmd.extend([self.image, "tail", "-f", "/dev/null"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode == 0:
                self.container_id = result.stdout.strip()
                self._log("start", f"Container: {self.container_id}")
                return {
                    "status": "success",
                    "container_id": self.container_id,
                    "workspace": str(self.workspace_path.absolute()),
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Timeout starting container",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    def execute(self, command: str, timeout: int = 120) -> Dict[str, Any]:
        """Execute a command in the sandbox."""
        if not self.container_id:
            # Run directly without sandbox
            return self._execute_direct(command, timeout)
        
        self._log("execute", command)
        
        try:
            cmd = [
                "docker", "exec",
                self.container_id,
                "bash", "-c", command,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace_path),
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            self._log("result", output or error)
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": output,
                "error": error,
                "returncode": result.returncode,
            }
            
        except subprocess.TimeoutExpired:
            self._log("timeout", command)
            return {
                "status": "error",
                "error": f"Command timed out after {timeout}s",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    def _execute_direct(self, command: str, timeout: int = 120) -> Dict[str, Any]:
        """Execute directly without sandbox (fallback)."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace_path),
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
                "returncode": result.returncode,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop the sandbox container."""
        if not self.container_id:
            return {"status": "success", "message": "No container running"}
        
        try:
            result = subprocess.run(
                ["docker", "stop", self.container_id],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            self._log("stop", self.container_id)
            self.container_id = None
            
            return {
                "status": "success",
                "message": "Container stopped",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    def _log(self, action: str, details: str):
        """Add entry to audit log."""
        from datetime import datetime
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
        })
    
    def get_audit_log(self) -> list:
        """Get the audit log."""
        return self.audit_log
    
    def is_running(self) -> bool:
        """Check if sandbox is running."""
        if not self.container_id:
            return False
        
        try:
            result = subprocess.run(
                ["docker", "ps", "-q", "--filter", f"id={self.container_id}"],
                capture_output=True,
                text=True,
            )
            return self.container_id in result.stdout
        except Exception:
            return False
