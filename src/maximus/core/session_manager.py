"""Session Manager - Load and list saved sessions.

Handles:
- Listing all saved sessions from disk
- Loading session data by ID
- Session metadata (creation date, message count, model)
- Sorting by creation time (newest first)
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class SessionMetadata:
    """Metadata for a saved session."""
    session_id: str
    created_at: datetime
    message_count: int
    model: str
    
    def format_display(self) -> str:
        """Format for user display.
        
        Example: abc12345 (May 8, 2:30 PM) - 12 messages - qwen2.5-coder:7b
        """
        # Use platform-independent date format
        date_str = self.created_at.strftime("%b %d, %I:%M %p").lstrip("0").replace(" 0", " ")
        return f"{self.session_id[:8]} ({date_str}) - {self.message_count} messages - {self.model}"


class SessionManager:
    """Manage saved sessions on disk."""
    
    def __init__(self, sessions_dir: Optional[Path] = None):
        """Initialize SessionManager.
        
        Args:
            sessions_dir: Directory where sessions are stored.
                         Defaults to ~/.local/maximus/sessions
        """
        if sessions_dir is None:
            sessions_dir = Path.home() / ".local" / "maximus" / "sessions"
        
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"SessionManager initialized at {self.sessions_dir}")
    
    def list_all_sessions(self) -> List[SessionMetadata]:
        """List all saved sessions, sorted by creation date (newest first).
        
        Returns:
            List of SessionMetadata, newest first.
            Empty list if no sessions exist.
        """
        sessions = []
        
        # Find all .json files in sessions directory
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                metadata = self._load_session_metadata(session_file)
                if metadata:
                    sessions.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to load session {session_file}: {e}")
                # Continue with next session
                continue
        
        # Sort by creation date (newest first)
        sessions.sort(key=lambda x: x.created_at, reverse=True)
        
        return sessions
    
    def _load_session_metadata(self, session_file: Path) -> Optional[SessionMetadata]:
        """Load metadata from a session file.
        
        Args:
            session_file: Path to session JSON file
            
        Returns:
            SessionMetadata if valid, None if invalid/corrupted
        """
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            session_id = data.get("session_id")
            model = data.get("model", "unknown")
            messages = data.get("messages", [])
            created_at_str = data.get("created_at")
            
            # Parse creation date
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except (ValueError, TypeError):
                    created_at = datetime.now()
            else:
                # Fallback to file modification time
                created_at = datetime.fromtimestamp(session_file.stat().st_mtime)
            
            return SessionMetadata(
                session_id=session_id,
                created_at=created_at,
                message_count=len(messages),
                model=model
            )
        except json.JSONDecodeError:
            logger.warning(f"Corrupted JSON in {session_file.name}")
            return None
        except Exception as e:
            logger.error(f"Error loading session metadata: {e}")
            return None
    
    def load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load complete session data from disk.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Complete session dict with all messages, or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            logger.warning(f"Session file not found: {session_id}")
            return None
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded session {session_id} with {len(data.get('messages', []))} messages")
            return data
        except json.JSONDecodeError:
            logger.error(f"Corrupted JSON in session {session_id}")
            return None
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def get_session_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """Get metadata for a specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionMetadata or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        return self._load_session_metadata(session_file)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            True if session file exists, False otherwise
        """
        return (self.sessions_dir / f"{session_id}.json").exists()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from disk.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            logger.warning(f"Cannot delete: session {session_id} not found")
            return False
        
        try:
            session_file.unlink()
            logger.info(f"Deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
