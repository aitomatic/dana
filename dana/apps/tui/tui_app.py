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

from dana.registry import AGENT_REGISTRY

from .core.runtime import DanaSandbox
from .core.taskman import task_manager
from .ui.agent_detail import AgentDetail
from .ui.agents_list import AgentFocused, AgentSelected, AgentsList
from .ui.log_panel import LogPanel
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
    
    .content-area {
        height: 1fr;
    }
    
    .right-panel {
        width: 35%;
        min-width: 30;
    }
    
    .left-panel {
        width: 1fr;
    }
    
    .agents-section {
        height: 30%;
    }
    
    .detail-section {
        height: 1fr;
    }
    
    /* Panel titles - minimal styling to respect terminal theme */
    .panel-title {
        background: $accent;
        color: $text;
        text-style: bold;
    }
    
    /* Terminal specific - use design system */
    #terminal-output {
        border: round $accent;
        height: 1fr;
        background: $surface;
        color: $text;
        overflow: auto;
        scrollbar-size: 0 0;
    }
    
    
    #terminal-input-container {
        border: round $accent;
        background: $surface;
        height: 5;
    }
    
    #terminal-prompt {
        width: 2;
        border: none;
        background: $surface;
        color: $accent;
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
        margin: 0;
        padding: 0;
        position: relative;
    }
    

    
    /* Agents list - use design system */
    #agents-list {
        border: round $accent;
        background: $surface;
        color: $text;
        overflow-x: scroll;  /* Force horizontal scrollbar to always show */
        overflow-y: auto;
        scrollbar-size: 1 1;
        scrollbar-background: $accent 30%;
        scrollbar-color: $text;
        scrollbar-color-hover: $text 80%;
        scrollbar-color-active: $text;
    }
    
    /* Force agent list items to not wrap and show full width */
    #agents-list ListItem {
        min-width: 80;
        overflow-x: hidden;
        overflow-y: hidden;
    }
    
    #agents-list Label {
        min-width: 80;
        width: auto;
    }
    
    /* Agent detail - use design system */
    #detail-log {
        border: round $accent;
        background: $surface;
        color: $text;
        overflow: auto;
        scrollbar-size: 0 0;
    }
    
    /* Footer - use design system */
    Footer {
        background: $accent;
        color: $text;
        opacity: 0.5
    }
    
    /* Log panel - use design system */
    #log-panel {
        border: round $accent;
        background: $surface;
        color: $text;
        height: 30%;
        min-height: 8;
        display: none;
    }
    
    #log-output {
        border: none;
        height: 99%;
        background: $surface;
        color: $text;
        overflow: auto;
        scrollbar-size: 0 2;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+l", "toggle_logs", "Logs", show=True),
        # Binding("escape", "cancel_focused", "Cancel", show=false),
        # Binding("shift+escape", "cancel_all", "Cancel All", show=False),
        Binding("f1", "help", "Help", show=True),
        Binding("tab", "next_agent", "Next Agent", show=False),
        Binding("shift+tab", "prev_agent", "Prev Agent", show=False),
        Binding("ctrl+x", "clear_transcript", "Clear", show=False),
        Binding("ctrl+h", "show_history", "History", show=False),
        Binding("ctrl+shift+h", "clear_history", "Clear History", show=False),
        Binding("ctrl+s", "save_logs", "Save Logs", show=False),
        Binding("ctrl+r", "sync_registry", "Sync Registry", show=True),
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
        self.log_panel: LogPanel | None = None

        # TUI-managed focused agent state
        self._focused_agent: str | None = None

        # Queue for pending agent updates (in case events fire before UI is ready)
        self._pending_agent_updates = []

        # Register for AGENT_REGISTRY events
        self._setup_registry_events()

    def _setup_registry_events(self) -> None:
        """Set up event handlers for AGENT_REGISTRY events."""
        AGENT_REGISTRY.on_registered(self._on_agent_registered)
        AGENT_REGISTRY.on_unregistered(self._on_agent_unregistered)

    def _on_agent_registered(self, agent_id: str, agent_instance) -> None:
        """Handle agent registration events from AGENT_REGISTRY."""
        # Use call_after_refresh to ensure we run in the correct Textual context
        self.call_after_refresh(self._handle_agent_registered, agent_id, agent_instance)

    def _handle_agent_registered(self, agent_id: str, agent_instance) -> None:
        """Handle agent registration in the correct Textual context."""
        # Log the event
        if self.repl_panel:
            self.repl_panel.add_system_message(f"Agent registered in global registry: {agent_id}", "green")

        # Queue the update if UI isn't ready yet
        if not self.agents_list:
            self._pending_agent_updates.append(("registered", agent_id))
        else:
            # Update the agents list if it exists
            self.agents_list.refresh_agents()

    def _on_agent_unregistered(self, agent_id: str, agent_instance) -> None:
        """Handle agent unregistration events from AGENT_REGISTRY."""
        # Use call_after_refresh to ensure we run in the correct Textual context
        self.call_after_refresh(self._handle_agent_unregistered, agent_id, agent_instance)

    def _handle_agent_unregistered(self, agent_id: str, agent_instance) -> None:
        """Handle agent unregistration in the correct Textual context."""
        # Log the event
        if self.repl_panel:
            self.repl_panel.add_system_message(f"Agent unregistered from global registry: {agent_id}", "yellow")

        # Queue the update if UI isn't ready yet
        if not self.agents_list:
            self._pending_agent_updates.append(("unregistered", agent_id))
        else:
            # Update the agents list if it exists
            self.agents_list.refresh_agents()

    def sync_with_global_registry(self) -> None:
        """Refresh the TUI to reflect the current state of AGENT_REGISTRY."""
        # Get all agents from the global registry
        global_agents = AGENT_REGISTRY.list_instances()

        # Log the sync operation
        if self.repl_panel:
            self.repl_panel.add_system_message(f"Refreshing from global registry: {len(global_agents)} agents found", "blue")

        # Update the agents list to reflect global state
        if self.agents_list:
            self.agents_list.refresh_agents()

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        with Vertical(classes="main-container"):
            with Horizontal(classes="content-area"):
                # Left panel: Unified REPL (input/output + execution)
                with Vertical(classes="left-panel"):
                    self.repl_panel = TerminalREPL(self.sandbox)
                    yield self.repl_panel

                # Right panel: Agents list + Agent detail
                with Vertical(classes="right-panel"):
                    # Top: Agents list
                    with Vertical(classes="agents-section"):
                        self.agents_list = AgentsList()
                        yield self.agents_list

                    # Bottom: Agent detail
                    with Vertical(classes="detail-section"):
                        self.agent_detail = AgentDetail(self.sandbox)
                        yield self.agent_detail

            # Log panel (initially hidden)
            self.log_panel = LogPanel(id="log-panel")
            yield self.log_panel

        # Footer with key hints
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application when mounted."""
        # Set initial focus
        if self.repl_panel:
            self.repl_panel.focus_input()

        # Update all panels with initial state
        self._update_all_panels()

        # Process any pending agent updates that occurred before UI was ready
        self._process_pending_agent_updates()

    def _process_pending_agent_updates(self) -> None:
        """Process any pending agent updates that occurred before UI was ready."""
        if not self._pending_agent_updates:
            return

        # Process all pending updates
        for event_type, agent_id in self._pending_agent_updates:
            if self.repl_panel:
                if event_type == "registered":
                    self.repl_panel.add_system_message(f"Agent registered in global registry: {agent_id}", "green")
                else:
                    self.repl_panel.add_system_message(f"Agent unregistered from global registry: {agent_id}", "yellow")

        # Refresh the agents list to show all current agents
        if self.agents_list:
            self.agents_list.refresh_agents()

        # Clear the pending updates
        self._pending_agent_updates.clear()

    def _update_all_panels(self) -> None:
        """Update all panels with current state."""
        if self.repl_panel:
            self.repl_panel.set_focused_agent(self._focused_agent)

        if self.agents_list:
            self.agents_list.update_focus(self._focused_agent)

        if self.agent_detail:
            self.agent_detail.set_focused_agent(self._focused_agent)

    @on(AgentSelected)
    def handle_agent_selected(self, event: AgentSelected) -> None:
        """Handle agent highlighting (hover) from agents list."""
        # Agent is highlighted/hovered - could update preview or status
        # Currently no action needed, just visual feedback in the list
        pass

    @on(AgentFocused)
    def handle_agent_focused(self, event: AgentFocused) -> None:
        """Handle agent focus change (actual selection) from agents list."""
        # Agent is actually selected/clicked - change the focused agent
        self.focus_agent(event.agent_name)

    def focus_agent(self, agent_name: str) -> None:
        """Focus on a specific agent."""
        # Check if agent exists in global registry
        instances = AGENT_REGISTRY.list_instances()
        agent_exists = any(hasattr(instance, "name") and instance.name == agent_name for instance in instances)

        if agent_exists:
            self._focused_agent = agent_name
            self._update_all_panels()
            if self.repl_panel:
                self.repl_panel.focus_input()

    # Action handlers for keybindings
    def action_cancel_focused(self) -> None:
        """Cancel the focused agent's current task."""
        if self._focused_agent:
            cancelled = task_manager.cancel_agent_tasks(self._focused_agent)
            if cancelled > 0:
                if self.repl_panel:
                    self.repl_panel.add_system_message(f"Cancelled {cancelled} task(s) for {self._focused_agent}", "yellow")
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
        # Get agents directly from AGENT_REGISTRY
        instances = AGENT_REGISTRY.list_instances()
        agents = [instance.name for instance in instances if hasattr(instance, "name")]
        agents.sort()  # Sort for consistent ordering

        if not agents:
            return

        current = self._focused_agent
        if current and current in agents:
            current_idx = agents.index(current)
            next_idx = (current_idx + 1) % len(agents)
            self.focus_agent(agents[next_idx])
        elif agents:
            self.focus_agent(agents[0])

    def action_prev_agent(self) -> None:
        """Focus on the previous agent."""
        # Get agents directly from AGENT_REGISTRY
        instances = AGENT_REGISTRY.list_instances()
        agents = [instance.name for instance in instances if hasattr(instance, "name")]
        agents.sort()  # Sort for consistent ordering

        if not agents:
            return

        current = self._focused_agent
        if current and current in agents:
            current_idx = agents.index(current)
            prev_idx = (current_idx - 1) % len(agents)
            self.focus_agent(agents[prev_idx])
        elif agents:
            self.focus_agent(agents[-1])

    def action_help(self) -> None:
        """Show help information."""
        if self.repl_panel:
            help_text = """
Dana TUI Help
=============

Key Bindings:
- Ctrl+Q: Quit
- Ctrl+L: Toggle log panel
- F1: Show this help
- Tab/Shift+Tab: Navigate between agents
- Ctrl+X: Clear transcript
- Ctrl+H: Show history
- Ctrl+Shift+H: Clear history
- Ctrl+S: Save logs
- Ctrl+R: Sync with global registry

Copy/Paste:
Input Area:
- Ctrl+Shift+C: Copy selected text
- Ctrl+Shift+V: Paste text
- Ctrl+Shift+X: Cut selected text

Output Areas (Terminal, Logs, Agent Detail):
- Ctrl+Shift+C: Copy all content
- Ctrl+Shift+A: Select all and copy

Registry Integration:
- The TUI automatically monitors AGENT_REGISTRY events
- Agent registration/unregistration events are logged
- Press Ctrl+R to manually refresh from the global registry
- The agents list updates automatically when registry changes
- The TUI displays agents from the global AGENT_REGISTRY only
            """
            self.repl_panel.add_meta_command_result(help_text)

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

    def action_toggle_logs(self) -> None:
        """Toggle the log panel visibility."""
        if self.log_panel:
            if self.log_panel.is_visible():
                self.log_panel.hide()
                if self.repl_panel:
                    self.repl_panel.add_system_message("Log panel hidden. Press Ctrl+L to show.", "dim")
            else:
                self.log_panel.show()
                if self.repl_panel:
                    self.repl_panel.add_system_message("Log panel visible. Press Ctrl+L to hide.", "green")

    def action_sync_registry(self) -> None:
        """Manually sync with the global AGENT_REGISTRY."""
        self.sync_with_global_registry()


def main():
    """Main entry point for the Dana TUI."""
    import argparse

    parser = argparse.ArgumentParser(description="Dana TUI - Textual User Interface")
    parser.add_argument("--no-console-logging", action="store_true", help="Disable console logging (logs only appear in TUI log panel)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging based on arguments
    from dana.common.utils.logging import DANA_LOGGER

    if args.no_console_logging:
        DANA_LOGGER.disable_console_logging()
    if args.debug:
        DANA_LOGGER.configure(level=DANA_LOGGER.DEBUG, force=True)

    app = DanaTUI()
    app.run()
