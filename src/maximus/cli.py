"""CLI for Maximus.ai."""

import sys
import asyncio
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="maximus")
def cli():
    """Maximus.ai - 100% Free, Unlimited, Capable Coding Agent."""
    pass


@cli.command()
@click.argument("prompt")
@click.option("--model", default="qwen2.5-coder:7b", help="Ollama model to use")
@click.option("--workdir", default=".", help="Working directory")
def run(prompt, model, workdir):
    """Run Maximus with a prompt."""
    from maximus.models import AgentConfig
    from maximus.core import AgentLoop

    config = AgentConfig(model=model, workdir=workdir)
    agent = AgentLoop(config)

    console.print(Panel.fit(
        f"[bold green]Maximus.ai[/bold green] running with model: {model}\n"
        f"Prompt: {prompt}",
        title="Maximus.ai"
    ))

    try:
        for event in agent.run(prompt):
            if event.type.value == "text_chunk":
                console.print(event.data.get("text", ""), end="")
            elif event.type.value == "tool_start":
                console.print(f"\n[dim]Tool: {event.data.get('tool')}[/dim]")
            elif event.type.value == "state_change":
                console.print(f"\n[blue]State: {event.data.get('state')}[/blue]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    console.print("\n[bold green]Done.[/bold green]")


@cli.command()
@click.option("--model", default="qwen2.5-coder:7b", help="Ollama model to use")
@click.option("--workdir", default=".", help="Working directory")
def chat(model, workdir):
    """Start interactive chat session."""
    from maximus.models import AgentConfig
    from maximus.core import AgentLoop

    config = AgentConfig(model=model, workdir=workdir)
    agent = AgentLoop(config)

    console.print(Panel.fit(
        f"[bold green]Maximus.ai[/bold green] Chat Mode (model: {model})\n"
        "Type 'exit' or 'quit' to stop.\n",
        title="Maximus.ai Interactive"
    ))

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ("exit", "quit", "q"):
            break

        if not user_input.strip():
            continue

        try:
            for event in agent.run(user_input):
                if event.type.value == "text_chunk":
                    console.print(event.data.get("text", ""), end="")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


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
            console.print(f"[green]OK[/green] Ollama running ({len(models)} models available)")
        else:
            console.print("[red]FAIL[/red] Ollama not responding")
    except Exception:
        console.print("[red]FAIL[/red] Ollama not running (start with: ollama serve)")

    # Check Python version
    import sys
    console.print(f"[green]OK[/green] Python {sys.version_info.major}.{sys.version_info.minor}")

    # Check directories
    for d in ["src/maximus", "tests", "docs"]:
        if Path(d).exists():
            console.print(f"[green]OK[/green] {d} exists")
        else:
            console.print(f"[red]FAIL[/red] {d} missing")


if __name__ == "__main__":
    cli()
