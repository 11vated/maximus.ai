"""Tests for all 29 registered tools - one test per tool."""

import pytest
import asyncio
from maximus.tools.registry import registry, register_tool
from maximus.tools.builtin import register_builtin_tools, register_repo_tools


# Ensure all tools are registered
register_builtin_tools()
register_repo_tools()

ALL_TOOL_NAMES = registry.list_tools()
# Expected: 35 base tools + 2 new (multi_edit, web_fetch) = 37
assert len(ALL_TOOL_NAMES) == 37, f"Expected 37 tools, got {len(ALL_TOOL_NAMES)}"


@pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
def test_tool_exists(tool_name):
    """Test that each tool exists in registry."""
    tool = registry.get(tool_name)
    assert tool is not None, f"Tool {tool_name} not found"
    assert tool.metadata.name == tool_name


@pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
def test_tool_metadata(tool_name):
    """Test that each tool has valid metadata."""
    metadata = registry.get_metadata(tool_name)
    assert metadata is not None
    assert metadata.name == tool_name
    assert metadata.description is not None
    assert len(metadata.description) > 0
    assert metadata.permission_level in ["safe", "write", "dangerous"]
    assert isinstance(metadata.read_only, bool)
    assert isinstance(metadata.local_only, bool)


@pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
def test_tool_schema(tool_name):
    """Test that each tool can generate a valid schema."""
    tool = registry.get(tool_name)
    schema = tool.to_schema()
    assert schema is not None
    assert "name" in schema
    assert schema["name"] == tool_name
    assert "description" in schema


# Specific tool tests
def test_execute_shell_safe():
    """Test execute_shell with safe command."""
    tool = registry.get("execute_shell")
    result = asyncio.run(tool.execute({"command": "echo hello"}, {}))
    assert result["success"] is True
    assert "hello" in result["stdout"].lower()


def test_read_file_missing():
    """Test read_file with missing path."""
    tool = registry.get("read_file")
    result = asyncio.run(tool.execute({}, {}))
    assert result["success"] is False
    assert "error" in result


def test_write_file():
    """Test write_file creates file."""
    tool = registry.get("write_file")
    result = asyncio.run(tool.execute({
        "path": "test_output.txt",
        "content": "Hello from Maximus",
    }, {}))
    assert result["success"] is True

    # Cleanup
    import os
    if os.path.exists("test_output.txt"):
        os.remove("test_output.txt")


def test_grep_tool():
    """Test grep tool."""
    tool = registry.get("grep")
    result = asyncio.run(tool.execute({
        "pattern": "def",
        "path": "src/maximus/cli.py",
    }, {}))
    assert result["success"] is True
    assert "results" in result


def test_glob_tool():
    """Test glob tool."""
    tool = registry.get("glob")
    result = asyncio.run(tool.execute({
        "pattern": "*.py",
        "path": "src/maximus",
    }, {}))
    assert result["success"] is True
    assert "results" in result


def test_datetime_tool():
    """Test datetime tool."""
    tool = registry.get("datetime")
    result = asyncio.run(tool.execute({}, {}))
    assert result["success"] is True
    assert "iso" in result


def test_env_info():
    """Test env_info tool."""
    tool = registry.get("env_info")
    result = asyncio.run(tool.execute({}, {}))
    assert result["success"] is True
    assert "env" in result


def test_system_info():
    """Test system_info tool."""
    tool = registry.get("system_info")
    result = asyncio.run(tool.execute({}, {}))
    assert result["success"] is True
    assert "os" in result


def test_create_dir():
    """Test create_dir tool."""
    tool = registry.get("create_dir")
    result = asyncio.run(tool.execute({"path": "test_temp_dir"}, {}))
    assert result["success"] is True

    # Cleanup
    import os
    if os.path.exists("test_temp_dir"):
        os.rmdir("test_temp_dir")


def test_list_processes():
    """Test list_processes tool."""
    tool = registry.get("list_processes")
    result = asyncio.run(tool.execute({}, {}))
    assert result["success"] is True
    assert "output" in result


def test_browser_tool():
    """Test browser_tool (may fail without display)."""
    tool = registry.get("browse_url")
    # Just test it doesn't crash
    result = asyncio.run(tool.execute({"url": "https://example.com"}, {}))
    assert "success" in result


def test_test_runner():
    """Test test_runner tool."""
    tool = registry.get("run_tests")
    result = asyncio.run(tool.execute({"path": "tests/unit"}, {}))
    assert "success" in result


def test_move_file():
    """Test move_file tool."""
    tool = registry.get("move_file")
    # Create source
    with open("test_source.txt", "w") as f:
        f.write("test")

    result = asyncio.run(tool.execute({
        "src": "test_source.txt",
        "dst": "test_dest.txt",
    }, {}))
    assert result["success"] is True

    # Cleanup
    import os
    for f in ["test_source.txt", "test_dest.txt"]:
        if os.path.exists(f):
            os.remove(f)


def test_copy_file():
    """Test copy_file tool."""
    tool = registry.get("copy_file")
    with open("test_copy_src.txt", "w") as f:
        f.write("copy test")

    result = asyncio.run(tool.execute({
        "src": "test_copy_src.txt",
        "dst": "test_copy_dst.txt",
    }, {}))
    assert result["success"] is True

    # Cleanup
    import os
    for f in ["test_copy_src.txt", "test_copy_dst.txt"]:
        if os.path.exists(f):
            os.remove(f)


def test_delete_file():
    """Test delete_file tool."""
    tool = registry.get("delete_file")
    with open("test_delete.txt", "w") as f:
        f.write("delete me")

    result = asyncio.run(tool.execute({"path": "test_delete.txt", "force": True}, {}))
    assert result["success"] is True
    import os
    assert not os.path.exists("test_delete.txt")


def test_git_diff():
    """Test git_diff tool."""
    tool = registry.get("git_diff")
    result = asyncio.run(tool.execute({}, {}))
    assert "success" in result


def test_git_add():
    """Test git_add tool."""
    tool = registry.get("git_add")
    result = asyncio.run(tool.execute({"files": ["test.txt"]}, {}))
    assert "success" in result


def test_git_commit():
    """Test git_commit tool."""
    tool = registry.get("git_commit")
    result = asyncio.run(tool.execute({"message": "Test commit"}, {}))
    assert "success" in result


def test_git_push():
    """Test git_push tool."""
    tool = registry.get("git_push")
    result = asyncio.run(tool.execute({}, {}))
    assert "success" in result


def test_analyze_open_swe():
    """Test analyze_open_swe tool."""
    tool = registry.get("analyze_open_swe")
    result = asyncio.run(tool.execute({"repo_path": "."}, {}))
    assert result["success"] is True
    assert "repo" in result


def test_analyze_clawspring():
    """Test analyze_clawspring tool."""
    tool = registry.get("analyze_clawspring")
    result = asyncio.run(tool.execute({"repo_path": "."}, {}))
    assert result["success"] is True
    assert "repo" in result


def test_analyze_nexus():
    """Test analyze_nexus tool."""
    tool = registry.get("analyze_nexus")
    result = asyncio.run(tool.execute({"repo_path": "."}, {}))
    assert result["success"] is True
    assert "repo" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
