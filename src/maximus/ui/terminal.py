"""Terminal UI - Simple, unified chat interface with session persistence.

Single entry point for the Maximus chat experience.
Features:
- Interactive session menu to resume previous conversations
- Session history with metadata
- Support for --session, --new, --list-sessions flags
"""
import sys
import os
import signal
import getpass
import uuid
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maximus.utils.ollama import ensure_ollama_running, get_default_model
from maximus.core.api import MaximusBackend
from maximus.core.session_manager import SessionManager


class TerminalUI:
    """Simple terminal-based chat interface with session management."""
    
    def __init__(self, model: str = None, verbose: bool = False, session_id: str = None, force_new: bool = False, show_menu: bool = False):
        self.verbose = verbose
        self.session_id = session_id
        self.force_new = force_new
        self.show_menu = show_menu
        self.backend = None
        self.model = model
        self.session_manager = None
        
    def log(self, msg: str):
        """Log message if verbose mode."""
        if self.verbose:
            print(f"[DEBUG] {msg}", file=sys.stderr)
            
    def init_backend(self):
        """Initialize the backend - ensures Ollama running."""
        print("Initializing Maximus...", file=sys.stderr)
        
        # Ensure Ollama is running
        if not ensure_ollama_running():
            print("ERROR: Could not start Ollama. Please install and run 'ollama serve'", file=sys.stderr)
            sys.exit(1)
        
        # Select model if not specified
        if not self.model:
            self.model = get_default_model()
            print(f"Using model: {self.model}", file=sys.stderr)
        
        # Initialize backend
        self.backend = MaximusBackend(model=self.model)
        self.session_manager = SessionManager()
        print(f"Maximus ready (session: {self.session_id})", file=sys.stderr)
        print("Type 'exit' or 'quit' to end session", file=sys.stderr)
        print("Type '--list-sessions' to show available sessions\n", file=sys.stderr)
    
    def show_session_menu(self) -> str:
        """Show interactive session menu and return selected session ID.
        
        Returns:
            Session ID to resume, or None to start new session
        """
        print("\n=== Maximus - Session Manager ===\n", file=sys.stderr)
        
        # List all sessions
        sessions = self.session_manager.list_all_sessions()
        
        if not sessions:
            print("No saved sessions found.", file=sys.stderr)
            print("Starting new session...\n", file=sys.stderr)
            return None
        
        # Auto-load if only 1 session (unless --force-new)
        if len(sessions) == 1 and not self.force_new:
            session = sessions[0]
            print(f"Auto-loading session: {session.format_display()}\n", file=sys.stderr)
            return session.session_id
        
        # Show menu
        print("Recent Sessions:\n", file=sys.stderr)
        for i, session in enumerate(sessions, 1):
            print(f"[{i}] {session.format_display()}", file=sys.stderr)
        
        print(f"\n[n] Start new session", file=sys.stderr)
        print(f"[q] Quit\n", file=sys.stderr)
        
        while True:
            try:
                choice = input("Choice: ").strip().lower()
                
                if choice == 'q':
                    print("Goodbye!", file=sys.stderr)
                    sys.exit(0)
                elif choice == 'n':
                    print("Starting new session...\n", file=sys.stderr)
                    return None
                else:
                    # Try to parse as session number
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(sessions):
                            session = sessions[idx]
                            print(f"Loading session: {session.format_display()}\n", file=sys.stderr)
                            return session.session_id
                        else:
                            print(f"Invalid choice. Please enter 1-{len(sessions)}, n, or q", file=sys.stderr)
                    except ValueError:
                        print(f"Invalid choice. Please enter 1-{len(sessions)}, n, or q", file=sys.stderr)
            except KeyboardInterrupt:
                print("\nGoodbye!", file=sys.stderr)
                sys.exit(0)
            except EOFError:
                sys.exit(0)
    
    def list_sessions_in_chat(self):
        """List sessions during chat and show menu."""
        sessions = self.session_manager.list_all_sessions()
        
        if not sessions:
            print("\n[No saved sessions]", file=sys.stderr)
            return
        
        print("\n=== Saved Sessions ===\n", file=sys.stderr)
        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session.format_display()}", file=sys.stderr)
        print()
    
    def run(self):
        """Main chat loop."""
        self.init_backend()
        
        # Handle session selection
        if self.force_new:
            # --new flag: skip menu and use new session
            self.session_id = str(uuid.uuid4())[:8]
        elif self.show_menu:
            # --list-sessions flag during startup would show menu
            selected = self.show_session_menu()
            if selected:
                # Load selected session from disk
                self.session_id = selected
                restored_session = self.backend.load_session_from_disk(selected)
                if restored_session:
                    print(f"Session restored with {len(restored_session.messages)} previous messages", file=sys.stderr)
                else:
                    print(f"Warning: Could not restore session {selected}, starting fresh", file=sys.stderr)
                    self.session_id = str(uuid.uuid4())[:8]
            else:
                # New session
                self.session_id = str(uuid.uuid4())[:8]
        elif self.session_id:
            # --session <id> flag: load specific session
            restored_session = self.backend.load_session_from_disk(self.session_id)
            if not restored_session:
                print(f"Warning: Session {self.session_id} not found, starting fresh", file=sys.stderr)
                self.session_id = str(uuid.uuid4())[:8]
            else:
                print(f"Session restored with {len(restored_session.messages)} previous messages", file=sys.stderr)
        else:
            # No flags: show menu to choose
            selected = self.show_session_menu()
            if selected:
                self.session_id = selected
                restored_session = self.backend.load_session_from_disk(selected)
                if restored_session:
                    print(f"Session restored with {len(restored_session.messages)} previous messages", file=sys.stderr)
                else:
                    print(f"Warning: Could not restore session {selected}, starting fresh", file=sys.stderr)
                    self.session_id = str(uuid.uuid4())[:8]
            else:
                self.session_id = str(uuid.uuid4())[:8]
        
        prompt = ">>> "
        
        while True:
            try:
                # Get user input
                user_input = input(prompt)
                
                # Check for exit commands
                if user_input.strip().lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                # Skip empty input
                if not user_input.strip():
                    continue
                
                # Clear screen command
                if user_input.strip() == 'clear':
                    print("\033[2J\033[H", end="")
                    continue
                
                # List sessions command
                if user_input.strip() == '--list-sessions':
                    self.list_sessions_in_chat()
                    continue
                
                # Process message through backend
                if self.backend:
                    response = self.backend.process_message(
                        user_input, 
                        self.session_id
                    )
                    print(response)
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
                continue
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                if self.verbose:
                    import traceback
                    traceback.print_exc()
                    
        # Cleanup
        if self.backend:
            self.backend.shutdown()


def parse_args():
    """Parse command line arguments."""
    model = None
    verbose = False
    session_id = None
    force_new = False
    show_menu = False
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--model' or args[i] == '-m':
            if i + 1 < len(args):
                model = args[i + 1]
                i += 2
            else:
                print("Error: --model requires an argument")
                sys.exit(1)
        elif args[i] == '--session':
            if i + 1 < len(args):
                session_id = args[i + 1]
                i += 2
            else:
                print("Error: --session requires an argument")
                sys.exit(1)
        elif args[i] == '--verbose' or args[i] == '-v':
            verbose = True
            i += 1
        elif args[i] == '--new':
            force_new = True
            i += 1
        elif args[i] == '--list-sessions':
            show_menu = True
            i += 1
        elif args[i] == '--help' or args[i] == '-h':
            print_help()
            sys.exit(0)
        elif args[i] == '--version':
            print("Maximus v2.0.0")
            sys.exit(0)
        elif args[i] == 'doctor':
            run_diagnostics()
            sys.exit(0)
        else:
            i += 1
            
    return model, verbose, session_id, force_new, show_menu


def print_help():
    """Print help message."""
    print("""Maximus - AI Coding Assistant

Usage:
    maximus                    Start session (show menu if sessions exist)
    maximus --new              Start fresh session (skip menu)
    maximus --session <id>     Resume specific session
    maximus --model <name>     Use specific model
    maximus --verbose          Show debug information
    maximus doctor             Run diagnostics

Options:
    -m, --model <name>        Specify model (7b, 14b, fast, smart, think)
    --session <id>            Resume existing session by ID
    --new                      Force new session (skip menu)
    -v, --verbose             Enable debug output
    -h, --help                Show this help
    --version                 Show version number

Examples:
    maximus                   Start with session menu
    maximus --new            Start fresh session
    maximus --session abc123 Resume session abc123
    maximus -m 14b           Use qwen2.5-coder:14b model
    maximus --verbose        Debug mode
""")


def run_diagnostics():
    """Run system diagnostics."""
    print("=== Maximus Diagnostics ===\n")
    
    # Check Python version
    print(f"Python: {sys.version.split()[0]}")
    
    # Check Ollama
    try:
        import httpx
        resp = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"Ollama: Running ({len(models)} models)")
            for m in models[:3]:
                print(f"  - {m['name']}")
        else:
            print("Ollama: Not responding")
    except Exception as e:
        print(f"Ollama: Not running ({e})")
    
    # Check config
    config_path = os.path.expanduser("~/.config/maximus/config.yaml")
    if os.path.exists(config_path):
        print(f"Config: {config_path}")
    else:
        print("Config: Not configured (will use defaults)")
    
    # Check sessions
    sessions_dir = os.path.expanduser("~/.local/maximus/sessions")
    if os.path.exists(sessions_dir):
        sessions = os.listdir(sessions_dir)
        print(f"Sessions: {len(sessions)} saved")
        
        # Show recent sessions
        session_manager = SessionManager()
        recent = session_manager.list_all_sessions()[:3]
        if recent:
            print("\n  Recent sessions:")
            for session in recent:
                print(f"    - {session.format_display()}")
    else:
        print("Sessions: None saved")
    
    print("\n=== End Diagnostics ===")


def main():
    """Main entry point."""
    model, verbose, session_id, force_new, show_menu = parse_args()
    
    ui = TerminalUI(
        model=model, 
        verbose=verbose, 
        session_id=session_id, 
        force_new=force_new,
        show_menu=show_menu
    )
    ui.run()


if __name__ == "__main__":
    main()
