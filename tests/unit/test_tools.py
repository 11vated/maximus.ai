"""Tests for Maximus.ai tools."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from maximus.tools.builtin import ExecuteShellTool, ReadFileTool, WriteFileTool, GrepTool, LsTool
from maximus.tools.base import ToolMetadata


def test_tool_metadata():
    """Test tool metadata creation."""
    tool = ExecuteShellTool()
    assert tool.metadata.name == "execute_shell"
    assert tool.metadata.permission_level == "dangerous"
    assert tool.metadata.local_only is True


@pytest.mark.asyncio
async def test_read_file_missing_path():
    """Test read_file with missing path."""
    tool = ReadFileTool()
    result = await tool.execute({}, {"workdir": "."})
    assert result["success"] is False
    assert "Missing" in result["error"]


@pytest.mark.asyncio
async def test_write_file_missing_path():
    """Test write_file with missing path."""
    tool = WriteFileTool()
    result = await tool.execute({"content": "test"}, {"workdir": "."})
    assert result["success"] is False
    assert "Missing" in result["error"]


@pytest.mark.asyncio
async def test_ls_tool():
    """Test ls tool."""
    tool = LsTool()
    result = await tool.execute({}, {"workdir": "."})
    assert result["success"] is True
    assert "entries" in result


@pytest.mark.asyncio
async def test_grep_missing_pattern():
    """Test grep with missing pattern."""
    tool = GrepTool()
    result = await tool.execute({}, {"workdir": "."})
    assert result["success"] is False
    assert "Missing" in result["error"]


@pytest.mark.asyncio
async def test_execute_shell_safe_command():
    """Test execute_shell with safe command."""
    tool = ExecuteShellTool()
    result = await tool.execute({"command": "echo hello"}, {"workdir": "."})
    assert result["success"] is True
    assert "hello" in result["stdout"]


@pytest.mark.asyncio
async def test_execute_shell_unsafe_command():
    """Test execute_shell with unsafe command."""
    tool = ExecuteShellTool()
    result = await tool.execute({"command": "rm -rf /"}, {"workdir": "."})
    assert result["success"] is False
    assert "safe list" in result["error"]


def test_tool_schema():
    """Test tool schema generation."""
    tool = ReadFileTool()
    schema = tool.to_schema()
    assert schema["name"] == "read_file"
    assert "parameters" in schema
