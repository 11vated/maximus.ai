"""Terminal UI - Advanced terminal interface with virtual scrolling.

Single entry point for the Maximus chat experience.
Features:
- Interactive session menu to resume previous conversations
- Session history with metadata
- Support for --session, --new, --list-sessions flags
- Virtual scrolling for long conversations
- Error boundaries with retry logic
- Rich streaming output
"""
import sys
import os
import signal
import getpass
import uuid
import time
import asyncio
from datetime import datetime
from collections import deque
from typing import Optional, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maximus.utils.ollama import ensure_ollama_running, get_default_model
from maximus.core.api import MaximusBackend
from maximus.core.session_manager import SessionManager
from maximus.mcp.connector import add_server, list_available_servers, auto_discover_servers
from maximus.discovery.connector import discover_packages, get_package_details, format_package_info

# Terminal constants
MAX_OUTPUT_LINES = 500  # Virtual scroll buffer size
ERROR_RETRY_ATTEMPTS = 3
ERROR_RETRY_DELAY = 1  # seconds


class VirtualScrollBuffer:
    """Virtual scrolling buffer for terminal output.
    
    Keeps only the most recent lines in memory to prevent memory issues
    with long conversations.
    """
    
    def __init__(self, max_lines: int = MAX_OUTPUT_LINES):
        self.max_lines = max_lines
        self.lines: deque = deque(maxlen=max_lines)
        self.total_lines = 0
        
    def add(self, text: str):
        """Add text to buffer, respecting max_lines."""
        for line in text.split('\n'):
            self.lines.append(line)
            self.total_lines += 1
            
    def get_visible(self) -> List[str]:
        """Get visible lines (most recent max_lines)."""
        return list(self.lines)
    
    def get_scrolled(self, offset: int = 0) -> List[str]:
        """Get lines scrolled back by offset."""
        lines = list(self.lines)
        if offset >= len(lines):
            return []
        return lines[-(self.max_lines - offset):] if offset > 0 else lines


class ErrorBoundary:
    """Error boundary with retry logic and graceful degradation."""
    
    def __init__(self, max_retries: int = ERROR_RETRY_ATTEMPTS):
        self.max_retries = max_retries
        self.retry_count = 0
        self.last_error: Optional[Exception] = None
        
    def execute(self, func, *args, **kwargs):
        """Execute function with retry logic."""
        for attempt in range(self.max_retries):
            try:
                self.retry_count = attempt
                return func(*args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                self.last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(ERROR_RETRY_DELAY * (attempt + 1))
                    continue
                raise
            except Exception as e:
                self.last_error = e
                raise
        return None
    
    def reset(self):
        """Reset retry counter."""
        self.retry_count = 0
        self.last_error = None


class TerminalUI:
    """Advanced terminal-based chat interface with session management.
    
    Features:
    - Virtual scrolling for long conversations
    - Error boundaries with retry logic
    - Session persistence with menu
    - Rich streaming output
    """
    
    def __init__(self, model: str = None, verbose: bool = False, session_id: str = None, force_new: bool = False, show_menu: bool = False):
        self.verbose = verbose
        self.session_id = session_id
        self.force_new = force_new
        self.show_menu = show_menu
        self.backend = None
        self.model = model
        self.session_manager = None
        self.output_buffer = VirtualScrollBuffer()
        self.error_boundary = ErrorBoundary()
        self.use_rich_output = self._detect_rich_support()
        
    def _detect_rich_support(self) -> bool:
        """Detect if rich output is supported."""
        try:
            import sys
            return sys.stdout.isatty() and os.environ.get('TERM')
        except:
            return False
        
    def log(self, msg: str):
        """Log message if verbose mode."""
        if self.verbose:
            print(f"[DEBUG] {msg}", file=sys.stderr)
            
    def stream_output(self, text: str, end: str = "\n"):
        """Stream output with virtual scrolling support."""
        self.output_buffer.add(text)
        if self.use_rich_output and len(self.output_buffer.lines) > self.output_buffer.max_lines:
            # Only show most recent lines
            visible = self.output_buffer.get_visible()
            for line in visible[-100:]:  # Show last 100 lines
                print(line)
        else:
            print(text, end=end)
            
    def safe_execute(self, func, *args, **kwargs):
        """Execute function with error boundary."""
        try:
            return self.error_boundary.execute(func, *args, **kwargs)
        except Exception as e:
            self.stream_output(f"\n[ERROR] {e}\n", file=sys.stderr)
            if self.verbose:
                import traceback
                traceback.print_exc()
            return None
            
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

    async def handle_mcp_command(self, command: str):
        """Handle MCP commands like 'mcp add github://...'."""
        parts = command.split(maxsplit=1)
        if not parts:
            self.stream_output("Usage: mcp <command> [args]\n", file=sys.stderr)
            self.stream_output("Commands: add <url>, list, discover\n", file=sys.stderr)
            return
            
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        try:
            if cmd == "add":
                if not args:
                    self.stream_output("Usage: mcp add <url>\n", file=sys.stderr)
                    return
                    
                # Extract server name from URL or use default
                name = "server"
                if args.startswith("github://"):
                    name = "github"
                elif args.startswith("file://"):
                    name = "filesystem"
                    
                self.stream_output(f"Adding MCP server: {name} ({args})...", file=sys.stderr)
                success = self.safe_execute(
                    lambda: asyncio.run(add_server(name, args))
                )
                if success:
                    self.stream_output(" ✓ Done\n", file=sys.stderr)
                else:
                    self.stream_output(" ✗ Failed\n", file=sys.stderr)
                    
            elif cmd == "list":
                servers = self.safe_execute(lambda: list_available_servers())
                self.stream_output("Available MCP servers:\n", file=sys.stderr)
                for s in servers:
                    self.stream_output(f"  - {s}\n", file=sys.stderr)
                    
            elif cmd == "discover":
                self.stream_output("Discovering MCP servers...", file=sys.stderr)
                discovered = self.safe_execute(
                    lambda: asyncio.run(auto_discover_servers())
                )
                if discovered:
                    self.stream_output(f" ✓ Found: {', '.join(discovered)}\n", file=sys.stderr)
                else:
                    self.stream_output(" ✗ No servers discovered\n", file=sys.stderr)
            else:
                self.stream_output(f"Unknown MCP command: {cmd}\n", file=sys.stderr)
                self.stream_output("Commands: add, list, discover\n", file=sys.stderr)
                
        except Exception as e:
            self.stream_output(f"Error: {e}\n", file=sys.stderr)

    async def handle_discover_command(self, command: str):
        """Handle discover commands like 'discover redis client'."""
        parts = command.split(maxsplit=1)
        if not parts or not parts[0]:
            self.stream_output("Usage: discover <query> [--install]\n", file=sys.stderr)
            return
            
        query = parts[0]
        install_flag = "--install" in command
        
        try:
            self.stream_output(f"Searching for packages: '{query}'...", file=sys.stderr)
            packages = self.safe_execute(
                lambda: asyncio.run(discover_packages(query, limit=10))
            )
            
            if packages:
                self.stream_output(f"Found {len(packages)} packages:\n", file=sys.stderr)
                for pkg in packages:
                    pkg_info = self.safe_execute(
                        lambda: asyncio.run(get_package_details(pkg["name"]))
                    )
                    if pkg_info:
                        formatted = format_package_info(pkg_info)
                        self.stream_output(f"  • {formatted}\n", file=sys.stderr)
                    
                if install_flag and packages:
                    # Install the first package
                    pkg_name = packages[0]["name"]
                    self.stream_output(f"Installing {pkg_name}...", file=sys.stderr)
                    # In a real implementation, this would use pip install
                    self.stream_output(" ✓ (simulated) Package would be installed in sandbox\n", file=sys.stderr)
            else:
                self.stream_output("No packages found\n", file=sys.stderr)
                
        except Exception as e:
            self.stream_output(f"Error: {e}\n", file=sys.stderr)
    
    async def run(self):
        """Main chat loop with error handling."""
        self.init_backend()

        # Handle session selection
        if self.force_new:
            self.session_id = str(uuid.uuid4())[:8]
        elif self.show_menu:
            selected = self.show_session_menu()
            if selected:
                self.session_id = selected
                restored_session = self.safe_execute(
                    lambda: self.backend.load_session_from_disk(selected)
                )
                if restored_session:
                    self.stream_output(f"Session restored with {len(restored_session.messages)} previous messages\n", file=sys.stderr)
                else:
                    self.stream_output(f"Warning: Could not restore session {selected}, starting fresh\n", file=sys.stderr)
                    self.session_id = str(uuid.uuid4())[:8]
            else:
                self.session_id = str(uuid.uuid4())[:8]
        elif self.session_id:
            restored_session = self.safe_execute(
                lambda: self.backend.load_session_from_disk(self.session_id)
            )
            if not restored_session:
                self.stream_output(f"Warning: Session {self.session_id} not found, starting fresh\n", file=sys.stderr)
                self.session_id = str(uuid.uuid4())[:8]
            else:
                self.stream_output(f"Session restored with {len(restored_session.messages)} previous messages\n", file=sys.stderr)
        else:
            selected = self.show_session_menu()
            if selected:
                self.session_id = selected
                restored_session = self.safe_execute(
                    lambda: self.backend.load_session_from_disk(selected)
                )
                if restored_session:
                    self.stream_output(f"Session restored with {len(restored_session.messages)} previous messages\n", file=sys.stderr)
                else:
                    self.stream_output(f"Warning: Could not restore session {selected}, starting fresh\n", file=sys.stderr)
                    self.session_id = str(uuid.uuid4())[:8]
            else:
                self.session_id = str(uuid.uuid4())[:8]

        prompt = ">>> "

        while True:
            try:
                user_input = input(prompt)

                if user_input.strip().lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break

                if not user_input.strip():
                    continue

                if user_input.strip() == 'clear':
                    self.output_buffer = VirtualScrollBuffer()
                    print("\033[2J\033[H", end="")
                    continue

                if user_input.strip() == '--list-sessions':
                    self.list_sessions_in_chat()
                    continue

                # MCP commands
                if user_input.strip().startswith('mcp '):
                    await self.handle_mcp_command(user_input.strip()[4:])
                    continue

                # Discovery commands
                if user_input.strip().startswith('discover '):
                    await self.handle_discover_command(user_input.strip()[9:])
                    continue

                # Discovery commands
                if user_input.strip().startswith('discover '):
                    await self.handle_discover_command(user_input.strip()[9:])
                    continue

                if self.backend:
                    response = self.safe_execute(
                        self.backend.process_message,
                        user_input, 
                        self.session_id
                    )
                    if response:
                        self.stream_output(response)
                    self.error_boundary.reset()

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
                continue
            except EOFError:
                break
            except Exception as e:
                self.stream_output(f"Error: {e}\n", file=sys.stderr)
                if self.verbose:
                    import traceback
                    traceback.print_exc()

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
    asyncio.run(ui.run())


if __name__ == "__main__":
    main()
