"""CLI for Maximus.ai."""

import sys
import asyncio
import logging
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from rich.markdown import Markdown

logger = logging.getLogger(__name__)
console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="maximus")
def cli():
    """Maximus.ai - 100% Free, Unlimited, Capable Coding Agent."""
    pass


# Model aliases for easy switching
MODEL_ALIASES = {
    "7b": "qwen2.5-coder:7b",
    "14b": "qwen2.5-coder:14b",
    "fast": "codellama:7b",
    "smart": "qwen2.5-coder:14b",
    "think": "deepseek-r1:7b",
    "think14b": "deepseek-r1:14b",
    "code": "qwen2.5-coder:7b",
    "coder": "qwen2.5-coder:7b",
    "llama": "llama3.1:8b",
    "vision": "llava:7b",
}


def resolve_model(model: str) -> str:
    """Resolve model alias to full model name."""
    if not model:
        return "qwen2.5-coder:7b"
    # Check if it's an alias
    if model.lower() in MODEL_ALIASES:
        return MODEL_ALIASES[model.lower()]
    # Otherwise return as-is (assume it's a valid Ollama model)
    return model


@cli.command()
@click.argument("prompt", required=False)
@click.option("--model", "-m", default="qwen2.5-coder:7b", help="Ollama model (or alias: 7b, 14b, fast, smart, think)")
@click.option("--workdir", default=".", help="Working directory")
@click.option("--session", "session_id", default=None, help="Resume existing session")
def run(prompt, model, workdir, session_id):
    """Run Maximus with a prompt or start interactive mode.
    
    Examples:
        maximus run "list files"
        maximus run "write code" -m 14b
        maximus run "debug this" --fast
        maximus run "think about it" --think
    """
    from maximus.models import AgentConfig
    from maximus.chat import ChatSession, SessionManager

    # Resolve model alias
    resolved_model = resolve_model(model)
    
    config = AgentConfig(model=resolved_model, workdir=workdir)
    
    # If prompt provided, run single shot
    if prompt:
        console.print(Panel.fit(
            f"[bold green]Maximus.ai[/bold green] running with model: {resolved_model}\n"
            f"Prompt: {prompt}",
            title="Maximus.ai"
        ))
        
        # Create session for this run
        session = ChatSession(workdir=workdir, config=config)
        
        try:
            # Use sync generator instead of async
            for event in session.agent.run(prompt):
                if event.type.value == "text_chunk":
                    txt = event.data.get("text", "")
                    if txt:
                        print(txt, end="")
                elif event.type.value == "tool_start":
                    print(f"\n[Tool: {event.data.get('tool')}]")
                elif event.type.value == "tool_end":
                    success = event.data.get("success", False)
                    print(f" [{'OK' if success else 'FAIL'}]")
                elif event.type.value == "state_change":
                    print(f"\n--> {event.data.get('state', '').upper()}")
                elif event.type.value == "error":
                    print(f"\nERROR: {event.data.get('error')}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            print(traceback.format_exc())
            sys.exit(1)
        
        print("\n\nDone.")
    else:
        # No prompt - start interactive chat
        ctx.invoke(chat, model=model, workdir=workdir, session_id=session_id)


@cli.command()
@click.option("--model", "-m", default="qwen2.5-coder:7b", help="Ollama model (or alias: 7b, 14b, fast, smart, think)")
@click.option("--workdir", default=".", help="Working directory")
@click.option("--session", "session_id", default=None, help="Resume existing session")
def chat(model, workdir, session_id):
    """Start interactive chat session with full conversation history.
    
    Examples:
        maximus chat
        maximus chat -m 14b
        maximus chat --think
    """
    from maximus.models import AgentConfig
    from maximus.chat import ChatSession, SessionManager
    from maximus.chat.project_context import get_project_context

    resolved_model = resolve_model(model)
    config = AgentConfig(model=resolved_model, workdir=workdir)
    manager = SessionManager(workdir=workdir)
    
    # Get or create session
    if session_id:
        session = manager.get_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            sys.exit(1)
        console.print(f"[green]Resumed session: {session_id}[/green]")
    else:
        session = manager.create_session(workdir=workdir, config=config)
    
    # Auto-detect and inject project context if not already set
    if not session.project_context:
        try:
            session.project_context = get_project_context(workdir)
            if session.project_context:
                console.print("[dim]📦 Project context loaded automatically[/dim]")
        except Exception as e:
            logger.debug(f"Failed to detect project context: {e}")
    
    console.print(Panel.fit(
        f"[bold green]Maximus.ai[/bold green] Chat Mode\n"
        f"Model: {model} | Session: {session.session_id}\n"
        f"Type [bold]/help[/bold] for commands, [bold]exit[/bold] to quit.",
        title="Maximus.ai Interactive"
    ))
    
    # Print recent history if resuming
    history = session.get_history(count=5)
    if history and session.turn_count > 0:
        console.print("\n[dim]Recent conversation:[/dim]")
        for msg in history[-4:]:
            if msg.get("role") == "user":
                console.print(f"[cyan]You:[/cyan] {msg['content'][:80]}...")
            elif msg.get("role") == "assistant":
                console.print(f"[green]Maximus:[/green] {msg['content'][:80]}...")
    
    while True:
        try:
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input.strip():
            continue

        # Check for slash commands
        if user_input.startswith("/"):
            if not handle_slash_command(user_input, session, manager):
                break  # Exit command
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            break

        try:
            # Stream responses
            for event in session.chat(user_input):
                if event.type.value == "text_chunk":
                    console.print(event.data.get("text", ""), end="")
                elif event.type.value == "tool_start":
                    console.print(f"\n[dim]⚡ {event.data.get('tool')}[/dim]")
                elif event.type.value == "tool_end":
                    success = event.data.get("success", False)
                    color = "green" if success else "red"
                    console.print(f"[{color}]✓ Done[/{color}]")
                elif event.type.value == "state_change":
                    state = event.data.get("state", "")
                    console.print(f"\n[blue]🔄 {state.upper()}[/blue]")
                elif event.type.value == "error":
                    console.print(f"\n[red]❌ Error: {event.data.get('error')}[/red]")
            
            # Save session after each turn
            session.save()
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            session.save()

    # Save final state
    session.save()
    console.print(f"\n[green]Session saved: {session.session_id}[/green]")


def handle_slash_command(cmd: str, session, manager) -> bool:
    """Handle slash commands. Returns False to exit, True to continue."""
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    handlers = {
        "/help": lambda: show_help(),
        "/sessions": lambda: list_sessions(manager),
        "/new": lambda: new_session(manager),
        "/resume": lambda: resume_session(manager, args),
        "/delete": lambda: delete_session(manager, args),
        "/clear": lambda: clear_history(session),
        "/history": lambda: show_history(session),
        "/pending": lambda: show_pending(session),
        "/approve": lambda: approve_edit(session, args),
        "/reject": lambda: reject_edit(session, args),
        "/project": lambda: set_project(session, args),
    }
    
    handler = handlers.get(command)
    if handler:
        return handler()
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("Type /help for available commands")
        return True


def show_help():
    """Show available commands."""
    table = Table(title="Maximus.ai Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")
    
    commands = [
        ("/help", "Show this help message"),
        ("/sessions", "List all sessions"),
        ("/new", "Start a new session"),
        ("/resume <id>", "Resume a specific session"),
        ("/delete <id>", "Delete a session"),
        ("/clear", "Clear conversation history"),
        ("/history", "Show conversation history"),
        ("/pending", "Show pending edits"),
        ("/approve <id>", "Approve a pending edit"),
        ("/reject <id>", "Reject a pending edit"),
        ("/project <type>", "Set project type (python, node, go, rust)"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    
    console.print(table)
    return True


def list_sessions(manager):
    """List all sessions."""
    sessions = manager.list_sessions()
    
    if not sessions:
        console.print("[yellow]No sessions found.[/yellow]")
        return True
    
    table = Table(title="Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Turns", style="yellow")
    table.add_column("Last Activity", style="dim")
    table.add_column("Last Message", style="white")
    
    for s in sessions:
        table.add_row(
            s["session_id"][:20] + "...",
            s["status"],
            str(s["turn_count"]),
            s["last_activity"][:19],
            s.get("last_message", "")[:40]
        )
    
    console.print(table)
    return True


def new_session(manager):
    """Start a new session (creates new ChatSession)."""
    session = manager.create_session()
    console.print(f"[green]Created new session: {session.session_id}[/green]")
    console.print("[yellow]Note: Use /resume with the session ID to return to this session.[/yellow]")
    return True


def resume_session(manager, session_id: str):
    """Resume a session."""
    if not session_id:
        console.print("[red]Usage: /resume <session_id>[/red]")
        return True
    
    session = manager.get_session(session_id)
    if session:
        console.print(f"[green]Session loaded: {session_id}[/green]")
        show_history(session)
    else:
        console.print(f"[red]Session not found: {session_id}[/red]")
    return True


def delete_session(manager, session_id: str):
    """Delete a session."""
    if not session_id:
        console.print("[red]Usage: /delete <session_id>[/red]")
        return True
    
    if manager.delete_session(session_id):
        console.print(f"[green]Deleted: {session_id}[/green]")
    else:
        console.print(f"[red]Failed to delete: {session_id}[/red]")
    return True


def clear_history(session):
    """Clear conversation history."""
    session.clear_history()
    console.print("[green]History cleared.[/green]")
    return True


def show_history(session):
    """Show conversation history."""
    history = session.get_history(count=20)
    
    if not history:
        console.print("[yellow]No history.[/yellow]")
        return True
    
    for i, msg in enumerate(history):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:100]
        
        if role == "user":
            console.print(f"[cyan]{i+1}. You:[/cyan] {content}")
        elif role == "assistant":
            console.print(f"[green]{i+1}. Maximus:[/green] {content}")
    return True


def show_pending(session):
    """Show pending edits."""
    pending = session.get_pending_edits()
    
    if not pending:
        console.print("[yellow]No pending edits.[/yellow]")
        return True
    
    table = Table(title="Pending Edits")
    table.add_column("ID", style="cyan")
    table.add_column("Tool", style="yellow")
    table.add_column("File", style="white")
    table.add_column("Created", style="dim")
    
    for edit in pending:
        path = edit.args.get("path", "unknown")
        table.add_row(edit.id[:8], edit.tool, path, str(edit.created_at)[:19])
    
    console.print(table)
    console.print("\nUse /approve <id> or /reject <id>")
    return True


def approve_edit(session, edit_id: str):
    """Approve a pending edit."""
    if not edit_id:
        console.print("[red]Usage: /approve <edit_id>[/red]")
        return True
    
    if session.approve_edit(edit_id):
        console.print(f"[green]Edit approved: {edit_id}[/green]")
    else:
        console.print(f"[red]Edit not found: {edit_id}[/red]")
    return True


def reject_edit(session, edit_id: str):
    """Reject a pending edit."""
    if not edit_id:
        console.print("[red]Usage: /reject <edit_id>[/red]")
        return True
    
    if session.reject_edit(edit_id):
        console.print(f"[yellow]Edit rejected: {edit_id}[/yellow]")
    else:
        console.print(f"[red]Edit not found: {edit_id}[/red]")
    return True


def set_project(session, project_type: str):
    """Set project type."""
    if not project_type:
        console.print("[red]Usage: /project <python|node|go|rust|java>[/red]")
        return True
    
    project_contexts = {
        "python": "Python project with pip, venv, pytest",
        "node": "Node.js project with npm, package.json",
        "go": "Go project with go.mod",
        "rust": "Rust project with Cargo.toml",
        "java": "Java project with Maven/Gradle"
    }
    
    context = project_contexts.get(project_type.lower())
    if context:
        session.set_project_context(context)
        console.print(f"[green]Project type set: {project_type}[/green]")
    else:
        console.print(f"[red]Unknown project type: {project_type}[/red]")
        console.print(f"Available: {', '.join(project_contexts.keys())}")
    return True


@cli.command()
def sessions():
    """List all chat sessions."""
    from maximus.chat import SessionManager
    manager = SessionManager()
    list_sessions(manager)


@cli.command()
@click.argument("session_id")
def session_delete(session_id):
    """Delete a session."""
    from maximus.chat import SessionManager
    manager = SessionManager()
    delete_session(manager, session_id)


@cli.command()
def status():
    """Check Maximus.ai system status."""
    import httpx

    console.print("[bold]Maximus.ai Status Check[/bold]\n")

    # Check Ollama
    ollama_url = "http://localhost:11434"
    try:
        resp = httpx.get(f"{ollama_url}/api/tags", timeout=3)
        if resp.is_success:
            models = resp.json().get("models", [])
            console.print(f"[green]✓[/green] Ollama running ({len(models)} models)")
            for m in models[:5]:
                console.print(f"  - {m['name']}")
        else:
            console.print("[red]✗[/red] Ollama not responding")
    except Exception:
        console.print("[red]✗[/red] Ollama not running (start with: ollama serve)")

    # Check sessions directory
    from maximus.chat import SessionManager
    manager = SessionManager()
    session_count = len(manager.list_sessions())
    console.print(f"[green]✓[/green] Sessions: {session_count}")

    # Check Python
    import sys
    console.print(f"[green]✓[/green] Python {sys.version_info.major}.{sys.version_info.minor}")


@cli.command()
def models():
    """List available Ollama models with aliases.
    
    Examples:
        maximus models
        maximus models --available
    """
    import httpx
    from rich.table import Table
    
    console.print("[bold]Available Models[/bold]\n")
    
    # Get models from Ollama
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if resp.is_success:
            ollama_models = resp.json().get("models", [])
            
            # Show aliases table
            alias_table = Table(title="Model Aliases")
            alias_table.add_column("Alias", style="cyan")
            alias_table.add_column("Model", style="green")
            alias_table.add_column("Use With", style="dim")
            
            for alias, model in MODEL_ALIASES.items():
                alias_table.add_row(alias, model, f"-m {alias}")
            
            console.print(alias_table)
            console.print("")
            
            # Show available models
            avail_table = Table(title="Ollama Available Models")
            avail_table.add_column("Model", style="green")
            avail_table.add_column("Size", style="yellow")
            
            for m in ollama_models:
                size_gb = m.get('size', 0) / (1024**3)
                avail_table.add_row(m['name'], f"{size_gb:.1f} GB")
            
            console.print(avail_table)
        else:
            console.print("[red]Failed to get models from Ollama[/red]")
    except Exception as e:
        console.print(f"[red]Ollama not available: {e}[/red]")
        console.print("[yellow]Start Ollama with: ollama serve[/yellow]")


@cli.command()
@click.argument("query")
@click.option("--language", "-l", default="python", help="Language: python, javascript, rust")
@click.option("--limit", "-n", default=10, help="Number of results")
def discover(query, language, limit):
    """Discover open-source packages for your project.
    
    Example: maximus discover "async http client"
    """
    from maximus.discovery import get_package_discovery
    from rich.progress import Progress
    
    console.print(f"[bold]Searching for:[/bold] {query} (language: {language})")
    
    async def search():
        discovery = get_package_discovery()
        results = await discovery.discover(query, languages=[language], limit=limit)
        return results
    
    results = asyncio.run(search())
    
    if not results:
        console.print("[yellow]No packages found.[/yellow]")
        return
    
    # Display results
    table = Table(title=f"Package Results for '{query}'")
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    table.add_column("Registry", style="dim")
    
    for pkg in results:
        table.add_row(
            pkg.name,
            pkg.version or "latest",
            pkg.description[:60] + "..." if len(pkg.description) > 60 else pkg.description,
            pkg.registry
        )
    
    console.print(table)
    console.print(f"\n[dim]Found {len(results)} packages[/dim]")


@cli.command()
@click.option("--show-defaults", is_flag=True, help="Show default configuration")
def config(show_defaults):
    """Show or edit Maximus configuration.
    
    Examples:
        maximus config
        maximus config --show-defaults
    """
    from maximus.models import AgentConfig
    from pathlib import Path
    
    config_path = Path.home() / ".maximus" / "config.json"
    
    console.print("[bold]Maximus Configuration[/bold]\n")
    
    # Show current config
    if config_path.exists():
        console.print(f"[green]Config file:[/green] {config_path}")
        console.print(f"[dim]Use --show-defaults to see all available options[/dim]")
    else:
        console.print(f"[yellow]No config file found at: {config_path}[/yellow]")
        console.print("[dim]Config will use defaults[/dim]")
    
    console.print("\n[bold]Current Defaults:[/bold]")
    cfg = AgentConfig()
    console.print(f"  model: {cfg.model}")
    console.print(f"  workdir: {cfg.workdir}")
    console.print(f"  max_model_calls: {cfg.max_model_calls}")
    console.print(f"  context_window: {cfg.context_window}")
    console.print(f"  trust_level: {cfg.trust_level.value}")


@cli.command()
def memory():
    """Show Maximus memory status and contents.
    
    Examples:
        maximus memory
        maximus memory --clear
    """
    from pathlib import Path
    from maximus.memory import MemoryMesh
    
    mem_dir = Path.home() / ".maximus" / "memory"
    
    console.print("[bold]Maximus Memory Status[/bold]\n")
    
    if not mem_dir.exists():
        console.print("[yellow]Memory directory not found[/yellow]")
        return
    
    # Show memory directories
    console.print(f"[green]Memory directory:[/green] {mem_dir}")
    
    subdirs = ['short_term', 'long_term', 'episodic', 'semantic', 'working']
    for subdir in subdirs:
        path = mem_dir / subdir
        if path.exists():
            files = list(path.glob("*"))
            console.print(f"  {subdir}: {len(files)} items")
        else:
            console.print(f"  {subdir}: (empty)")
    
    console.print("\n[dim]Use MemoryMesh API for detailed operations[/dim]")


@cli.command()
def hooks():
    """List available and registered hooks.
    
    Examples:
        maximus hooks
    """
    from maximus.hooks import get_hook_manager
    
    console.print("[bold]Maximus Hooks[/bold]\n")
    
    manager = get_hook_manager()
    hooks = manager.list_hooks()
    
    if not hooks:
        console.print("[yellow]No hooks registered[/yellow]")
        console.print("[dim]Add hooks in ~/.maximus/hooks/[/dim]")
        return
    
    for event_name, count in hooks.items():
        console.print(f"  {event_name}: {count} handlers")
    
    console.print("\n[dim]Available events: PRE_RUN, POST_RUN, PRE_TOOL, POST_TOOL, ON_STATE_CHANGE, ON_ERROR, ON_SUCCESS[/dim]")


if __name__ == "__main__":
    cli()