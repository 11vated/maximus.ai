"""E2E Tests for Maximus Terminal UI using Playwright-style testing.

Since we're testing a terminal app, we use subprocess testing.
"""
import subprocess
import sys
import time
import os
import signal
import pytest


class TestTerminalUI:
    """End-to-end tests for terminal UI."""
    
    def test_cli_help(self):
        """Test that help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "maximus.ui.terminal", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "Maximus" in result.stdout
        
    def test_cli_version(self):
        """Test version command."""
        result = subprocess.run(
            [sys.executable, "-m", "maximus.ui.terminal", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "v" in result.stdout.lower()
        
    def test_doctor_command(self):
        """Test doctor diagnostics command."""
        result = subprocess.run(
            [sys.executable, "-m", "maximus.ui.terminal", "doctor"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "Diagnostics" in result.stdout or "diagnostics" in result.stdout.lower()
        
    def test_new_session_flag(self):
        """Test --new flag starts new session."""
        result = subprocess.run(
            [sys.executable, "-m", "maximus.ui.terminal", "--new"],
            input="exit\n",
            capture_output=True,
            text=True,
            timeout=30
        )
        # Should start and exit cleanly
        assert "Initializing" in result.stderr or "Maximus" in result.stderr


class TestSessionManagement:
    """Tests for session management."""
    
    def test_session_manager_exists(self):
        """Verify SessionManager can be imported."""
        from maximus.core.session_manager import SessionManager
        sm = SessionManager()
        assert sm is not None
        
    def test_session_manager_list(self):
        """Test session listing."""
        from maximus.core.session_manager import SessionManager
        sm = SessionManager()
        sessions = sm.list_all_sessions()
        assert isinstance(sessions, list)


class TestVirtualScrollBuffer:
    """Tests for virtual scroll buffer."""
    
    def test_buffer_add(self):
        """Test adding to buffer."""
        from maximus.ui.terminal import VirtualScrollBuffer
        buf = VirtualScrollBuffer(max_lines=10)
        buf.add("line1\nline2\nline3")
        assert len(buf.lines) == 3
        
    def test_buffer_max_lines(self):
        """Test buffer respects max_lines."""
        from maximus.ui.terminal import VirtualScrollBuffer
        buf = VirtualScrollBuffer(max_lines=5)
        for i in range(100):
            buf.add(f"line{i}")
        assert len(buf.lines) == 5
        assert buf.total_lines == 100  # Total count still accurate
        
    def test_buffer_visible(self):
        """Test get_visible returns recent lines."""
        from maximus.ui.terminal import VirtualScrollBuffer
        buf = VirtualScrollBuffer(max_lines=10)
        for i in range(20):
            buf.add(f"line{i}")
        visible = buf.get_visible()
        assert len(visible) == 10
        assert visible[-1] == "line19"


class TestErrorBoundary:
    """Tests for error boundary."""
    
    def test_retry_logic(self):
        """Test retry on connection error."""
        from maximus.ui.terminal import ErrorBoundary
        import time
        
        attempts = [0]
        def failing_func():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ConnectionError("Test error")
            return "success"
            
        eb = ErrorBoundary(max_retries=3)
        result = eb.execute(failing_func)
        assert result == "success"
        assert eb.retry_count == 2
        
    def test_max_retries_exceeded(self):
        """Test that max retries stops execution."""
        from maximus.ui.terminal import ErrorBoundary
        
        def always_fails():
            raise ConnectionError("Always fails")
            
        eb = ErrorBoundary(max_retries=2)
        with pytest.raises(ConnectionError):
            eb.execute(always_fails)