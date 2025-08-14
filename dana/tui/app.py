"""
Main Dana TUI application.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer

from .core.mock_agents import CoderAgent, PlannerAgent, ResearchAgent
from .core.runtime import DanaSandbox
from .core.taskman import task_manager
from .ui.agent_detail import AgentDetail
from .ui.agents_list import AgentFocused, AgentSelected, AgentsList
from .ui.repl_panel import TerminalREPL


class DanaTUI(App):
    """Main Dana TUI application."""

    CSS = """
    /* Global styles - use Textual's design system */
    Screen {
        background: $surface;
        color: $text;
    }
    
    /* Layout containers */
    .main-container {
        height: 100%;
    }
    
    .right-panel {
        width: 35%;
        min-width: 30;
    }
    
    .left-panel {
        width: 1fr;
    }
    
    .agents-section {
        height: 50%;
    }
    
    .detail-section {
        height: 50%;
    }
    
    /* Panel titles - minimal styling to respect terminal theme */
    .panel-title {
        background: $accent;
        color: $text;
        padding: 0 1;
        text-style: bold;
    }
    
    /* Terminal specific - use design system */
    #terminal-output {
        border: round $border;
        height: 1fr;
        margin: 0;
        background: $surface;
        color: $text;
        overflow: auto;
        scrollbar-size: 0 0;
    }
    
    
    #terminal-input-container {
        border: round $border;
        background: $surface;
        height: 5;
        padding: 0;
        margin: 0;
    }
    
    #terminal-prompt {
        width: 2;
        border: none;
        background: $surface;
        color: $accent;
        padding: 0;
    }
    
    #terminal-input {
        border: none;
        background: $surface;
        color: $text;
        width: 1fr;
        padding: 0;
        margin: 0;
    }
    
    /* Overlay autocomplete input */
    .overlay-input {
        display: block;
        background: $surface;
        border: none;
        color: $text;
        width: 100%;
        height: auto;
        margin: 0 0 0 0;
        padding: 0;
        position: relative;
    }
    
    /* Agents list - use design system */
    #agents-list {
        border: round $border;
        height: 1fr;
        background: $surface;
        color: $text;
        overflow: auto;
        scrollbar-size: 0 0;
    }
    
    /* Agent detail - use design system */
    #detail-log {
        border: round $border;
        height: 1fr;
        background: $surface;
        color: $text;
        overflow: auto;
        scrollbar-size: 0 0;
    }
    
    /* Footer - use design system */
    Footer {
        background: $accent;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel_focused", "Cancel", show=True),
        Binding("shift+escape", "cancel_all", "Cancel All", show=True),
        Binding("tab", "next_agent", "Next Agent", show=False),
        Binding("shift+tab", "prev_agent", "Prev Agent", show=False),
        Binding("f1", "help", "Help", show=True),
        Binding("ctrl+l", "clear_transcript", "Clear", show=False),
        Binding("ctrl+h", "show_history", "History", show=False),
        Binding("ctrl+shift+h", "clear_history", "Clear History", show=False),
        Binding("ctrl+s", "save_logs", "Save Logs", show=False),
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Dana Multi-Agent REPL"
        self.sub_title = "Interactive Agent Environment"

        # Use terminal's native color scheme
        self.dark = None  # Let terminal decide

        # Check for minimal styling environment variable
        import os

        self.minimal_style = os.getenv("DANA_TUI_MINIMAL", "").lower() in ("1", "true", "yes")

        # Initialize core systems
        self.sandbox = DanaSandbox()

        # UI components
        self.repl_panel: TerminalREPL | None = None
        self.agents_list: AgentsList | None = None
        self.agent_detail: AgentDetail | None = None

        # Create initial mock agents
        self._setup_initial_agents()

    def _setup_initial_agents(self) -> None:
        """Set up initial mock agents for demo."""
        agents = [ResearchAgent(), CoderAgent(), PlannerAgent()]

        for agent in agents:
            self.sandbox.register(agent)

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        with Horizontal(classes="main-container"):
            # Left panel: Unified REPL (input/output + execution)
            with Vertical(classes="left-panel"):
                self.repl_panel = TerminalREPL(self.sandbox)
                yield self.repl_panel

            # Right panel: Agents list + Agent detail
            with Vertical(classes="right-panel"):
                # Top: Agents list
                with Vertical(classes="agents-section"):
                    self.agents_list = AgentsList(self.sandbox)
                    yield self.agents_list

                # Bottom: Agent detail
                with Vertical(classes="detail-section"):
                    self.agent_detail = AgentDetail(self.sandbox)
                    yield self.agent_detail

        # Footer with key hints
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application when mounted."""
        # Set initial focus
        if self.repl_panel:
            self.repl_panel.focus_input()

        # Update all panels with initial state
        self._update_all_panels()

    def _update_all_panels(self) -> None:
        """Update all panels with current state."""
        focused_agent = self.sandbox.get_focused_name()

        if self.repl_panel:
            self.repl_panel.set_focused_agent(focused_agent)

        if self.agents_list:
            self.agents_list.update_focus(focused_agent)

        if self.agent_detail:
            self.agent_detail.set_focused_agent(focused_agent)

    @on(AgentSelected)
    def handle_agent_selected(self, event: AgentSelected) -> None:
        """Handle agent selection from agents list."""
        # Just highlight, don't change focus yet
        pass

    @on(AgentFocused)
    def handle_agent_focused(self, event: AgentFocused) -> None:
        """Handle agent focus change from agents list."""
        self.focus_agent(event.agent_name)

    def focus_agent(self, agent_name: str) -> None:
        """Focus on a specific agent."""
        if self.sandbox.set_focus(agent_name):
            self._update_all_panels()
            if self.repl_panel:
                self.repl_panel.focus_input()

    # Action handlers for keybindings
    def action_cancel_focused(self) -> None:
        """Cancel the focused agent's current task."""
        focused_agent = self.sandbox.get_focused_name()
        if focused_agent:
            cancelled = task_manager.cancel_agent_tasks(focused_agent)
            if cancelled > 0:
                if self.repl_panel:
                    self.repl_panel.add_system_message(f"Cancelled {cancelled} task(s) for {focused_agent}", "yellow")
                if self.agent_detail:
                    self.agent_detail.add_system_message(f"Tasks cancelled: {cancelled}", "yellow")
        else:
            # Try to cancel current REPL task
            if self.repl_panel:
                if not self.repl_panel.cancel_current_task():
                    self.repl_panel.add_system_message("No running tasks to cancel.", "dim")

    def action_cancel_all(self) -> None:
        """Cancel all running tasks."""
        cancelled = task_manager.cancel_all_tasks()
        if cancelled > 0:
            if self.repl_panel:
                self.repl_panel.add_system_message(f"Cancelled {cancelled} task(s) across all agents", "yellow")
            if self.agent_detail:
                self.agent_detail.add_system_message(f"All tasks cancelled: {cancelled}", "yellow")
        else:
            if self.repl_panel:
                self.repl_panel.add_system_message("No running tasks to cancel.", "dim")

    def action_next_agent(self) -> None:
        """Focus on the next agent."""
        agents = self.sandbox.list()
        if not agents:
            return

        current = self.sandbox.get_focused_name()
        if current and current in agents:
            current_idx = agents.index(current)
            next_idx = (current_idx + 1) % len(agents)
            self.focus_agent(agents[next_idx])
        elif agents:
            self.focus_agent(agents[0])

    def action_prev_agent(self) -> None:
        """Focus on the previous agent."""
        agents = self.sandbox.list()
        if not agents:
            return

        current = self.sandbox.get_focused_name()
        if current and current in agents:
            current_idx = agents.index(current)
            prev_idx = (current_idx - 1) % len(agents)
            self.focus_agent(agents[prev_idx])
        elif agents:
            self.focus_agent(agents[-1])

    def action_help(self) -> None:
        """Show help information."""
        if self.repl_panel:
            self.repl_panel.add_meta_command_result("No help available yet.")

    def action_clear_transcript(self) -> None:
        """Clear the REPL transcript."""
        if self.repl_panel:
            self.repl_panel.clear_transcript()

    def action_show_history(self) -> None:
        """Show command history."""
        if self.repl_panel:
            self.repl_panel.show_history()

    def action_clear_history(self) -> None:
        """Clear command history."""
        if self.repl_panel:
            self.repl_panel.clear_command_history()

    def action_save_logs(self) -> None:
        """Save logs to file."""
        # TODO: Implement log saving
        if self.repl_panel:
            self.repl_panel.add_system_message("Log saving not yet implemented.", "yellow")


def main():
    """Main entry point for the Dana TUI."""
    app = DanaTUI()
    app.run()
