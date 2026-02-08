"""Rich CLI Renderer - A Notifiable that displays agent activity with Rich.

Implements the Notifiable protocol to receive STAR loop broadcasts and
route them to phase-specific handlers for rich terminal display.

Supports graceful degradation for limited terminals:
- No color support: falls back to plain text output
- Narrow terminals (<80 cols): truncates content to fit
- Terminal resize: adapts without crashing

Usage with DanaCodingAgent (or any agent extending Notifier)::

    from dana.cli.rich_cli_renderer import RichCLIRenderer
    from dana.apps.dana.thought_logger import ThoughtLogger

    # Create renderer and attach to agent alongside ThoughtLogger
    renderer = RichCLIRenderer(verbose=True, show_tool_calls=True)
    logger = ThoughtLogger(verbose=True)
    agent.with_notifiable(renderer, logger)

    # Both receive broadcasts from the agent's STAR loop automatically.
    # No changes required to the agent code.
"""

import signal
import threading
from typing import Any

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from dana.cli.components.hint_bar import HintBarComponent
from dana.cli.components.progress_tracker import ProgressTrackerComponent
from dana.cli.components.result_panel import ResultPanelComponent
from dana.cli.components.spinner import SpinnerComponent
from dana.cli.components.status_line import StatusLineComponent
from dana.cli.components.stream_display import StreamDisplayComponent
from dana.cli.components.subagent_card import SubagentCardComponent
from dana.cli.components.tool_card import ToolCardComponent
from dana.cli.state import RenderState
from dana.common.protocols import DictParams, Notifiable


# Minimum terminal width for rich rendering
_MIN_RICH_WIDTH = 80


class RichCLIRenderer(Notifiable):
    """A Notifiable that renders agent activity using Rich terminal components.

    Routes broadcast messages from agents to phase-specific handlers based
    on the broadcast key present in the message. Uses rich.live.Live for
    flicker-free terminal updates.

    Graceful degradation:
    - If the terminal has no color support, falls back to plain text output.
    - If the terminal is narrower than 80 columns, tool card content is truncated.
    - Terminal resize events (SIGWINCH) are handled without crashing.
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
        self._progress_tracker = ProgressTrackerComponent()
        self._hint_bar = HintBarComponent()
        self._pending_tool_cards: list[dict[str, Any]] = []
        self._live: Live | None = None
        self._agent_stack: list[str] = []  # Track parent agent IDs for subagent transitions
        self._completed_subagents: list[SubagentCardComponent] = []  # Completed subagent cards for display
        self._caller_message_shown = False  # Only show ❯ once per user interaction
        self._seen_tool_calls = False  # Suppress streaming once tools are in play
        self._lock = threading.Lock()

        # Detect terminal capabilities
        self._has_color = self.console.color_system is not None
        self._install_resize_handler()

    def _install_resize_handler(self) -> None:
        """Install a SIGWINCH handler to handle terminal resize gracefully.

        Only installs on platforms that support SIGWINCH (Unix-like).
        Falls back silently on Windows or when signal registration fails.
        """
        if not hasattr(signal, "SIGWINCH"):
            return
        try:
            self._prev_sigwinch = signal.getsignal(signal.SIGWINCH)

            def _on_resize(signum: int, frame: Any) -> None:
                # Refresh display to adapt to new terminal size
                try:
                    self._refresh_display()
                except Exception:
                    pass  # Never crash on resize
                # Chain to previous handler if it was callable
                prev = self._prev_sigwinch
                if callable(prev) and prev is not signal.SIG_DFL and prev is not signal.SIG_IGN:
                    prev(signum, frame)

            signal.signal(signal.SIGWINCH, _on_resize)
        except (OSError, ValueError):
            # signal.signal() can fail if not called from main thread
            pass

    @property
    def has_color(self) -> bool:
        """Whether the terminal supports color output."""
        return self._has_color

    @property
    def terminal_width(self) -> int:
        """Current terminal width in columns."""
        return self.console.width

    @property
    def is_narrow(self) -> bool:
        """Whether the terminal is narrower than the minimum width (80 cols)."""
        return self.console.width < _MIN_RICH_WIDTH

    def _truncate_for_width(self, text: str, max_width: int | None = None) -> str:
        """Truncate text to fit within the terminal width.

        Args:
            text: The text to truncate.
            max_width: Override max width. Defaults to console width - 6
                       (accounting for panel borders and padding).

        Returns:
            Truncated text with ellipsis if needed.
        """
        if max_width is None:
            # Account for panel borders (2 chars each side) + padding (1 char each side)
            max_width = max(self.console.width - 6, 10)
        if len(text) <= max_width:
            return text
        return text[: max_width - 1] + "…"

    def _ensure_live(self) -> None:
        """Start the Live context if not already running.

        Skipped if terminal has no color support (plain text mode).
        """
        if not self._has_color:
            return
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

    def _is_in_subagent(self) -> bool:
        """Check if we're currently inside a subagent context."""
        return self.state.active_subagent is not None

    def _flush_tool_cards(self) -> None:
        """Print any pending tool cards to the console and clear the queue.

        Tool cards are printed outside the Live context so they persist
        in terminal history. Live is temporarily stopped to avoid
        interleaving with the live display.

        In no-color mode, prints plain text summaries instead of panels.
        In narrow terminals, truncates content to fit.

        Skipped when inside a subagent (cards go to the subagent container).
        """
        if not self._pending_tool_cards:
            return

        # Don't flush individual cards when inside a subagent
        if self._is_in_subagent():
            return

        # Stop Live temporarily so printed cards don't conflict
        was_live = self._live is not None
        if was_live:
            self._stop_live()

        pending = self._pending_tool_cards
        if not self._has_color:
            for tc in pending:
                func = tc.get("function", "unknown")
                args = tc.get("arguments", {})
                summary = f"-> {func}"
                if args:
                    params = ", ".join(f"{k}={v}" for k, v in args.items())
                    if self.is_narrow:
                        params = self._truncate_for_width(params)
                    summary += f": {params}"
                self.console.print(summary)
        elif len(pending) > 3:
            collapsed_count = len(pending) - 2
            self.console.print(Text(f"  +{collapsed_count} more tool uses", style="dim"))
            for tc in pending[-2:]:
                self.console.print(self._tool_card.render(tc))
        else:
            for tc in pending:
                self.console.print(self._tool_card.render(tc))

        self._pending_tool_cards.clear()

        # Restart Live if it was running
        if was_live:
            self._ensure_live()

    def _flush_completed_subagents(self) -> None:
        """Print completed subagent cards to the console permanently."""
        if not self._completed_subagents:
            return

        was_live = self._live is not None
        if was_live:
            self._stop_live()

        for card in self._completed_subagents:
            if self._has_color:
                self.console.print(card.render())
            else:
                self.console.print(card.render_plain())

        self._completed_subagents.clear()
        self.console.print()  # Visual separator after subagent cards

        if was_live:
            self._ensure_live()

    def _refresh_display(self) -> None:
        """Update the Live display with current state.

        Renders components in order: spinner, active subagent card, streaming text,
        result panels (historical collapsed, then recent interactive), progress tracker,
        hint bar, and status line at the bottom.
        """
        if self._live is None:
            return

        renderables: list[RenderableType] = []

        if self._spinner.running:
            spinner_text = f"[bold cyan]✦[/bold cyan] {self._spinner.text}"
            elapsed = self._spinner.elapsed_text
            if elapsed and elapsed != "0s":
                tokens = self._spinner.estimated_tokens_text
                spinner_text += f" [dim]({elapsed} · ↓ {tokens})[/dim]"
            renderables.append(Text.from_markup(spinner_text))

        # Active subagent card (shown in live display while in progress)
        if self.state.active_subagent is not None:
            renderables.append(self.state.active_subagent.render())

        if self._stream_display.buffer:
            renderables.append(self._stream_display.render())

        # Historical results (always collapsed, dimmed)
        for panel in self.state.historical_results:
            renderables.append(panel.render(expanded=False))

        # Current turn results (interactive with keyboard navigation)
        for i, panel in enumerate(self.state.current_turn_results):
            is_selected = i == self.state.selected_index
            is_expanded = i in self.state.expanded_indices
            renderables.append(panel.render(expanded=is_expanded, selected=is_selected))

        # Progress tracker above status line
        progress_table = self._progress_tracker.render()
        if progress_table is not None:
            renderables.append(progress_table)

        # Status line at bottom
        status_text = self._status_line.render()
        if status_text:
            renderables.append(Text.from_markup(f"[dim]{status_text}[/dim]"))

        # Hint bar
        is_processing = self._spinner.running
        has_results = len(self.state.current_turn_results) > 0
        hint = self._hint_bar.render(has_results=has_results, is_processing=is_processing)
        if hint is not None:
            renderables.append(hint)

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
                # Returning to a parent agent - subagent completed
                # Complete the active subagent card
                if self.state.active_subagent is not None:
                    self.state.active_subagent.complete()
                    self._completed_subagents.append(self.state.active_subagent)
                    self.state.active_subagent = None

                # Pop stack back to the returning agent
                while self._agent_stack and self._agent_stack[-1] != new_agent_id:
                    self._agent_stack.pop()
                if self._agent_stack:
                    self._agent_stack.pop()
            else:
                # New subagent invoked - push current agent onto stack
                self._agent_stack.append(old_agent_id)

                # Create a SubagentCardComponent for this subagent
                agent_type = getattr(notifier, "agent_type", "Agent")
                # Try to extract purpose from agent description or ID
                purpose = new_agent_id
                self.state.active_subagent = SubagentCardComponent(
                    agent_type=str(agent_type),
                    purpose=purpose,
                )

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

        Thread-safe: acquires lock before mutating any shared state.

        Args:
            notifier: The agent sending the notification.
            message: The notification message containing trace data.
        """
        with self._lock:
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
        Transitions current_turn_results to historical_results.
        """
        self.state.current_phase = "SEE"

        # Flush completed subagents before transitioning results
        self._flush_completed_subagents()

        # Transition current turn results to historical
        if self.state.current_turn_results:
            for panel in self.state.current_turn_results:
                panel.is_recent = False
            self.state.historical_results.extend(self.state.current_turn_results)
            self.state.current_turn_results = []
            self.state.selected_index = -1
            self.state.expanded_indices.clear()

        # Display user message with highlighted prefix (only once per interaction)
        caller_message = data.get("caller_message", "")
        if caller_message:
            self._spinner.increment_chars(len(str(caller_message)))
        if caller_message and self.verbose and not self._caller_message_shown:
            self._caller_message_shown = True
            was_live = self._live is not None
            if was_live:
                self._stop_live()
            user_line = Text()
            user_line.append("❯ ", style="bold green")
            user_line.append(str(caller_message), style="bold on grey23")
            self.console.print(user_line)
            if was_live:
                self._ensure_live()

        # Clear stream display for new STAR loop
        self._stream_display.clear()

        self._ensure_live()
        if not self._spinner.running:
            self._spinner.start()

        perception = data.get("perception", "")
        context = {"perception": perception} if perception else None
        self._spinner.update_phase("SEE", context)

        if not self._has_color:
            self.console.print(f"[SEE] {self._spinner.text}")
        else:
            self._refresh_display()

    def _handle_think(self, notifier: object, data: DictParams) -> None:
        """Handle THINK phase (trace_thoughts) broadcasts.

        Updates spinner to THINK phase. Extracts tool_calls for intent display.
        Routes tool cards to subagent container when inside a subagent.
        Streams response text to StreamDisplayComponent. Stops spinner when done=True.
        """
        self.state.current_phase = "THINK"

        done = data.get("done", False)
        tool_calls = data.get("tool_calls", [])
        response = data.get("response", "")
        todo_list = data.get("todo_list")

        if response:
            self._spinner.increment_chars(len(str(response)))

        # Update progress tracker if todo_list is present
        if todo_list is not None and isinstance(todo_list, list):
            self._progress_tracker.update_todos(todo_list)
            self.state.todo_items = list(todo_list)

        # Display reasoning text between tool call rounds
        reasoning = data.get("reasoning")
        if reasoning and self.show_reasoning and not done and tool_calls and not self._is_in_subagent():
            was_live = self._live is not None
            if was_live:
                self._stop_live()
            if self._has_color:
                self.console.print(Text(f"  {reasoning}", style="dim italic"))
            else:
                self.console.print(f"  {reasoning}")
            if was_live:
                self._ensure_live()

        # Track whether tools have been used in this interaction
        if tool_calls:
            self._seen_tool_calls = True

        if done:
            self._flush_completed_subagents()
            self._flush_tool_cards()

            # Capture metrics before stopping spinner
            tool_count = self._spinner.tool_count
            elapsed = self._spinner.elapsed_text
            tokens = self._spinner.estimated_tokens_text

            self._spinner.stop()
            self._stop_live()

            # Print completion summary when tools were used
            if tool_count > 0 and not self._agent_stack:
                summary = Text(f"  ✓ Done ({tool_count} tools · {elapsed} · {tokens})", style="dim")
                self.console.print(summary)

            # Print final response if available (skip for subagents —
            # the subagent card already summarizes their work)
            if response and self.verbose and not self._agent_stack:
                self.console.print()  # Visual separator
                if self._has_color:
                    self.console.print(Markdown(str(response)))
                else:
                    self.console.print(str(response))

            # Only reset interaction state when the top-level agent completes.
            # Subagent done=True should NOT reset these flags.
            if not self._agent_stack:
                self._caller_message_shown = False
                self._seen_tool_calls = False
            return

        # Only stream response text when NOT in a tool-use loop.
        # Once any tool_calls have been seen in this interaction, all
        # non-final response text is intermediate reasoning — suppress it.
        if response and not tool_calls and not self._seen_tool_calls:
            self._stream_display.append_chunk(str(response))

        self._ensure_live()
        if not self._spinner.running:
            self._spinner.start()

        # Route tool cards: to subagent container or to pending queue
        if tool_calls and isinstance(tool_calls, list) and self.show_tool_calls:
            for tc in tool_calls:
                if isinstance(tc, dict):
                    if self._is_in_subagent():
                        self.state.active_subagent.add_tool_call(tc)
                    else:
                        self._pending_tool_cards.append(tc)

        # Extract tool names from tool_calls for intent display
        if tool_calls and isinstance(tool_calls, list):
            tool_names = [tc.get("function", "unknown") for tc in tool_calls if isinstance(tc, dict)]
            self._spinner.update_phase("THINK", {"tool_calls": tool_names})
        else:
            self._spinner.update_phase("THINK")

        if not self._has_color:
            if self._is_in_subagent():
                # In no-color mode, show subagent summary instead of individual tool cards
                self.console.print(self.state.active_subagent.render_plain())
            else:
                self.console.print(f"[THINK] {self._spinner.text}")
        else:
            self._refresh_display()

    def _handle_act(self, notifier: object, data: DictParams) -> None:
        """Handle ACT phase (trace_outputs) broadcasts.

        Flushes pending tool cards then updates spinner to ACT phase.
        Creates ResultPanelComponent for each tool result.
        When inside a subagent, routes results to the subagent container instead.
        """
        self.state.current_phase = "ACT"

        # Flush tool cards before spinner so they appear first
        self._flush_tool_cards()

        # Track tool count in spinner for metrics
        tool_results = data.get("tool_results", [])
        if tool_results and isinstance(tool_results, list):
            for result in tool_results:
                if isinstance(result, dict):
                    self._spinner.increment_tool_count()
                    self.state.session_tool_count += 1

                    output = result.get("result", result.get("output", ""))
                    if output:
                        self._spinner.increment_chars(len(str(output)))

                    if self._is_in_subagent():
                        # Route to subagent container
                        self.state.active_subagent.add_tool_result(result)
                    else:
                        # Create result panels (existing behavior)
                        tool_name = result.get("target", result.get("function", result.get("tool", "unknown")))
                        success = result.get("success", True)
                        exit_code = result.get("exit_code", 0 if success else 1)
                        if not isinstance(exit_code, int):
                            exit_code = 0
                        panel = ResultPanelComponent(
                            tool_name=str(tool_name),
                            output=str(output),
                            exit_code=exit_code,
                            is_recent=True,
                        )
                        self.state.current_turn_results.append(panel)

        self._ensure_live()
        if not self._spinner.running:
            self._spinner.start()

        # Extract tool names from tool_calls in the output data
        tool_calls = data.get("tool_calls", [])
        tool_names: list[str] = []
        if tool_calls and isinstance(tool_calls, list):
            tool_names = [tc.get("function", "unknown") for tc in tool_calls if isinstance(tc, dict)]

        self._spinner.update_phase("ACT", {"tools": tool_names} if tool_names else None)

        if not self._has_color:
            if self._is_in_subagent():
                self.console.print(self.state.active_subagent.render_plain())
            else:
                self.console.print(f"[ACT] {self._spinner.text}")
        else:
            self._refresh_display()

    def select_up(self) -> None:
        """Move selection up among current turn results.

        Thread-safe: acquires lock before mutating state.
        Wraps around to the last result if at the top.
        Only operates on current_turn_results (recent/interactive).
        """
        with self._lock:
            count = len(self.state.current_turn_results)
            if count == 0:
                return

            if self.state.selected_index <= 0:
                self.state.selected_index = count - 1
            else:
                self.state.selected_index -= 1

    def select_down(self) -> None:
        """Move selection down among current turn results.

        Thread-safe: acquires lock before mutating state.
        Wraps around to the first result if at the bottom.
        Only operates on current_turn_results (recent/interactive).
        """
        with self._lock:
            count = len(self.state.current_turn_results)
            if count == 0:
                return

            if self.state.selected_index >= count - 1:
                self.state.selected_index = 0
            else:
                self.state.selected_index += 1

    def toggle_expand(self) -> None:
        """Toggle expand/collapse for the currently selected result.

        Thread-safe: acquires lock before mutating state.
        Only operates on current_turn_results (recent/interactive).
        No-op if no result is selected or index is out of range.
        """
        with self._lock:
            idx = self.state.selected_index
            if idx < 0 or idx >= len(self.state.current_turn_results):
                return

            if idx in self.state.expanded_indices:
                self.state.expanded_indices.discard(idx)
            else:
                self.state.expanded_indices.add(idx)

    def _handle_reflect(self, notifier: object, data: DictParams) -> None:
        """Handle REFLECT phase (trace_learning) broadcasts."""

    def _handle_workflow(self, notifier: object, data: DictParams) -> None:
        """Handle workflow_progress broadcasts."""

    def _handle_skill(self, notifier: object, data: DictParams) -> None:
        """Handle skill_progress broadcasts."""
