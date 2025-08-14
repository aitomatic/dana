"""
Simple terminal-like REPL panel for Dana TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, RichLog, Static

from dana.core.concurrency import is_promise
from dana.core.concurrency.base_promise import BasePromise

from ..core.completion import DanaInput
from ..core.runtime import DanaSandbox


class TerminalREPL(Vertical):
    """Simple Dana REPL with proper input/output separation."""

    def __init__(self, sandbox: DanaSandbox, **kwargs):
        super().__init__(**kwargs)
        self.sandbox = sandbox
        self._output: RichLog | None = None
        self._input: DanaInput | None = None

    def compose(self) -> ComposeResult:
        """Create the terminal REPL UI."""
        # Header
        yield Static("Dana REPL", classes="panel-title", id="terminal-title")

        # Output area (history of commands and results)
        self._output = RichLog(highlight=True, markup=True, wrap=True, id="terminal-output")
        yield self._output

        # Dana autocomplete input for expressions
        self._input = DanaInput(sandbox=self.sandbox, placeholder="Enter Dana expression...", id="terminal-input")
        yield self._input

    def on_mount(self) -> None:
        """Initialize the terminal when mounted."""
        # Add welcome message
        if self._output:
            self._output.write("Welcome to Dana REPL!")
            self._output.write("Enter Dana expressions and press Enter to execute.")
            self._output.write("")  # Empty line

        # Focus the input
        if self._input:
            self._input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle when user submits input (presses Enter)."""
        command = event.value.strip()

        if not command:
            return

        # Add command to history
        if self._input and hasattr(self._input, "add_to_history"):
            self._input.add_to_history(command)

        # Show the command in output (like a real REPL)
        if self._output:
            self._output.write(f"[bold]>>> {command}[/bold]")

        # Execute the command
        self._execute_dana_code(command)

        # Clear the input for next command
        if self._input:
            if hasattr(self._input, "value"):
                self._input.value = ""
            elif hasattr(self._input, "clear"):
                self._input.clear()

    def set_focused_agent(self, agent_name: str | None) -> None:
        """No-op for compatibility - agents not used in simple REPL."""
        pass

    def _execute_dana_code(self, code: str) -> None:
        """Execute Dana code directly using the sandbox."""
        try:
            # Execute the Dana code
            result = self.sandbox.execute_string(code)

            if result.success:
                # Handle output
                if result.output:
                    self._output.write(result.output.rstrip())

                # Handle result
                if result.result is not None:
                    # Check if result is a Promise
                    if is_promise(result.result):
                        self._handle_promise_result(result.result)
                    else:
                        # Direct result
                        self._output.write(str(result.result))

            else:
                # Handle error
                if result.error:
                    self._output.write(f"[red]Error: {result.error}[/red]")
                else:
                    self._output.write("[red]Unknown execution error[/red]")

        except Exception as e:
            self._output.write(f"[red]Execution error: {str(e)}[/red]")

        # No need to add empty line - RichLog handles spacing

    def _handle_promise_result(self, promise_result: BasePromise) -> None:
        """Handle Promise result by displaying safe Promise information."""
        try:
            if hasattr(promise_result, "get_display_info"):
                promise_info = promise_result.get_display_info()
            else:
                promise_info = f"<{type(promise_result).__name__}>"
        except Exception:
            promise_info = "<Promise (info unavailable)>"

        # Display promise info
        self._output.write(promise_info)

        # Add callback to print the result when promise is delivered
        if hasattr(promise_result, "add_on_delivery_callback"):

            def on_promise_delivered(result):
                """Callback to print the delivered promise result."""
                try:
                    if self._output:
                        self._output.write(f"Promise resolved: {result}")
                except Exception:
                    pass  # Safe fallback

            promise_result.add_on_delivery_callback(on_promise_delivered)

    def clear_terminal(self) -> None:
        """Clear the terminal output."""
        if self._output:
            self._output.clear()
            self._output.write("[dim]Terminal cleared.[/dim]")
            self._output.write("")

    def clear_transcript(self) -> None:
        """Clear the terminal transcript."""
        self.clear_terminal()

    def cancel_current_task(self) -> bool:
        """Cancel the current running task."""
        # No tasks to cancel in simple Dana REPL
        return False

    def focus_input(self) -> None:
        """Focus the input area."""
        if self._input:
            self._input.focus()

    def add_system_message(self, message: str, style: str = "dim") -> None:
        """Add a system message to the output."""
        if self._output:
            if style == "dim":
                self._output.write(f"[dim]{message}[/dim]")
            elif style == "yellow":
                self._output.write(f"[yellow]{message}[/yellow]")
            elif style == "red":
                self._output.write(f"[red]{message}[/red]")
            elif style == "green":
                self._output.write(f"[green]{message}[/green]")
            else:
                self._output.write(message)

    def add_meta_command_result(self, result: str) -> None:
        """Add a meta command result to the output."""
        if self._output:
            self._output.write(result)

    def show_history(self) -> None:
        """Display the command history."""
        if self._input and hasattr(self._input, "get_history"):
            history = self._input.get_history()
            if history:
                if self._output:
                    self._output.write("[dim]Command History:[/dim]")
                    for i, command in enumerate(history[-20:], 1):  # Show last 20 commands
                        self._output.write(f"[dim]{i:2d}[/dim] {command}")
                    self._output.write("")
            else:
                if self._output:
                    self._output.write("[dim]No command history.[/dim]")
        else:
            if self._output:
                self._output.write("[dim]History not available.[/dim]")

    def clear_command_history(self) -> None:
        """Clear the command history."""
        if self._input and hasattr(self._input, "clear_history"):
            self._input.clear_history()
            if self._output:
                self._output.write("[dim]Command history cleared.[/dim]")
        else:
            if self._output:
                self._output.write("[dim]History not available to clear.[/dim]")
