"""Tests for Sandbox functionality."""
import asyncio
import pytest
from maximus.sandbox.factory import get_sandbox, SandboxFactory, SandboxConfig, SandboxType


class TestSandboxFactory:
    """Tests for sandbox factory."""

    def test_get_sandbox_default(self):
        """Test getting default sandbox."""
        sandbox = get_sandbox()
        assert sandbox is not None

    def test_sandbox_config_defaults(self):
        """Test sandbox config defaults."""
        config = SandboxConfig()
        assert config.sandbox_type == SandboxType.DOCKER
        assert config.timeout == 300
        assert config.network_enabled is True

    def test_sandbox_config_custom(self):
        """Test custom sandbox config."""
        config = SandboxConfig(
            sandbox_type=SandboxType.LOCAL,
            timeout=60,
            memory_limit="1g",
            network_enabled=False,
        )
        assert config.sandbox_type == SandboxType.LOCAL
        assert config.timeout == 60
        assert config.memory_limit == "1g"
        assert config.network_enabled is False


class TestSandboxTypes:
    """Tests for sandbox type enumeration."""

    def test_all_types_exist(self):
        """Test all sandbox types are defined."""
        assert SandboxType.LOCAL == "local"
        assert SandboxType.DOCKER == "docker"
        assert SandboxType.LANGSMITH == "langsmith"
        assert SandboxType.MODAL == "modal"
        assert SandboxType.DAYTONA == "daytona"

    def test_enum_count(self):
        """Test we have expected number of types."""
        assert len(SandboxType) >= 4


class TestSandboxInterface:
    """Tests for sandbox interface contract."""

    def test_interface_has_required_methods(self):
        """Test the ABC defines required methods."""
        from maximus.sandbox.interface import SandboxBackend
        assert hasattr(SandboxBackend, 'initialize')
        assert hasattr(SandboxBackend, 'execute')
        assert hasattr(SandboxBackend, 'cleanup')