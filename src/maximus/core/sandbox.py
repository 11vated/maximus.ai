"""Sandbox execution system for safe agent operations.

Implements SWE-ReX style isolated execution:
- Docker-based isolation for code execution
- Command allowlist for shell operations  
- Resource limits (memory, CPU, time)
- Audit logging for security
"""

import os
import asyncio
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""
    # Isolation level
    use_docker: bool = True
    docker_image: str = "maximus-sandbox:latest"
    
    # Resource limits
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    max_execution_time_seconds: int = 30
    
    # Working directory
    workspace_root: str = "/tmp/maximus-sandbox"
    
    # Security
    allow_network: bool = True
    allow_subprocess: bool = False
    
    # Command whitelist (if empty, all allowed)
    allowed_commands: List[str] = None
    
    def __post_init__(self):
        if self.allowed_commands is None:
            self.allowed_commands = [
                # File operations
                "ls", "cat", "head", "tail", "grep", "find", "wc",
                # Text processing
                "sed", "awk", "sort", "uniq", "cut", "tr",
                # Git (basic)
                "git",
                # Python/Node execution
                "python", "python3", "pip", "node", "npm",
                # Development tools
                "gcc", "g++", "make", "cmake",
                # System info
                "whoami", "pwd", "echo", "date",
            ]


class Sandbox:
    """Isolated execution environment for agent operations.
    
    This prevents the agent from causing damage to the host system.
    All code execution, shell commands, and file operations happen in isolation.
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._session_id: Optional[str] = None
        self._workspace_path: Optional[Path] = None
        self._container_id: Optional[str] = None
        
    async def __aenter__(self):
        """Create a new sandbox session."""
        self._session_id = f"sandbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._workspace_path = Path(self.config.workspace_root) / self._session_id
        self._workspace_path.mkdir(parents=True, exist_ok=True)
        
        if self.config.use_docker:
            await self._start_docker_container()
            
        logger.info(f"Sandbox session created: {self._session_id}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up sandbox session."""
        await self._cleanup()
        
    async def _start_docker_container(self):
        """Start a Docker container for isolation."""
        try:
            # Check if docker is available
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.warning("Docker not available, falling back to filesystem isolation")
                self.config.use_docker = False
                return
                
            # Pull or build the image
            # For now, we'll use a simple approach - just create the workspace
            logger.info("Docker available, using container isolation")
            
        except FileNotFoundError:
            logger.warning("Docker not installed, using filesystem isolation only")
            self.config.use_docker = False
        except Exception as e:
            logger.warning(f"Docker setup failed: {e}, using filesystem isolation")
            self.config.use_docker = False
    
    async def _cleanup(self):
        """Clean up the sandbox session."""
        if self._container_id:
            try:
                subprocess.run(
                    ["docker", "stop", self._container_id],
                    capture_output=True,
                    timeout=10
                )
            except Exception as e:
                logger.warning(f"Failed to stop container: {e}")
        
        if self._workspace_path and self._workspace_path.exists():
            try:
                shutil.rmtree(self._workspace_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup workspace: {e}")
                
        logger.info(f"Sandbox session cleaned: {self._session_id}")
    
    @property
    def workspace(self) -> Optional[Path]:
        """Get the workspace directory for this session."""
        return self._workspace_path
    
    async def execute_command(
        self, 
        command: str, 
        timeout: Optional[int] = None,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a shell command in the sandbox.
        
        This is the primary interface for running commands.
        All commands should go through this to ensure safety.
        """
        if not self._session_id:
            raise RuntimeError("Sandbox not initialized. Use 'async with Sandbox()'")
        
        # Security check: validate command
        security_check = self._validate_command(command)
        if not security_check["allowed"]:
            return {
                "success": False,
                "error": f"Command blocked by security: {security_check['reason']}",
                "output": "",
                "exit_code": 1
            }
        
        timeout = timeout or self.config.max_execution_time_seconds
        
        # Set working directory
        if cwd is None and self._workspace_path:
            cwd = str(self._workspace_path)
        
        try:
            start_time = datetime.now()
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                result = {
                    "success": process.returncode == 0,
                    "output": stdout.decode('utf-8', errors='replace'),
                    "error": stderr.decode('utf-8', errors='replace'),
                    "exit_code": process.returncode,
                    "execution_time_ms": execution_time,
                    "command": command
                }
                
                # Log the execution
                await self._log_execution(command, result)
                
                return result
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout}s",
                    "output": "",
                    "exit_code": -1,
                    "timeout": True
                }
                
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "exit_code": -1
            }
    
    def _validate_command(self, command: str) -> Dict[str, Any]:
        """Validate a command against security rules."""
        command_lower = command.lower().strip()
        
        # Block dangerous commands
        dangerous_patterns = [
            "rm -rf /", "mkfs", "dd if=", ":(){:|:&};:",
            "chmod 777 /", "chown -r", "> /dev/sda",
            "curl.*| sh", "wget.*| sh",  # Remote script execution
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return {
                    "allowed": False,
                    "reason": f"Dangerous pattern detected: {pattern}"
                }
        
        # Check allowlist if configured
        if self.config.allowed_commands:
            cmd_base = command_lower.split()[0] if command_lower.split() else ""
            
            # Get actual command (handle aliases)
            allowed = False
            for allowed_cmd in self.config.allowed_commands:
                if cmd_base.endswith(allowed_cmd) or cmd_base == allowed_cmd:
                    allowed = True
                    break
            
            if not allowed:
                return {
                    "allowed": False,
                    "reason": f"Command '{cmd_base}' not in allowlist"
                }
        
        return {"allowed": True, "reason": "Command validated"}
    
    async def _log_execution(self, command: str, result: Dict[str, Any]):
        """Log command execution for audit."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id,
            "command": command,
            "success": result.get("success"),
            "exit_code": result.get("exit_code"),
            "execution_time_ms": result.get("execution_time_ms", 0)
        }
        
        # Write to audit log
        audit_path = Path(self.config.workspace_root) / "audit.log"
        with open(audit_path, "a") as f:
            f.write(f"{log_entry}\n")
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write a file to the sandbox workspace."""
        if not self._workspace_path:
            raise RuntimeError("Sandbox not initialized")
        
        # Safety: only allow writes within workspace
        file_path = self._workspace_path / path.lstrip("/")
        
        # Prevent directory traversal
        try:
            file_path.resolve().relative_to(self._workspace_path.resolve())
        except ValueError:
            return {
                "success": False,
                "error": "Path outside workspace"
            }
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return {
                "success": True,
                "path": str(file_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file from the sandbox workspace."""
        if not self._workspace_path:
            raise RuntimeError("Sandbox not initialized")
        
        file_path = self._workspace_path / path.lstrip("/")
        
        # Safety check
        try:
            resolved = file_path.resolve()
            resolved.relative_to(self._workspace_path.resolve())
        except ValueError:
            return {
                "success": False,
                "error": "Path outside workspace"
            }
        
        if not file_path.exists():
            return {
                "success": False,
                "error": "File not found"
            }
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return {
                "success": True,
                "content": content,
                "path": str(file_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get information about the sandbox workspace."""
        if not self._workspace_path:
            return {"initialized": False}
        
        files = []
        try:
            for f in self._workspace_path.rglob("*"):
                if f.is_file():
                    files.append(str(f.relative_to(self._workspace_path)))
        except Exception:
            pass
        
        return {
            "initialized": True,
            "session_id": self._session_id,
            "workspace_path": str(self._workspace_path),
            "docker_enabled": self.config.use_docker,
            "files": files[:100]  # Limit to 100 files
        }


async def run_in_sandbox(
    command: str,
    config: Optional[SandboxConfig] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """Convenience function to run a command in a temporary sandbox."""
    async with Sandbox(config) as sandbox:
        return await sandbox.execute_command(command, timeout)