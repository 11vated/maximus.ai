"""Tests for session persistence functionality."""
import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maximus.core.session_manager import SessionManager, SessionMetadata
from maximus.core.api import Session, MaximusBackend


class TestSessionManager:
    """Test SessionManager functionality."""
    
    @pytest.fixture
    def temp_sessions_dir(self):
        """Create temporary sessions directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_list_sessions_empty(self, temp_sessions_dir):
        """Test listing sessions when none exist."""
        manager = SessionManager(temp_sessions_dir)
        sessions = manager.list_all_sessions()
        
        assert sessions == []
    
    def test_list_sessions_multiple(self, temp_sessions_dir):
        """Test listing multiple sessions sorted by creation date (newest first)."""
        manager = SessionManager(temp_sessions_dir)
        
        # Create 3 mock sessions
        sessions_data = [
            {
                "session_id": "session1",
                "model": "qwen2.5-coder:7b",
                "messages": [{"role": "user", "content": "hello"}],
                "created_at": "2025-05-08T10:00:00"
            },
            {
                "session_id": "session2",
                "model": "qwen2.5-coder:14b",
                "messages": [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "hi"}
                ],
                "created_at": "2025-05-08T14:00:00"
            },
            {
                "session_id": "session3",
                "model": "codellama:7b",
                "messages": [
                    {"role": "user", "content": "help"},
                    {"role": "assistant", "content": "sure"}
                ],
                "created_at": "2025-05-08T12:00:00"
            }
        ]
        
        # Write sessions to disk
        for data in sessions_data:
            path = temp_sessions_dir / f"{data['session_id']}.json"
            with open(path, 'w') as f:
                json.dump(data, f)
        
        # List sessions
        sessions = manager.list_all_sessions()
        
        assert len(sessions) == 3
        # Should be sorted newest first (session2 at 14:00 is newest)
        assert sessions[0].session_id == "session2"
        assert sessions[1].session_id == "session3"
        assert sessions[2].session_id == "session1"
    
    def test_load_session_data(self, temp_sessions_dir):
        """Test loading complete session data from disk."""
        manager = SessionManager(temp_sessions_dir)
        
        # Create a test session
        session_data = {
            "session_id": "test_session",
            "model": "qwen2.5-coder:7b",
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi there"},
                {"role": "tool", "content": "tool result", "name": "ls"}
            ],
            "created_at": "2025-05-08T10:30:00"
        }
        
        session_file = temp_sessions_dir / "test_session.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Load session data
        loaded = manager.load_session_data("test_session")
        
        assert loaded is not None
        assert loaded["session_id"] == "test_session"
        assert loaded["model"] == "qwen2.5-coder:7b"
        assert len(loaded["messages"]) == 3
        # Verify all message types are preserved
        assert loaded["messages"][0]["role"] == "user"
        assert loaded["messages"][1]["role"] == "assistant"
        assert loaded["messages"][2]["role"] == "tool"
        assert loaded["messages"][2]["name"] == "ls"
    
    def test_load_session_not_found(self, temp_sessions_dir):
        """Test loading non-existent session."""
        manager = SessionManager(temp_sessions_dir)
        loaded = manager.load_session_data("nonexistent")
        
        assert loaded is None
    
    def test_load_corrupted_session(self, temp_sessions_dir):
        """Test loading corrupted JSON file."""
        manager = SessionManager(temp_sessions_dir)
        
        # Write corrupted JSON
        bad_file = temp_sessions_dir / "bad.json"
        with open(bad_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should return None for corrupted session
        loaded = manager.load_session_data("bad")
        assert loaded is None
    
    def test_session_exists(self, temp_sessions_dir):
        """Test checking if session exists."""
        manager = SessionManager(temp_sessions_dir)
        
        # Create a test session
        session_file = temp_sessions_dir / "test.json"
        with open(session_file, 'w') as f:
            json.dump({"session_id": "test"}, f)
        
        assert manager.session_exists("test") is True
        assert manager.session_exists("nonexistent") is False
    
    def test_session_metadata_accuracy(self, temp_sessions_dir):
        """Test that session metadata (message count, model) is accurate."""
        manager = SessionManager(temp_sessions_dir)
        
        session_data = {
            "session_id": "metadata_test",
            "model": "qwen2.5-coder:14b",
            "messages": [
                {"role": "user", "content": "msg1"},
                {"role": "assistant", "content": "msg2"},
                {"role": "user", "content": "msg3"}
            ],
            "created_at": "2025-05-08T15:30:00"
        }
        
        session_file = temp_sessions_dir / "metadata_test.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        metadata = manager.get_session_metadata("metadata_test")
        
        assert metadata is not None
        assert metadata.message_count == 3
        assert metadata.model == "qwen2.5-coder:14b"
        assert metadata.session_id == "metadata_test"


class TestSessionRestoration:
    """Test session restoration in backend."""
    
    @pytest.fixture
    def temp_sessions_dir(self):
        """Create temporary sessions directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_save_and_load_roundtrip(self, temp_sessions_dir):
        """Test that session can be saved and fully restored."""
        # Create a session
        session = Session("test_session", "qwen2.5-coder:7b")
        
        # Add messages (including tool calls and responses)
        session.add_message("user", "list files")
        session.add_message("assistant", "I'll list files for you")
        session.add_message("tool", '{"files": ["a.py", "b.py"]}', )
        
        # Save to disk
        session_dict = session.to_dict()
        session_file = temp_sessions_dir / "test_session.json"
        with open(session_file, 'w') as f:
            json.dump(session_dict, f)
        
        # Now load it back using SessionManager
        manager = SessionManager(temp_sessions_dir)
        loaded_data = manager.load_session_data("test_session")
        
        assert loaded_data is not None
        assert loaded_data["session_id"] == "test_session"
        assert len(loaded_data["messages"]) == 3
        
        # Verify message integrity
        assert loaded_data["messages"][0]["content"] == "list files"
        assert loaded_data["messages"][1]["content"] == "I'll list files for you"
        assert loaded_data["messages"][2]["content"] == '{"files": ["a.py", "b.py"]}'
    
    def test_backend_load_session_from_disk(self, temp_sessions_dir):
        """Test backend's load_session_from_disk method."""
        # Create a session file
        session_data = {
            "session_id": "backend_test",
            "model": "qwen2.5-coder:7b",
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
                {"role": "user", "content": "how are you?"},
                {"role": "assistant", "content": "I'm good!"}
            ],
            "created_at": "2025-05-08T10:00:00"
        }
        
        session_file = temp_sessions_dir / "backend_test.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Create backend with custom sessions dir
        backend = MaximusBackend(model="qwen2.5-coder:7b")
        backend.session_manager = SessionManager(temp_sessions_dir)
        backend.sessions_dir = temp_sessions_dir
        
        # Load session
        restored = backend.load_session_from_disk("backend_test")
        
        assert restored is not None
        assert restored.session_id == "backend_test"
        assert len(restored.messages) == 4
        # Verify full conversation history
        assert restored.messages[0]["role"] == "user"
        assert restored.messages[0]["content"] == "hello"
        assert restored.messages[-1]["role"] == "assistant"
        assert restored.messages[-1]["content"] == "I'm good!"
    
    def test_backend_load_nonexistent_session(self, temp_sessions_dir):
        """Test backend handling of non-existent session."""
        backend = MaximusBackend(model="qwen2.5-coder:7b")
        backend.session_manager = SessionManager(temp_sessions_dir)
        
        restored = backend.load_session_from_disk("nonexistent")
        
        assert restored is None
    
    def test_full_context_restoration(self, temp_sessions_dir):
        """Test that full context is restored including tool calls and responses."""
        # Create a complex session with tool interactions
        session_data = {
            "session_id": "complex",
            "model": "qwen2.5-coder:7b",
            "messages": [
                {"role": "system", "content": "You are Maximus"},
                {"role": "user", "content": "read file.py"},
                {"role": "assistant", "content": "Reading file..."},
                {"role": "tool", "content": "content of file.py", "name": "read_file"},
                {"role": "assistant", "content": "Here's the content"},
                {"role": "user", "content": "edit it"},
                {"role": "tool", "content": "preview of changes", "name": "preview_write"}
            ],
            "created_at": "2025-05-08T12:00:00"
        }
        
        session_file = temp_sessions_dir / "complex.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        backend = MaximusBackend()
        backend.session_manager = SessionManager(temp_sessions_dir)
        
        restored = backend.load_session_from_disk("complex")
        
        assert restored is not None
        assert len(restored.messages) == 7
        
        # Verify all message types are preserved with full context
        messages = restored.messages
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[3]["role"] == "tool"
        assert messages[3]["name"] == "read_file"
        assert messages[6]["name"] == "preview_write"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
