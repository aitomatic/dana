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
        self._pending_tool_cards: list[dict[str, Any]] = []
        self._live: Live | None = None

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

        Renders spinner and streaming text together. Streaming text
        appears below the spinner so both are visible simultaneously.
        """
        if self._live is None:
            return

        renderables: list[Text] = []

        if self._spinner.running:
            renderables.append(Text.from_markup(f"[bold cyan]⠋[/bold cyan] {self._spinner.text}"))

        if self._stream_display.buffer:
            renderables.append(self._stream_display.render())

        if renderables:
            self._live.update(Group(*renderables))
        else:
            self._live.update(Text(""))

    def notify(self, notifier: object, message: DictParams) -> None:
        """Receive a broadcast message and route to the appropriate handler.

        Args:
            notifier: The agent sending the notification.
            message: The notification message containing trace data.
        """
        # Update agent context from notifier
        self.state.current_agent_id = getattr(notifier, "object_id", "unknown")

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
