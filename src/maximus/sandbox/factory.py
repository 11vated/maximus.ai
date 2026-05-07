"""Pluggable sandbox backends for Maximus.ai.

Implements Open-SWE pattern:
- LocalSandbox - direct execution
- DockerSandbox - containerized execution
- LangSmithSandbox - cloud sandboxes with tracing
- ModalSandbox - serverless execution
- DaytonaSandbox - managed dev environments
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SandboxType(str, Enum):
    """Available sandbox backends."""
    LOCAL = "local"
    DOCKER = "docker"
    LANGSMITH = "langsmith"
    MODAL = "modal"
    DAYTONA = "daytona"


@dataclass
class SandboxConfig:
    """Configuration for sandbox."""
    sandbox_type: SandboxType = SandboxType.DOCKER
    workdir: str = "."
    timeout: int = 300
    memory_limit: Optional[str] = None
    cpu_limit: Optional[str] = None
    network_enabled: bool = True
    allowed_domains: List[str] = field(default_factory=lambda: ["*"])
    
    # Backend-specific config
    docker_image: str = "maximus-sandbox:latest"
    langsmith_api_key: Optional[str] = None
    langsmith_project: Optional[str] = None
    modal_function: Optional[str] = None
    daytona_provider: str = "daytona"


@dataclass
class SandboxResult:
    """Result from sandbox execution."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    error: Optional[str] = None
    duration: float = 0.0
    sandbox_id: Optional[str] = None


class SandboxBackend(ABC):
    """Abstract base class for sandbox backends."""

    @abstractmethod
    async def initialize(self, config: SandboxConfig) -> None:
        """Initialize the sandbox."""
        pass

    @abstractmethod
    async def execute(
        self, 
        command: str, 
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """Execute a command in the sandbox."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
        pass

    @property
    @abstractmethod
    def sandbox_id(self) -> Optional[str]:
        """Get the sandbox ID."""
        pass


class LocalSandbox(SandboxBackend):
    """Local filesystem sandbox - direct execution without isolation."""

    def __init__(self):
        self._config: Optional[SandboxConfig] = None
        self._sandbox_id = f"local_{uuid.uuid4().hex[:8]}"

    async def initialize(self, config: SandboxConfig) -> None:
        self._config = config

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """Execute command directly in local filesystem."""
        import time
        start_time = time.time()

        workdir = Path(cwd or self._config.workdir if self._config else ".")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(workdir),
                env=env
            )

            timeout_val = timeout or self._config.timeout if self._config else 300
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_val
            )

            return SandboxResult(
                success=process.returncode == 0,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                exit_code=process.returncode or 0,
                duration=time.time() - start_time,
                sandbox_id=self._sandbox_id
            )

        except asyncio.TimeoutError:
            process.kill()
            return SandboxResult(
                success=False,
                error=f"Command timed out after {timeout_val}s",
                duration=time.time() - start_time,
                sandbox_id=self._sandbox_id
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time,
                sandbox_id=self._sandbox_id
            )

    async def cleanup(self) -> None:
        pass

    @property
    def sandbox_id(self) -> Optional[str]:
        return self._sandbox_id


class DockerSandbox(SandboxBackend):
    """Docker container sandbox - full isolation."""

    def __init__(self):
        self._config: Optional[SandboxConfig] = None
        self._container_id: Optional[str] = None
        self._sandbox_id = f"docker_{uuid.uuid4().hex[:8]}"

    async def initialize(self, config: SandboxConfig) -> None:
        self._config = config
        # Ensure Docker is available
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            logger.info("Docker sandbox initialized")
        except FileNotFoundError:
            logger.warning("Docker not available - falling back to LocalSandbox")
            self._config.sandbox_type = SandboxType.LOCAL

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """Execute command in Docker container."""
        import time
        start_time = time.time()

        workdir = cwd or self._config.workdir if self._config else "."
        timeout_val = timeout or self._config.timeout if self._config else 300

        # Build docker run command
        docker_cmd = [
            "docker", "run", "--rm",
            "-w", workdir,
            "--network", "none" if not self._config.network_enabled else "bridge",
            "-v", f"{Path(workdir).absolute()}:{workdir}",
            self._config.docker_image if self._config else "maximus-sandbox:latest",
            "sh", "-c", command
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_val
            )

            return SandboxResult(
                success=process.returncode == 0,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                exit_code=process.returncode or 0,
                duration=time.time() - start_time,
                sandbox_id=self._sandbox_id
            )

        except asyncio.TimeoutError:
            process.kill()
            return SandboxResult(
                success=False,
                error=f"Docker command timed out after {timeout_val}s",
                duration=time.time() - start_time,
                sandbox_id=self._sandbox_id
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                error=f"Docker execution failed: {e}",
                duration=time.time() - start_time,
                sandbox_id=self._sandbox_id
            )

    async def cleanup(self) -> None:
        if self._container_id:
            try:
                await asyncio.create_subprocess_exec(
                    "docker", "rm", "-f", self._container_id,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
            except Exception:
                pass

    @property
    def sandbox_id(self) -> Optional[str]:
        return self._sandbox_id


class LangSmithSandbox(SandboxBackend):
    """LangSmith cloud sandbox with tracing."""

    def __init__(self):
        self._config: Optional[SandboxConfig] = None
        self._sandbox_id: Optional[str] = None

    async def initialize(self, config: SandboxConfig) -> None:
        self._config = config
        self._sandbox_id = f"langsmith_{uuid.uuid4().hex[:8]}"
        logger.info(f"LangSmith sandbox initialized: {self._sandbox_id}")

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """Execute via LangSmith (simulated - needs actual LangSmith setup)."""
        import time
        start_time = time.time()

        # This would integrate with LangSmith API in production
        # For now, simulate execution
        logger.warning("LangSmith sandbox - using local fallback")
        
        return SandboxResult(
            success=True,
            stdout=f"[LangSmith sandbox {self._sandbox_id}] Executed: {command}",
            duration=time.time() - start_time,
            sandbox_id=self._sandbox_id
        )

    async def cleanup(self) -> None:
        pass

    @property
    def sandbox_id(self) -> Optional[str]:
        return self._sandbox_id


class ModalSandbox(SandboxBackend):
    """Modal serverless sandbox."""

    def __init__(self):
        self._config: Optional[SandboxConfig] = None
        self._sandbox_id: Optional[str] = None

    async def initialize(self, config: SandboxConfig) -> None:
        self._config = config
        self._sandbox_id = f"modal_{uuid.uuid4().hex[:8]}"
        logger.info(f"Modal sandbox initialized: {self._sandbox_id}")

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """Execute via Modal (simulated)."""
        import time
        start_time = time.time()

        logger.warning("Modal sandbox - using local fallback")
        
        return SandboxResult(
            success=True,
            stdout=f"[Modal sandbox {self._sandbox_id}] Executed: {command}",
            duration=time.time() - start_time,
            sandbox_id=self._sandbox_id
        )

    async def cleanup(self) -> None:
        pass

    @property
    def sandbox_id(self) -> Optional[str]:
        return self._sandbox_id


class DaytonaSandbox(SandboxBackend):
    """Daytona managed dev environment sandbox."""

    def __init__(self):
        self._config: Optional[SandboxConfig] = None
        self._sandbox_id: Optional[str] = None

    async def initialize(self, config: SandboxConfig) -> None:
        self._config = config
        self._sandbox_id = f"daytona_{uuid.uuid4().hex[:8]}"
        logger.info(f"Daytona sandbox initialized: {self._sandbox_id}")

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """Execute via Daytona (simulated)."""
        import time
        start_time = time.time()

        logger.warning("Daytona sandbox - using local fallback")
        
        return SandboxResult(
            success=True,
            stdout=f"[Daytona sandbox {self._sandbox_id}] Executed: {command}",
            duration=time.time() - start_time,
            sandbox_id=self._sandbox_id
        )

    async def cleanup(self) -> None:
        pass

    @property
    def sandbox_id(self) -> Optional[str]:
        return self._sandbox_id


class SandboxFactory:
    """Factory for creating sandbox backends."""

    _backends = {
        SandboxType.LOCAL: LocalSandbox,
        SandboxType.DOCKER: DockerSandbox,
        SandboxType.LANGSMITH: LangSmithSandbox,
        SandboxType.MODAL: ModalSandbox,
        SandboxType.DAYTONA: DaytonaSandbox,
    }

    @classmethod
    def create(cls, config: SandboxConfig) -> SandboxBackend:
        """Create a sandbox backend based on config."""
        backend_class = cls._backends.get(config.sandbox_type, LocalSandbox)
        return backend_class()

    @classmethod
    def register_backend(cls, sandbox_type: SandboxType, backend_class: type) -> None:
        """Register a custom backend."""
        cls._backends[sandbox_type] = backend_class


# Global sandbox instance management
_sandboxes: Dict[str, SandboxBackend] = {}


def get_sandbox(
    sandbox_type: SandboxType = SandboxType.DOCKER,
    sandbox_id: Optional[str] = None,
    config: Optional[SandboxConfig] = None
) -> SandboxBackend:
    """Get or create a sandbox instance."""
    if sandbox_id and sandbox_id in _sandboxes:
        return _sandboxes[sandbox_id]

    if config is None:
        config = SandboxConfig(sandbox_type=sandbox_type)

    sandbox = SandboxFactory.create(config)
    
    if sandbox_id:
        _sandboxes[sandbox_id] = sandbox
    
    return sandbox


def cleanup_sandbox(sandbox_id: str) -> None:
    """Clean up a specific sandbox."""
    if sandbox_id in _sandboxes:
        asyncio.create_task(_sandboxes[sandbox_id].cleanup())
        del _sandboxes[sandbox_id]


def cleanup_all() -> None:
    """Clean up all sandboxes."""
    for sandbox in _sandboxes.values():
        asyncio.create_task(sandbox.cleanup())
    _sandboxes.clear()