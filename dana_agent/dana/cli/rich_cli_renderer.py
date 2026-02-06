"""Rich CLI Renderer - A Notifiable that displays agent activity with Rich.

Implements the Notifiable protocol to receive STAR loop broadcasts and
route them to phase-specific handlers for rich terminal display.

Usage:
    from dana.cli.rich_cli_renderer import RichCLIRenderer

    renderer = RichCLIRenderer(verbose=True, show_tool_calls=True)
    agent.with_notifiable(renderer)
"""

from rich.console import Console

from dana.cli.state import RenderState
from dana.common.protocols import DictParams, Notifiable


class RichCLIRenderer(Notifiable):
    """A Notifiable that renders agent activity using Rich terminal components.

    Routes broadcast messages from agents to phase-specific handlers based
    on the broadcast key present in the message.
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
        """Handle SEE phase (trace_percepts) broadcasts."""

    def _handle_think(self, notifier: object, data: DictParams) -> None:
        """Handle THINK phase (trace_thoughts) broadcasts."""

    def _handle_act(self, notifier: object, data: DictParams) -> None:
        """Handle ACT phase (trace_outputs) broadcasts."""

    def _handle_reflect(self, notifier: object, data: DictParams) -> None:
        """Handle REFLECT phase (trace_learning) broadcasts."""

    def _handle_workflow(self, notifier: object, data: DictParams) -> None:
        """Handle workflow_progress broadcasts."""

    def _handle_skill(self, notifier: object, data: DictParams) -> None:
        """Handle skill_progress broadcasts."""
