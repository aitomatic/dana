"""
Simple terminal-like REPL panel for Dana TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Static

from dana.apps.tui.core.runtime import DanaSandbox
from dana.common import DANA_LOGGER
from dana.core.concurrency import is_promise
from dana.core.concurrency.base_promise import BasePromise

from .copyable_richlog import CopyableRichLog
from .prompt_textarea import PromptStyleTextArea
from .syntax_highlighter import dana_highlighter


class ExecuteCommand(Message):
    """Message to execute a command after display update."""

    def __init__(self, command: str) -> None:
        super().__init__()
        self.command = command


class TerminalREPL(Vertical):
    """Simple Dana REPL with proper input/output separation."""

    def __init__(self, sandbox: DanaSandbox, **kwargs):
        super().__init__(**kwargs)
        self.sandbox = sandbox
        self._output: CopyableRichLog | None = None
        self._input: PromptStyleTextArea | None = None
        self._prompt: Static | None = None

    def compose(self) -> ComposeResult:
        """Create the terminal REPL UI."""
        # Header
        yield Static("💻 Aitomatic Dana TUI", classes="panel-title", id="terminal-title")

        # Output area (history of commands and results) - with copy functionality
        self._output = CopyableRichLog(highlight=True, markup=True, wrap=True, id="terminal-output")
        yield self._output

        # Input container with prompt symbol
        with Horizontal(id="terminal-input-container"):
            # Prompt symbol (static)
            self._prompt = Static("⏵", id="terminal-prompt")
            yield self._prompt

            # Enhanced prompt-style input for Dana expressions
            self._input = PromptStyleTextArea(sandbox=self.sandbox.get_dana_sandbox(), id="terminal-input")
            yield self._input

    def on_mount(self) -> None:
        """Initialize the terminal when mounted."""
        # Add welcome message
        if self._output:
            self._output.write("Welcome to the Dana TUI!")
            self._output.write("Enter Dana expressions and press Enter to execute.")
            self._output.write("Multi-line input:")
            self._output.write("  • Lines ending with ':' automatically enter multi-line mode")
            self._output.write("  • Use \\ to add a new line and enter/stay in multi-line mode")
            self._output.write("  • An empty line executes the multi-line code")
            self._output.write("Navigation:")
            self._output.write("  • Use ↑↓ arrows to navigate command history")
            self._output.write("  • History persists between sessions")
            self._output.write("")  # Empty line

        # Focus the input
        if self._input:
            self._input.focus()

    def on_prompt_style_text_area_text_changed(self, event: PromptStyleTextArea.TextChanged) -> None:
        """Handle when input text changes - apply live Dana syntax highlighting."""
        if not self._input:
            return

        # TextArea uses its built-in syntax highlighting based on the language setting
        # Since we set language="python" in PromptStyleInput, Python syntax highlighting
        # is automatically applied as the user types. Dana syntax is similar enough
        # to Python that most keywords, strings, and numbers will be highlighted correctly.
        #
        # We also have a DanaSyntaxHighlighter class for output display and future enhancements.
        # The input area uses Python highlighting for real-time feedback, while the output
        # uses our custom DanaSyntaxHighlighter for accurate Dana syntax highlighting.
        pass

    def on_prompt_style_text_area_submitted(self, event: PromptStyleTextArea.Submitted) -> None:
        """Handle when user submits input from PromptStyleInput."""
        command = event.value.strip()

        DANA_LOGGER.debug(f"Input submitted: {command}")

        if not command:
            return

        # Show the command in output (like a real REPL) with syntax highlighting
        if self._output:
            # Format multi-line commands nicely
            if "\n" in command:
                lines = command.split("\n")
                highlighted_first = dana_highlighter.highlight_code(lines[0])
                self._output.write(f"[bold]⏵[/bold] {highlighted_first}")
                for line in lines[1:]:
                    highlighted_line = dana_highlighter.highlight_code(line)
                    self._output.write(f"[bold]...[/bold] {highlighted_line}")
            else:
                highlighted_command = dana_highlighter.highlight_code(command)
                self._output.write(f"[bold]⏵[/bold] {highlighted_command}")

            # Force refresh the display to show command immediately
            self._output.refresh()
            self.app.refresh()

        # Execute our own async task
        import asyncio

        asyncio.create_task(self._execute_command_async(command))

        # Add command to history after submission (before execution)
        if self._input:
            self._input.add_to_history(command)

    async def _execute_command_async(self, command: str) -> None:
        """Execute Dana code asynchronously with input blocking."""
        # Disable input while executing to maintain REPL blocking behavior
        if self._input:
            self._input.disabled = True

        try:
            # Execute in a thread pool to avoid blocking the event loop
            import asyncio

            from dana.core.runtime import DanaThreadPool

            loop = asyncio.get_running_loop()
            executor = DanaThreadPool.get_instance().get_executor()

            # Run the synchronous execution in a thread pool
            result = await loop.run_in_executor(executor, self.sandbox.execute_string, command)

            # Display results
            if self._output:
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
                            # Direct result with syntax highlighting
                            result_str = str(result.result)
                            highlighted_result = self._highlight_result(result_str)
                            self._output.write(highlighted_result)
                else:
                    # Handle error
                    if result.error:
                        safe_error = dana_highlighter.escape_markup(str(result.error))
                        self._output.write(f"[red]Error: {safe_error}[/red]")
                    else:
                        self._output.write("[red]Unknown execution error[/red]")

        except Exception as e:
            if self._output:
                safe_error = dana_highlighter.escape_markup(str(e))
                self._output.write(f"[red]Execution error: {safe_error}[/red]")

        finally:
            # Re-enable input now that execution is complete
            if self._input:
                self._input.disabled = False
                self._input.focus()  # Return focus to input

    def on_execute_command(self, event: ExecuteCommand) -> None:
        """Handle command execution message."""
        self._execute_dana_code(event.command)

    def set_focused_agent(self, agent_name: str | None) -> None:
        """No-op for compatibility - agents not used in simple REPL."""
        pass

    def _execute_dana_code(self, code: str) -> None:
        """Execute Dana code directly using the sandbox."""
        assert self._output is not None

        try:
            # Execute the Dana code directly first (like regular REPL)
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
                        # Direct result with syntax highlighting
                        result_str = str(result.result)
                        highlighted_result = self._highlight_result(result_str)
                        self._output.write(highlighted_result)

            else:
                # Handle error
                if result.error:
                    safe_error = dana_highlighter.escape_markup(str(result.error))
                    self._output.write(f"[red]Error: {safe_error}[/red]")
                else:
                    self._output.write("[red]Unknown execution error[/red]")

        except Exception as e:
            safe_error = dana_highlighter.escape_markup(str(e))
            self._output.write(f"[red]Execution error: {safe_error}[/red]")

        # No need to add empty line - RichLog handles spacing

    def _highlight_result(self, result_str: str) -> str:
        """
        Apply appropriate highlighting to Dana result values.

        Args:
            result_str: String representation of the result

        Returns:
            Highlighted result string with Rich markup
        """
        return dana_highlighter.highlight_result(result_str)

    def _handle_promise_result(self, promise_result: BasePromise) -> None:
        """Handle Promise result by displaying safe Promise information."""
        assert self._output is not None

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
                        result_str = str(result)
                        highlighted_result = self._highlight_result(result_str)
                        self._output.write(f"[dim]Promise resolved:[/dim] {highlighted_result}")
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
        if self._input:
            history = self._input.get_history()
            if history:
                if self._output:
                    self._output.write("[dim]Command History:[/dim]")
                    for i, command in enumerate(history[-20:], 1):  # Show last 20 commands
                        # Format multi-line commands for display
                        display_command = command.replace("\\n", " ⏎ ") if "\\n" in command else command
                        self._output.write(f"[dim]{i:2d}[/dim] {display_command}")
                    self._output.write("")
            else:
                if self._output:
                    self._output.write("[dim]No command history.[/dim]")
        else:
            if self._output:
                self._output.write("[dim]History not available.[/dim]")

    def clear_command_history(self) -> None:
        """Clear the command history."""
        if self._input:
            self._input.clear_history()
            if self._output:
                self._output.write("[dim]Command history cleared.[/dim]")
        else:
            if self._output:
                self._output.write("[dim]History not available to clear.[/dim]")
