"""
Agent detail widget for Dana TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import time

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static

from dana.registry import AGENT_REGISTRY

from ..core.events import AgentEvent, Done, Error, FinalResult, Progress, Status, Token, ToolEnd, ToolStart
from ..core.runtime import DanaSandbox
from .copyable_richlog import CopyableRichLog


class ThinkingEntry:
    """Represents an entry in the thinking feed."""

    def __init__(self, timestamp: float, event_type: str, content: str, style: str = ""):
        self.timestamp = timestamp
        self.event_type = event_type
        self.content = content
        self.style = style

    def format_line(self) -> str:
        """Format the entry as a display line."""
        time_str = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        if self.style:
            return f"[{self.style}]{time_str} {self.event_type}: {self.content}[/{self.style}]"
        else:
            return f"{time_str} {self.event_type}: {self.content}"


class AgentDetail(Vertical):
    """Widget showing detailed information about the focused agent."""

    # Reactive attributes
    focused_agent: reactive[str | None] = reactive(None)

    def __init__(self, sandbox: DanaSandbox, **kwargs):
        super().__init__(**kwargs)
        self.sandbox = sandbox
        self._text_log: CopyableRichLog | None = None
        self._thinking_entries: list[ThinkingEntry] = []
        self._max_entries = 200  # Keep last 200 entries
        self._last_update = 0.0
        self._update_timer = None

    def compose(self) -> ComposeResult:
        """Create the agent detail UI."""
        yield Static("🔍 Agent Detail", classes="panel-title", id="detail-title")
        self._text_log = CopyableRichLog(highlight=True, markup=True, wrap=False, id="detail-log", auto_scroll=True)
        yield self._text_log

    def on_mount(self) -> None:
        """Initialize the agent detail when mounted."""
        self.update_title()
        self.start_update_timer()

        # Add initial message
        if self._text_log:
            self._text_log.write("[dim]Select an agent to see thinking details...[/dim]\n")

    def on_unmount(self) -> None:
        """Clean up when unmounted."""
        if self._update_timer:
            self._update_timer.cancel()

    def start_update_timer(self) -> None:
        """Start the periodic update timer."""

        async def update_loop():
            while True:
                await self.app.sleep(0.5)  # Update at 2Hz
                self.refresh_display()

        if self._update_timer:
            self._update_timer.cancel()
        self._update_timer = asyncio.create_task(update_loop())

    def update_title(self) -> None:
        """Update the panel title with focused agent info."""
        title_widget = self.query_one("#detail-title", Static)

        focused_name = self.focused_agent
        if focused_name:
            # Get agent from registry
            agent = None
            for instance in AGENT_REGISTRY.list_instances():
                if hasattr(instance, "name") and instance.name == focused_name:
                    agent = instance
                    break

            if agent:
                metrics = agent.get_metrics()
                step = metrics.get("current_step", "idle")
                elapsed = metrics.get("elapsed_time", 0.0)

                if elapsed > 0:
                    title_text = f"🔍 {focused_name} • {step} • {elapsed:.1f}s"
                else:
                    title_text = f"🔍 {focused_name} • {step}"

                title_widget.update(title_text)
                self.focused_agent = focused_name
                return

        title_widget.update("Agent Detail")
        self.focused_agent = None

    def set_focused_agent(self, agent_name: str | None) -> None:
        """Set the focused agent and update display."""
        if agent_name != self.focused_agent:
            # Clear existing entries when switching agents
            if agent_name != self.focused_agent:
                self._thinking_entries.clear()
                if self._text_log:
                    self._text_log.clear()
                    if agent_name:
                        self._text_log.write(f"[bold]Thinking feed for {agent_name}[/bold]\n\n")
                    else:
                        self._text_log.write("[dim]Select an agent to see thinking details...[/dim]\n")

            self.focused_agent = agent_name
            self.update_title()

    def handle_agent_event(self, task_id: str, event: AgentEvent, agent_name: str) -> None:
        """Handle an event from an agent."""
        # Only show events for the focused agent
        if agent_name != self.focused_agent:
            return

        timestamp = time.time()
        entry = None

        if isinstance(event, Status):
            content = f"{event.step}"
            if event.detail:
                content += f" - {event.detail}"
            entry = ThinkingEntry(timestamp, "STATUS", content, "cyan")

        elif isinstance(event, ToolStart):
            args_str = ""
            if event.args:
                # Format args nicely, truncating if too long
                args_repr = str(event.args)
                if len(args_repr) > 50:
                    args_repr = args_repr[:47] + "..."
                args_str = f" {args_repr}"

            content = f"{event.name}{args_str}"
            entry = ThinkingEntry(timestamp, "TOOL→", content, "yellow")

        elif isinstance(event, ToolEnd):
            status = "OK" if event.ok else "ERR"
            ms_str = f"{event.ms}ms" if event.ms > 0 else ""
            content = f"{event.name} [{status}] {ms_str}"
            style = "green" if event.ok else "red"
            entry = ThinkingEntry(timestamp, "TOOL✓", content, style)

        elif isinstance(event, Progress):
            content = f"{event.pct:.1f}% complete"
            entry = ThinkingEntry(timestamp, "PROGRESS", content, "blue")

        elif isinstance(event, FinalResult):
            # Summarize the final result
            data_summary = ""
            if isinstance(event.data, dict):
                if "elapsed" in event.data:
                    data_summary += f"elapsed: {event.data['elapsed']}s"
                if "status" in event.data:
                    if data_summary:
                        data_summary += ", "
                    data_summary += f"status: {event.data['status']}"
                # Add other interesting keys
                for key in ["tokens", "lines_of_code", "papers_found", "confidence"]:
                    if key in event.data:
                        if data_summary:
                            data_summary += ", "
                        data_summary += f"{key}: {event.data[key]}"

            content = "Completed"
            if data_summary:
                content += f" ({data_summary})"
            entry = ThinkingEntry(timestamp, "RESULT", content, "green bold")

        elif isinstance(event, Error):
            content = event.message
            entry = ThinkingEntry(timestamp, "ERROR", content, "red bold")

        elif isinstance(event, Done):
            content = "Task finished"
            entry = ThinkingEntry(timestamp, "DONE", content, "dim")

        # Skip Token events - they're handled by the REPL panel
        elif isinstance(event, Token):
            return

        if entry:
            self.add_thinking_entry(entry)

    def add_thinking_entry(self, entry: ThinkingEntry) -> None:
        """Add a new thinking entry."""
        self._thinking_entries.append(entry)

        # Trim to max entries
        if len(self._thinking_entries) > self._max_entries:
            self._thinking_entries = self._thinking_entries[-self._max_entries :]

        # Add to display
        if self._text_log:
            self._text_log.write(entry.format_line() + "\n")

    def refresh_display(self) -> None:
        """Refresh the display with current metrics."""
        now = time.perf_counter()
        if now - self._last_update < 0.5:  # Limit to 2Hz
            return

        self._last_update = now
        self.update_title()

    def clear_thinking_feed(self) -> None:
        """Clear the thinking feed."""
        self._thinking_entries.clear()
        if self._text_log:
            self._text_log.clear()
            focused_name = self.focused_agent
            if focused_name:
                self._text_log.write(f"[bold]Thinking feed for {focused_name}[/bold]\n\n")
            else:
                self._text_log.write("[dim]Select an agent to see thinking details...[/dim]\n")

    def add_system_message(self, message: str, style: str = "dim") -> None:
        """Add a system message to the thinking feed."""
        if self._text_log:
            timestamp = time.time()
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            self._text_log.write(f"[{style}]{time_str} SYSTEM: {message}[/{style}]\n")

    def get_thinking_summary(self) -> dict[str, int]:
        """Get a summary of recent thinking activity."""
        if not self._thinking_entries:
            return {}

        # Count events in the last 60 seconds
        cutoff = time.time() - 60
        recent_entries = [e for e in self._thinking_entries if e.timestamp > cutoff]

        summary = {}
        for entry in recent_entries:
            event_type = entry.event_type
            summary[event_type] = summary.get(event_type, 0) + 1

        return summary

    def export_thinking_log(self) -> str:
        """Export the thinking log as text."""
        lines = []
        for entry in self._thinking_entries:
            # Strip markup for export
            content = entry.content
            lines.append(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry.timestamp))} {entry.event_type}: {content}")

        return "\n".join(lines)

    def get_agent_status_summary(self) -> str:
        """Get a one-line status summary for the focused agent."""
        focused_name = self.focused_agent
        if not focused_name:
            return "No agent focused"

        # Get agent from registry
        agent = None
        for instance in AGENT_REGISTRY.list_instances():
            if hasattr(instance, "name") and instance.name == focused_name:
                agent = instance
                break

        if not agent:
            return f"Agent {focused_name} not found"

        metrics = agent.get_metrics()
        step = metrics.get("current_step", "idle")
        is_running = metrics.get("is_running", False)
        elapsed = metrics.get("elapsed_time", 0.0)

        status = "●" if is_running else "○"

        if elapsed > 0:
            return f"{status} {focused_name}: {step} ({elapsed:.1f}s)"
        else:
            return f"{status} {focused_name}: {step}"
