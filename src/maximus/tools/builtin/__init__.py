"""Builtin tools for Maximus.ai."""

from maximus.tools.builtin.execute_shell import ExecuteShellTool
from maximus.tools.builtin.read_file import ReadFileTool
from maximus.tools.builtin.write_file import WriteFileTool
from maximus.tools.builtin.edit_file import EditFileTool
from maximus.tools.builtin.grep_tool import GrepTool
from maximus.tools.builtin.glob_tool import GlobTool
from maximus.tools.builtin.ls_tool import LsTool
from maximus.tools.builtin.python_runner import PythonRunnerTool
from maximus.tools.builtin.node_runner import NodeRunnerTool
from maximus.tools.builtin.git_tools import GitStatusTool, GitDiffTool, GitCommitTool, GitAddTool, GitPushTool
from maximus.tools.builtin.web_search import WebSearchTool
from maximus.tools.builtin.web_fetch import WebFetchTool
from maximus.tools.builtin.test_runner import TestRunnerTool
from maximus.tools.builtin.file_ops import MoveFileTool, CopyFileTool, DeleteFileTool
from maximus.tools.builtin.browser_tool import BrowserTool
from maximus.tools.builtin.scheduler_tools import SleepTool, DateTimeTool
from maximus.tools.builtin.system_tools import EnvInfoTool, SystemInfoTool, CreateDirTool, ListProcessesTool
from maximus.tools.builtin.task_tools import TodoWriteTool, TodoReadTool, TaskCreateTool, TaskUpdateTool, TaskStopTool, TaskListTool
from maximus.tools.builtin.multi_edit import MultiEditTool

# Repo analysis tools
from maximus.adapters.open_swe_adapter import AnalyzeOpenSweTool
from maximus.adapters.clawspring_adapter import AnalyzeClawSpringTool
from maximus.adapters.nexus_adapter import AnalyzeNexusTool

# Register all builtin tools
def register_builtin_tools():
    """Register all builtin tools with the global registry."""
    from maximus.tools.registry import register_tool

    register_tool(ExecuteShellTool())
    register_tool(ReadFileTool())
    register_tool(WriteFileTool())
    register_tool(EditFileTool())
    register_tool(MultiEditTool())  # NEW: Multi-file atomic edits
    register_tool(GrepTool())
    register_tool(GlobTool())
    register_tool(LsTool())
    register_tool(PythonRunnerTool())
    register_tool(NodeRunnerTool())
    register_tool(GitStatusTool())
    register_tool(GitDiffTool())
    register_tool(GitCommitTool())
    register_tool(GitAddTool())
    register_tool(GitPushTool())
    register_tool(WebSearchTool())
    register_tool(WebFetchTool())  # NEW: Web content fetching
    register_tool(TestRunnerTool())
    register_tool(MoveFileTool())
    register_tool(CopyFileTool())
    register_tool(DeleteFileTool())
    register_tool(BrowserTool())
    register_tool(SleepTool())
    register_tool(DateTimeTool())
    register_tool(EnvInfoTool())
    register_tool(SystemInfoTool())
    register_tool(CreateDirTool())
    register_tool(ListProcessesTool())
    register_tool(TodoWriteTool())
    register_tool(TodoReadTool())
    register_tool(TaskCreateTool())
    register_tool(TaskUpdateTool())
    register_tool(TaskStopTool())
    register_tool(TaskListTool())


def register_repo_tools():
    """Register repo analysis tools with the global registry."""
    from maximus.tools.registry import register_tool

    register_tool(AnalyzeOpenSweTool())
    register_tool(AnalyzeClawSpringTool())
    register_tool(AnalyzeNexusTool())
