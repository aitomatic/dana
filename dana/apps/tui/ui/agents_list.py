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
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView, Static

from dana.core.builtin_types.agent_system import AgentInstance
from dana.registry import AGENT_REGISTRY


class AgentListItem(ListItem):
    """Individual agent item in the list."""

    def __init__(self, agent_name: str, agent: AgentInstance, is_focused: bool = False):
        super().__init__()
        self.agent_name = agent_name
        self.agent = agent
        self.is_focused = is_focused
        self._last_update = 0.0
        # Don't call update_content() here - compose() hasn't run yet

    def compose(self) -> ComposeResult:
        """Create the list item content."""
        # Create a valid CSS ID by replacing spaces and special characters
        safe_id = self.agent_name.replace(" ", "_").replace("-", "_")
        safe_id = "".join(c for c in safe_id if c.isalnum() or c == "_")
        label = Label(self._format_agent_display(), id=f"agent-{safe_id}")
        # Disable text wrapping to allow horizontal scrolling
        label.wrap = False
        # Ensure minimum width to force horizontal overflow
        label.styles.min_width = 80
        yield label

    def update_content(self) -> None:
        """Update the agent display content."""
        now = time.perf_counter()
        if now - self._last_update < 0.5:  # Limit updates to 2Hz
            return

        self._last_update = now

        # Update the label content (only if widget is mounted)
        try:
            # Create the same safe ID as in compose()
            safe_id = self.agent_name.replace(" ", "_").replace("-", "_")
            safe_id = "".join(c for c in safe_id if c.isalnum() or c == "_")
            label = self.query_one(f"#agent-{safe_id}", Label)
            label.update(self._format_agent_display())
        except Exception:
            # Widget not mounted yet, skip update
            pass

    def _format_agent_display(self) -> str:
        """Format the agent display string."""
        metrics = self.agent.get_metrics()

        # Status indicator
        status_char = "●" if metrics.get("is_running", False) else "○"
        focus_char = "→" if self.is_focused else " "

        # Step and elapsed time
        step = metrics.get("current_step", "idle")  # Don't truncate for horizontal scrolling
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

        # Format with natural width (no truncation for horizontal scrolling)
        name_part = f"{focus_char}{status_char} {self.agent_name}"
        step_part = f"step: {step}"
        rate_part = f"tok/s: {tok_str}"
        time_part = f"⏱ {elapsed_str}"

        return f"{name_part} │ {step_part} │ {rate_part} │ {time_part}"

    def set_focused(self, focused: bool) -> None:
        """Update focus state."""
        self.is_focused = focused
        self.update_content()


class AgentsList(Vertical):
    """Widget displaying the list of agents with their status."""

    # Reactive attributes
    focused_agent: reactive[str | None] = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._list_view: ListView | None = None
        self._last_update = 0.0
        self._update_timer = None

    def compose(self) -> ComposeResult:
        """Create the agents list UI."""
        yield Static("🤖 Agents", classes="panel-title")
        self._list_view = ListView(id="agents-list")
        # Enable horizontal scrolling for long agent names/metrics
        self._list_view.can_focus = True
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
        # Don't check boolean value of ListView - it may return False when not mounted
        if self._list_view is None:
            return

        # Get current agents from AGENT_REGISTRY
        instances = AGENT_REGISTRY.list_instances()
        current_agents = {}
        for instance in instances:
            if hasattr(instance, "name"):
                current_agents[instance.name] = instance

        # Clear and rebuild the list
        self._list_view.clear()

        for agent_name in sorted(current_agents.keys()):
            agent: AgentInstance = current_agents[agent_name]
            # Note: focus state is managed by the TUI app, not this component
            is_focused = False  # Will be updated by update_focus method
            item = AgentListItem(agent_name, agent, is_focused)
            self._list_view.append(item)

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

    def add_agent(self, agent_name: str, agent: AgentInstance) -> None:
        """Add a new agent to the list."""
        if not self._list_view:
            return

        # Check if agent already exists
        for item in self._list_view.children:
            if isinstance(item, AgentListItem) and item.agent_name == agent_name:
                return  # Already exists

        # Add new agent (focus state will be updated by update_focus method)
        item = AgentListItem(agent_name, agent, False)
        self._list_view.append(item)

    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the list."""
        if not self._list_view:
            return

        # Find and remove the agent item
        for item in list(self._list_view.children):
            if isinstance(item, AgentListItem) and item.agent_name == agent_name:
                item.remove()
                break

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
        """Handle agent highlighting (hovering) in the list."""
        if isinstance(event.item, AgentListItem):
            # Post message when agent is highlighted/hovered (visual feedback only)
            self.post_message(AgentSelected(event.item.agent_name))

    @on(ListView.Selected)
    def on_agent_selected(self, event: ListView.Selected) -> None:
        """Handle agent selection (Enter key or click)."""
        if isinstance(event.item, AgentListItem):
            # Post message when agent is actually selected/clicked (focus change)
            self.post_message(AgentFocused(event.item.agent_name))


# Custom messages for agent selection
class AgentSelected(Message):
    """Message posted when an agent is highlighted/hovered over (but not necessarily focused)."""

    def __init__(self, agent_name: str):
        super().__init__()
        self.agent_name = agent_name


class AgentFocused(Message):
    """Message posted when an agent is actually selected/clicked and should become the focused agent."""

    def __init__(self, agent_name: str):
        super().__init__()
        self.agent_name = agent_name
