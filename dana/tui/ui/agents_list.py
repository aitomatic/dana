"""
Agents list widget for Dana TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import time

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView, Static

from ..core.runtime import Agent, DanaSandbox


class AgentListItem(ListItem):
    """Individual agent item in the list."""

    def __init__(self, agent_name: str, agent: Agent, is_focused: bool = False):
        super().__init__()
        self.agent_name = agent_name
        self.agent = agent
        self.is_focused = is_focused
        self._last_update = 0.0
        self.update_content()

    def compose(self) -> ComposeResult:
        """Create the list item content."""
        yield Label(self._format_agent_display(), id=f"agent-{self.agent_name}")

    def update_content(self) -> None:
        """Update the agent display content."""
        now = time.perf_counter()
        if now - self._last_update < 0.5:  # Limit updates to 2Hz
            return

        self._last_update = now

        # Update the label content
        label = self.query_one(f"#agent-{self.agent_name}", Label)
        label.update(self._format_agent_display())

    def _format_agent_display(self) -> str:
        """Format the agent display string."""
        metrics = self.agent.get_metrics()

        # Status indicator
        status_char = "●" if metrics.get("is_running", False) else "○"
        focus_char = "→" if self.is_focused else " "

        # Step and elapsed time
        step = metrics.get("current_step", "idle")[:8]  # Truncate long steps
        elapsed = metrics.get("elapsed_time", 0.0)

        # Token rate
        tok_rate = metrics.get("tokens_per_sec", 0.0)

        # Format the line with fixed width components
        if elapsed > 0:
            elapsed_str = f"{elapsed:05.1f}s"
        else:
            elapsed_str = "   -  "

        if tok_rate > 0:
            tok_str = f"{tok_rate:4.1f}"
        else:
            tok_str = " - "

        # Ensure consistent spacing
        name_part = f"{focus_char}{status_char} {self.agent_name:<12}"
        step_part = f"step: {step:<8}"
        rate_part = f"tok/s: {tok_str:<4}"
        time_part = f"⏱ {elapsed_str}"

        return f"{name_part} {step_part} {rate_part} {time_part}"

    def set_focused(self, focused: bool) -> None:
        """Update focus state."""
        self.is_focused = focused
        self.update_content()


class AgentsList(Vertical):
    """Widget displaying the list of agents with their status."""

    # Reactive attributes
    focused_agent: reactive[str | None] = reactive(None)
    agents: reactive[dict[str, Agent]] = reactive({})

    def __init__(self, sandbox: DanaSandbox, **kwargs):
        super().__init__(**kwargs)
        self.sandbox = sandbox
        self._list_view: ListView | None = None
        self._last_update = 0.0
        self._update_timer = None

    def compose(self) -> ComposeResult:
        """Create the agents list UI."""
        yield Static("Agents", classes="panel-title")
        self._list_view = ListView(id="agents-list")
        yield self._list_view

    def on_mount(self) -> None:
        """Initialize the agents list when mounted."""
        self.refresh_agents()
        self.start_update_timer()

    def on_unmount(self) -> None:
        """Clean up when unmounted."""
        if self._update_timer:
            self._update_timer.cancel()

    def start_update_timer(self) -> None:
        """Start the periodic update timer."""

        async def update_loop():
            while True:
                await self.app.sleep(0.5)  # Update at 2Hz
                self.refresh_metrics()

        if self._update_timer:
            self._update_timer.cancel()
        self._update_timer = asyncio.create_task(update_loop())

    def refresh_agents(self) -> None:
        """Refresh the entire agents list."""
        if not self._list_view:
            return

        # Get current agents from sandbox
        current_agents = self.sandbox.get_all_agents()
        focused_agent_name = self.sandbox.get_focused_name()

        # Clear and rebuild the list
        self._list_view.clear()

        for agent_name in sorted(current_agents.keys()):
            agent = current_agents[agent_name]
            is_focused = agent_name == focused_agent_name
            item = AgentListItem(agent_name, agent, is_focused)
            self._list_view.append(item)

        # Update reactive state
        self.agents = current_agents
        self.focused_agent = focused_agent_name

    def refresh_metrics(self) -> None:
        """Refresh just the metrics without rebuilding the list."""
        now = time.perf_counter()
        if now - self._last_update < 0.5:  # Limit to 2Hz
            return

        self._last_update = now

        if not self._list_view:
            return

        # Update each agent item's metrics
        for item in self._list_view.children:
            if isinstance(item, AgentListItem):
                item.update_content()

    def add_agent(self, agent_name: str, agent: Agent) -> None:
        """Add a new agent to the list."""
        if not self._list_view:
            return

        # Check if agent already exists
        for item in self._list_view.children:
            if isinstance(item, AgentListItem) and item.agent_name == agent_name:
                return  # Already exists

        # Add new agent
        is_focused = agent_name == self.sandbox.get_focused_name()
        item = AgentListItem(agent_name, agent, is_focused)
        self._list_view.append(item)

        # Update reactive state
        self.agents = self.sandbox.get_all_agents()

    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the list."""
        if not self._list_view:
            return

        # Find and remove the agent item
        for item in list(self._list_view.children):
            if isinstance(item, AgentListItem) and item.agent_name == agent_name:
                item.remove()
                break

        # Update reactive state
        self.agents = self.sandbox.get_all_agents()

    def update_focus(self, new_focused_agent: str | None) -> None:
        """Update which agent is focused."""
        if not self._list_view:
            return

        # Update all items' focus state
        for item in self._list_view.children:
            if isinstance(item, AgentListItem):
                is_focused = item.agent_name == new_focused_agent
                item.set_focused(is_focused)

        self.focused_agent = new_focused_agent

    def get_selected_agent(self) -> str | None:
        """Get the currently selected agent name."""
        if not self._list_view or not self._list_view.highlighted_child:
            return None

        highlighted = self._list_view.highlighted_child
        if isinstance(highlighted, AgentListItem):
            return highlighted.agent_name

        return None

    def select_agent(self, agent_name: str) -> bool:
        """Select a specific agent in the list."""
        if not self._list_view:
            return False

        for i, item in enumerate(self._list_view.children):
            if isinstance(item, AgentListItem) and item.agent_name == agent_name:
                self._list_view.index = i
                return True

        return False

    @on(ListView.Highlighted)
    def on_agent_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle agent selection in the list."""
        if isinstance(event.item, AgentListItem):
            # Post a custom message for the main app to handle
            self.post_message(AgentSelected(event.item.agent_name))

    @on(ListView.Selected)
    def on_agent_selected(self, event: ListView.Selected) -> None:
        """Handle agent selection (Enter key)."""
        if isinstance(event.item, AgentListItem):
            # Focus the selected agent
            self.post_message(AgentFocused(event.item.agent_name))


# Custom messages for agent selection
class AgentSelected:
    """Message posted when an agent is highlighted."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name


class AgentFocused:
    """Message posted when an agent should be focused."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
