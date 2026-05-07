"""Textual TUI application for Maximus.ai."""

import asyncio
from pathlib import Path
from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog, Static

from maximus.core.loop import AgentLoop
from maximus.models import AgentConfig, CognitiveState


class AgentStatusBar(Static):
    """Status bar showing agent state."""

    state_display = reactive(CognitiveState.INIT)
    tool_count = reactive(0)
    step_count = reactive(0)

    def render(self) -> str:
        color_map = {
            CognitiveState.INIT: "blue",
            CognitiveState.PLAN: "yellow",
            CognitiveState.ACT: "magenta",
            CognitiveState.OBSERVE: "cyan",
            CognitiveState.REFLECT: "green",
            CognitiveState.ADAPT: "bold yellow",
            CognitiveState.COMMIT: "bold blue",
            CognitiveState.PAUSE: "bold green",
        }
        color = color_map.get(self.state_display, "white")
        return (
            f"[{color}]State: {self.state_display.value}[/{color}]  |  "
            f"Tools: {self.tool_count}  |  "
            f"Steps: {self.step_count}"
        )


class ChatScreen(Screen):
    """Main chat screen."""

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
    ]

    def __init__(self, config: AgentConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.agent: Optional[AgentLoop] = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield AgentStatusBar(id="status")
            yield RichLog(id="output", highlight=True, markup=True, wrap=True)
            yield Input(id="input", placeholder="Type your prompt here...")
            yield Footer()

    def on_mount(self) -> None:
        self.agent = AgentLoop(self.config)
        output = self.query_one("#output", RichLog)
        output.write("[bold green]╔══════════════════════════════════════════╗")
        output.write("[bold green]║       Maximus.ai - Terminal UI          ║")
        output.write("[bold green]║   100% Free, Unlimited, Capable         ║")
        output.write("[bold green]╚══════════════════════════════════════════╝")
        output.write("")
        output.write(f"[dim]Model: {self.config.model}")
        output.write(f"[dim]Workdir: {self.config.workdir}")
        output.write("")
        self._update_status()

    def _update_status(self) -> None:
        status = self.query_one("#status", AgentStatusBar)
        if self.agent:
            status.state_display = self.agent.state
            from maximus.tools.registry import get_registry
            registry = get_registry()
            status.tool_count = len(registry.list_tools()) if registry else 0
            status.step_count = self.agent.model_calls

    def on_input_submitted(self, event: Input.Submitted) -> None:
        prompt = event.value.strip()
        if not prompt:
            return

        if prompt.lower() in ("exit", "quit", "q"):
            self.app.exit()
            return

        if prompt.lower() == "clear":
            self.query_one("#output", RichLog).clear()
            self.query_one("#input", Input).value = ""
            return

        self.query_one("#input", Input).value = ""
        self.query_one("#input", Input).disabled = True
        self.run_agent(prompt)

    @work(exclusive=True)
    async def run_agent(self, prompt: str) -> None:
        output = self.query_one("#output", RichLog)
        if not self.agent:
            return

        output.write(f"\n[bold cyan]You:[/bold cyan] {prompt}")
        output.write("")

        try:
            async for event in self.agent.run_async(prompt):
                self._update_status()

                if event.type.value == "text_chunk":
                    text = event.data.get("text", "")
                    if text:
                        output.write(text, end="")
                elif event.type.value == "tool_start":
                    tool = event.data.get("tool", "unknown")
                    output.write(f"\n[dim]🔧 Tool: {tool}[/dim]")
                elif event.type.value == "tool_end":
                    result = event.data.get("result", {})
                    status = "ok" if result.get("success") else "error"
                    icon = "✅" if status == "ok" else "❌"
                    output.write(f"\n[dim]{icon} Result ({status})[/dim]")
                elif event.type.value == "state_change":
                    new_state = event.data.get("state", "")
                    output.write(f"\n[blue]⏳ State → {new_state}[/blue]")
                elif event.type.value == "turn_done":
                    output_data = event.data.get("output", {})
                    content = output_data.get("content", "")
                    output.write(f"\n\n[bold green]Result:[/bold green] {content}")
                    output.write("\n[bold green]✓ Done[/bold green]")

            # Check if we got a turn_done event
            if self.agent.state != CognitiveState.PAUSE:
                pass
        except Exception as e:
            output.write(f"\n[red]❌ Error: {e}[/red]")
        finally:
            self.query_one("#input", Input).disabled = False
            self.query_one("#input", Input).focus()
            self._update_status()

    def action_clear(self) -> None:
        self.query_one("#output", RichLog).clear()

    def action_quit(self) -> None:
        self.app.exit()


class MaximusTUI(App):
    """Maximus.ai Textual TUI Application."""

    TITLE = "Maximus.ai"
    SUB_TITLE = "100% Free, Unlimited, Capable Coding Agent"
    CSS = """
    Screen {
        background: #0a0e14;
    }

    #status {
        height: 1;
        padding: 0 1;
        background: #1a1e24;
        color: #b3b1ad;
        dock: top;
    }

    #output {
        height: 1fr;
        border: none;
        background: #0a0e14;
        color: #c0c0c0;
        margin: 0;
        padding: 0 1;
    }

    #input {
        dock: bottom;
        height: 3;
        margin: 0 1 1 1;
        background: #1a1e24;
        color: #c0c0c0;
        border: solid #333;
    }

    #input:focus {
        border: solid #4a9eff;
    }

    Footer {
        background: #1a1e24;
        color: #666;
    }

    RichLog {
        scrollbar-gutter: stable;
    }
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__()
        self.config = config or AgentConfig()

    def on_mount(self) -> None:
        self.push_screen(ChatScreen(self.config))


def main():
    """Entry point for the TUI."""
    import sys

    model = "qwen2.5-coder:7b"
    workdir = "."

    args = sys.argv[1:]
    if args:
        i = 0
        while i < len(args):
            if args[i] == "--model" and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == "--workdir" and i + 1 < len(args):
                workdir = args[i + 1]
                i += 2
            else:
                i += 1

    config = AgentConfig(model=model, workdir=workdir)
    app = MaximusTUI(config)
    app.run()


if __name__ == "__main__":
    main()
