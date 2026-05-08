"""Terminal UI - Simple, unified chat interface.

Single entry point for the Maximus chat experience.
"""
import sys
import os
import signal
import getpass
import uuid

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maximus.utils.ollama import ensure_ollama_running, get_default_model
from maximus.core.api import MaximusBackend


class TerminalUI:
    """Simple terminal-based chat interface."""
    
    def __init__(self, model: str = None, verbose: bool = False):
        self.verbose = verbose
        self.session_id = str(uuid.uuid4())[:8]
        self.backend = None
        self.model = model
        
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
        print(f"Maximus ready (session: {self.session_id})", file=sys.stderr)
        print("Type 'exit' or 'quit' to end session\n", file=sys.stderr)
        
    def run(self):
        """Main chat loop."""
        self.init_backend()
        
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
                
                # Clear screen
                if user_input.strip() == 'clear':
                    print("\033[2J\033[H", end="")
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
        elif args[i] == '--verbose' or args[i] == '-v':
            verbose = True
            i += 1
        elif args[i] == '--help' or args[i] == '-h':
            print_help()
            sys.exit(0)
        elif args[i] == '--version':
            print("Maximus v1.0.0")
            sys.exit(0)
        elif args[i] == 'doctor':
            run_diagnostics()
            sys.exit(0)
        else:
            i += 1
            
    return model, verbose


def print_help():
    """Print help message."""
    print("""Maximus - AI Coding Assistant

Usage:
    maximus                    Start interactive session
    maximus --model <name>    Use specific model
    maximus --verbose          Show debug information
    maximus doctor             Run diagnostics

Options:
    -m, --model <name>        Specify model (7b, 14b, fast, smart, think)
    -v, --verbose             Enable debug output
    -h, --help                Show this help
    --version                 Show version number

Examples:
    maximus                   Start session with auto-detected model
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
    sessions_dir = os.path.expanduser("~/.local/share/maximus/sessions")
    if os.path.exists(sessions_dir):
        sessions = os.listdir(sessions_dir)
        print(f"Sessions: {len(sessions)} saved")
    else:
        print("Sessions: None saved")
    
    print("\n=== End Diagnostics ===")


def main():
    """Main entry point."""
    model, verbose = parse_args()
    
    ui = TerminalUI(model=model, verbose=verbose)
    ui.run()


if __name__ == "__main__":
    main()