"""Rich CLI Renderer - A Notifiable that displays agent activity with Rich.

Implements the Notifiable protocol to receive STAR loop broadcasts and
route them to phase-specific handlers for rich terminal display.

Usage:
    from dana.cli.rich_cli_renderer import RichCLIRenderer

    renderer = RichCLIRenderer(verbose=True, show_tool_calls=True)
    agent.with_notifiable(renderer)
"""

from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.text import Text

from dana.cli.components.spinner import SpinnerComponent
from dana.cli.components.status_line import StatusLineComponent
from dana.cli.components.stream_display import StreamDisplayComponent
from dana.cli.components.tool_card import ToolCardComponent
from dana.cli.state import RenderState
from dana.common.protocols import DictParams, Notifiable


class RichCLIRenderer(Notifiable):
    """A Notifiable that renders agent activity using Rich terminal components.

    Routes broadcast messages from agents to phase-specific handlers based
    on the broadcast key present in the message. Uses rich.live.Live for
    flicker-free terminal updates.
    """

    def __init__(
        self,
        console: Console | None = None,
        verbose: bool = True,
        show_tool_calls: bool = True,
        show_reasoning: bool = True,
        max_output_lines: int = 50,
    ) -> None:
        self.console = console or Console()
        self.verbose = verbose
        self.show_tool_calls = show_tool_calls
        self.show_reasoning = show_reasoning
        self.max_output_lines = max_output_lines
        self.state = RenderState()
        self._spinner = SpinnerComponent()
        self._stream_display = StreamDisplayComponent(max_visible_lines=20, line_threshold=max_output_lines)
        self._tool_card = ToolCardComponent()
        self._status_line = StatusLineComponent()
        self._pending_tool_cards: list[dict[str, Any]] = []
        self._live: Live | None = None
        self._agent_stack: list[str] = []  # Track parent agent IDs for subagent transitions

    def _ensure_live(self) -> None:
        """Start the Live context if not already running."""
        if self._live is None:
            self._live = Live(
                console=self.console,
                refresh_per_second=10,
                transient=True,
            )
            self._live.start()

    def _stop_live(self) -> None:
        """Stop the Live context if running."""
        if self._live is not None:
            self._live.stop()
            self._live = None

    def _flush_tool_cards(self) -> None:
        """Print any pending tool cards to the console and clear the queue.

        Tool cards are printed outside the Live context so they persist
        in terminal history. Live is temporarily stopped to avoid
        interleaving with the live display.
        """
        if not self._pending_tool_cards:
            return

        # Stop Live temporarily so printed cards don't conflict
        was_live = self._live is not None
        if was_live:
            self._stop_live()

        for tc in self._pending_tool_cards:
            panel = self._tool_card.render(tc)
            self.console.print(panel)

        self._pending_tool_cards.clear()

        # Restart Live if it was running
        if was_live:
            self._ensure_live()

    def _refresh_display(self) -> None:
        """Update the Live display with current state.

        Renders spinner, streaming text, and status line together.
        Status line is displayed at the bottom of the terminal output.
        """
        if self._live is None:
            return

        renderables: list[Text] = []

        if self._spinner.running:
            renderables.append(Text.from_markup(f"[bold cyan]⠋[/bold cyan] {self._spinner.text}"))

        if self._stream_display.buffer:
            renderables.append(self._stream_display.render())

        # Status line at bottom
        status_text = self._status_line.render()
        if status_text:
            renderables.append(Text.from_markup(f"[dim]{status_text}[/dim]"))

        if renderables:
            self._live.update(Group(*renderables))
        else:
            self._live.update(Text(""))

    def _update_agent_context(self, notifier: object) -> None:
        """Extract agent context from notifier and update state + status line.

        Detects subagent transitions by tracking agent_id changes.
        When a new agent_id appears, the previous one is pushed onto the stack.
        When a previous agent_id reappears, we pop back to it (subagent completed).
        """
        new_agent_id = getattr(notifier, "object_id", "unknown")
        old_agent_id = self.state.current_agent_id

        # Detect agent transitions
        if old_agent_id and new_agent_id != old_agent_id:
            if new_agent_id in self._agent_stack:
                # Returning to a parent agent - pop stack back to it
                while self._agent_stack and self._agent_stack[-1] != new_agent_id:
                    self._agent_stack.pop()
                if self._agent_stack:
                    self._agent_stack.pop()
            else:
                # New subagent invoked - push current agent onto stack
                self._agent_stack.append(old_agent_id)

        self.state.current_agent_id = new_agent_id

        # Extract model from notifier (try llm_client.model, then _llm_config)
        llm_client = getattr(notifier, "llm_client", None)
        if llm_client:
            self.state.current_model = getattr(llm_client, "model", "")
        else:
            llm_config = getattr(notifier, "_llm_config", {})
            if isinstance(llm_config, dict):
                self.state.current_model = llm_config.get("model", "")

        # Extract turn info from notifier
        star_loop_count = getattr(notifier, "_star_loop_count", 0)
        if isinstance(star_loop_count, int):
            self.state.current_turn = star_loop_count

        max_turns = getattr(notifier, "max_turns", 0)
        if isinstance(max_turns, int):
            self.state.max_turns = max_turns

        # Update status line from state
        self._status_line.update(
            agent_id=self.state.current_agent_id,
            model=self.state.current_model,
            turn=self.state.current_turn,
            max_turns=self.state.max_turns,
        )

    def notify(self, notifier: object, message: DictParams) -> None:
        """Receive a broadcast message and route to the appropriate handler.

        Args:
            notifier: The agent sending the notification.
            message: The notification message containing trace data.
        """
        # Update agent context and status line from notifier
        self._update_agent_context(notifier)

        if message.get("trace_percepts"):
            self._handle_see(notifier, message["trace_percepts"])
        if message.get("trace_thoughts"):
            self._handle_think(notifier, message["trace_thoughts"])
        if message.get("trace_outputs"):
            self._handle_act(notifier, message["trace_outputs"])
        if message.get("trace_learning"):
            self._handle_reflect(notifier, message["trace_learning"])
        if message.get("workflow_progress"):
            self._handle_workflow(notifier, message["workflow_progress"])
        if message.get("skill_progress"):
            self._handle_skill(notifier, message["skill_progress"])

    def _handle_see(self, notifier: object, data: DictParams) -> None:
        """Handle SEE phase (trace_percepts) broadcasts.

        Updates spinner to SEE phase with perception count info.
        Clears the stream display for the new STAR loop.
        """
        self.state.current_phase = "SEE"

        # Clear stream display for new STAR loop (new user message)
        self._stream_display.clear()

        self._ensure_live()
        if not self._spinner.running:
            self._spinner.start()

        perception = data.get("perception", "")
        context = {"perception": perception} if perception else None
        self._spinner.update_phase("SEE", context)
        self._refresh_display()

    def _handle_think(self, notifier: object, data: DictParams) -> None:
        """Handle THINK phase (trace_thoughts) broadcasts.

        Updates spinner to THINK phase. Extracts tool_calls for intent display.
        Renders tool cards for each tool call. Streams response text to
        StreamDisplayComponent. Stops spinner when done=True.
        """
        self.state.current_phase = "THINK"

        done = data.get("done", False)
        tool_calls = data.get("tool_calls", [])
        response = data.get("response", "")

        if done:
            self._flush_tool_cards()
            self._spinner.stop()
            self._stop_live()

            # Print final response if available
            if response and self.verbose:
                self.console.print(Text(str(response)))
            return

        # Stream response text if available
        if response:
            self._stream_display.append_chunk(str(response))

        self._ensure_live()
        if not self._spinner.running:
            self._spinner.start()

        # Render tool cards for each tool call
        if tool_calls and isinstance(tool_calls, list) and self.show_tool_calls:
            for tc in tool_calls:
                if isinstance(tc, dict):
                    self._pending_tool_cards.append(tc)

        # Extract tool names from tool_calls for intent display
        if tool_calls and isinstance(tool_calls, list):
            tool_names = [tc.get("function", "unknown") for tc in tool_calls if isinstance(tc, dict)]
            self._spinner.update_phase("THINK", {"tool_calls": tool_names})
        else:
            self._spinner.update_phase("THINK")

        self._refresh_display()

    def _handle_act(self, notifier: object, data: DictParams) -> None:
        """Handle ACT phase (trace_outputs) broadcasts.

        Flushes pending tool cards then updates spinner to ACT phase.
        Cards render before spinner during ACT phase.
        """
        self.state.current_phase = "ACT"

        # Flush tool cards before spinner so they appear first
        self._flush_tool_cards()

        self._ensure_live()
        if not self._spinner.running:
            self._spinner.start()

        # Extract tool names from tool_calls in the output data
        tool_calls = data.get("tool_calls", [])
        tool_names: list[str] = []
        if tool_calls and isinstance(tool_calls, list):
            tool_names = [tc.get("function", "unknown") for tc in tool_calls if isinstance(tc, dict)]

        self._spinner.update_phase("ACT", {"tools": tool_names} if tool_names else None)
        self._refresh_display()

    def _handle_reflect(self, notifier: object, data: DictParams) -> None:
        """Handle REFLECT phase (trace_learning) broadcasts."""

    def _handle_workflow(self, notifier: object, data: DictParams) -> None:
        """Handle workflow_progress broadcasts."""

    def _handle_skill(self, notifier: object, data: DictParams) -> None:
        """Handle skill_progress broadcasts."""
