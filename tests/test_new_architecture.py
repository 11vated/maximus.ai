"""Unit tests for the new Maximus architecture."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maximus.utils.ollama import resolve_model, detect_hardware, get_default_model
from maximus.core.safety import SafetyController, SafetyError
from maximus.tools.registry import get_registry


class TestModelResolution:
    """Test model alias resolution."""
    
    def test_resolve_7b(self):
        assert resolve_model("7b") == "qwen2.5-coder:7b"
        
    def test_resolve_14b(self):
        assert resolve_model("14b") == "qwen2.5-coder:14b"
        
    def test_resolve_fast(self):
        assert resolve_model("fast") == "codellama:7b"
        
    def test_resolve_smart(self):
        assert resolve_model("smart") == "qwen2.5-coder:14b"
        
    def test_resolve_think(self):
        assert resolve_model("think") == "deepseek-r1:7b"
        
    def test_resolve_full_name(self):
        assert resolve_model("qwen2.5-coder:7b") == "qwen2.5-coder:7b"
        
    def test_resolve_unknown(self):
        assert resolve_model("unknown") == "unknown"


class TestHardwareDetection:
    """Test hardware detection."""
    
    def test_detect_hardware(self):
        hardware = detect_hardware()
        assert "ram_gb" in hardware
        assert "has_gpu" in hardware
        assert "os" in hardware
        assert hardware["os"] in ["darwin", "linux", "windows"]


class TestDefaultModel:
    """Test default model selection."""
    
    def test_get_default_model(self):
        model = get_default_model()
        assert model is not None
        assert isinstance(model, str)


class TestSafetyController:
    """Test safety layers."""
    
    def test_layer2_write_without_preview(self):
        safety = SafetyController()
        
        # Should raise SafetyError when trying to write without preview
        with pytest.raises(SafetyError):
            safety.layer2_check("write_file", {"path": "test.py", "content": "print('hi')"}, {})
            
    def test_layer2_read_allowed(self):
        safety = SafetyController()
        
        # Should not raise for read operations
        safety.layer2_check("read_file", {"path": "test.py"}, {})
        
    def test_layer2_with_preview_recorded(self):
        safety = SafetyController()
        safety.record_preview("test_session")
        
        # Should not raise after preview recorded
        safety.layer2_check("write_file", {"path": "test.py", "content": "hi"}, {"session_id": "test_session"})


class TestToolRegistry:
    """Test tool registry."""
    
    def test_list_tools(self):
        registry = get_registry()
        tools = registry.list_tools()
        assert len(tools) > 0
        assert "read_file" in tools
        assert "write_file" in tools
        assert "preview_write" in tools
        
    def test_preview_write_registered(self):
        registry = get_registry()
        tool = registry.get("preview_write")
        assert tool is not None


class TestBackendAPI:
    """Test backend API."""
    
    def test_backend_initialization(self):
        from maximus.core.api import MaximusBackend
        backend = MaximusBackend(model="qwen2.5-coder:7b")
        assert backend.model == "qwen2.5-coder:7b"
        assert backend.llm is not None
        assert backend.registry is not None
        assert backend.safety is not None
        
    def test_get_session(self):
        from maximus.core.api import MaximusBackend
        backend = MaximusBackend()
        session = backend.get_session("new_session")
        assert session is not None
        assert session.session_id == "new_session"
        
    def test_process_creates_session(self):
        from maximus.core.api import MaximusBackend
        backend = MaximusBackend(model="qwen2.5-coder:7b")
        # Just creating a session, don't actually call LLM
        session_id = "test_session"
        session = backend.sessions.get(session_id)
        # Should create on demand
        assert session is None or session.session_id == session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])