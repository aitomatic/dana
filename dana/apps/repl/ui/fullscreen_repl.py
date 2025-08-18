"""
Full-screen Dana REPL with persistent status bar.

This module provides a full-screen REPL interface using prompt_toolkit's
Application framework with a fixed status area at the bottom.
"""

import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.styles import Style

from dana.apps.repl.repl import REPL
from dana.apps.repl.ui.prompt_session import DanaCompleter
from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme, get_dana_lexer


class FullScreenREPL(Loggable):
    """Full-screen Dana REPL with persistent bottom status bar."""

    def __init__(self, repl: REPL, colors: ColorScheme):
        """Initialize the full-screen REPL."""
        super().__init__()
        self.repl = repl
        self.colors = colors
        self.dana_lexer = get_dana_lexer()

        # Create the main input buffer
        self.input_buffer = Buffer(
            completer=DanaCompleter(self.repl),
            complete_while_typing=True,
            multiline=False,  # Single line for now, can be toggled
            history=None,  # We'll add history later
        )

        # Output buffer for displaying results
        self.output_buffer = Buffer(read_only=False)

        # Status information
        self.status_text = "Dana REPL | Ready"
        self.context_text = "Variables: 0 | Functions: 0 | Mode: Interactive"

        # Add welcome message
        self._add_output("Welcome to Dana REPL with persistent status bar!")
        self._add_output("Type your Dana code and press Enter to execute.")
        self._add_output("Press Ctrl+C to exit.\n")

        # Create the application
        self.app = self._create_application()

    def _create_application(self) -> Application:
        """Create the prompt_toolkit Application."""

        # Key bindings
        kb = KeyBindings()

        @kb.add("c-c")
        def _(event):
            """Handle Ctrl+C - cancel current input or exit."""
            if self.input_buffer.text:
                # Clear current input
                self.input_buffer.reset()
            else:
                # Exit application
                event.app.exit()

        @kb.add("enter")
        def _(event):
            """Handle Enter key - execute input."""
            text = self.input_buffer.text.strip()
            if text:
                # Execute the code asynchronously
                asyncio.create_task(self._execute_code(text))
                # Clear the input buffer
                self.input_buffer.reset()

        @kb.add(Keys.Tab)
        def _(event):
            """Handle tab completion."""
            b = event.app.current_buffer
            if b.complete_state:
                b.complete_next()
            else:
                b.start_completion(select_first=True)

        # Status bar controls
        status_control = FormattedTextControl(
            text=self._get_status_line1,
            show_cursor=False,
        )

        context_control = FormattedTextControl(
            text=self._get_status_line2,
            show_cursor=False,
        )

        # Main input control
        input_control = BufferControl(
            buffer=self.input_buffer,
            lexer=self.dana_lexer,
            include_default_input_processors=True,
        )

        # Output control for displaying results
        output_control = BufferControl(
            buffer=self.output_buffer,
            include_default_input_processors=False,
        )

        # Create the layout
        layout = Layout(
            HSplit(
                [
                    # Output area (shows results and history)
                    Window(
                        content=output_control,
                        height=Dimension(weight=1),  # Take most space
                        wrap_lines=True,
                        scroll_offsets=lambda: (1, 0),  # Keep cursor visible
                    ),
                    # Input area (single line at top of status bar)
                    Window(
                        content=input_control,
                        height=1,  # Single line
                        wrap_lines=False,
                        always_hide_cursor=False,
                    ),
                    # Status bar area (fixed 2 rows at bottom)
                    HSplit(
                        [
                            Window(
                                content=status_control,
                                height=1,  # Exactly 1 row
                                style="class:status-bar",
                                align=WindowAlign.LEFT,
                            ),
                            Window(
                                content=context_control,
                                height=1,  # Exactly 1 row
                                style="class:status-bar",
                                align=WindowAlign.LEFT,
                            ),
                        ]
                    ),
                ]
            )
        )

        # Define styles
        style = Style.from_dict(
            {
                # Main area styles
                "text-area": "",
                # Status bar styles
                "status-bar": "bg:#4444aa fg:#ffffff",  # Blue background, white text
                # Syntax highlighting
                "pygments.keyword": "#88ff88",  # Light green for keywords
                "pygments.string": "#ffaaff",  # Light magenta for strings
                "pygments.number": "#aaaaff",  # Light blue for numbers
                "pygments.comment": "#888888",  # Gray for comments
            }
        )

        return Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=True,
            refresh_interval=0.5,  # Refresh status every 500ms
        )

    def _get_status_line1(self) -> FormattedText:
        """Get the first status line."""
        return FormattedText([("class:status-bar", f" {self.status_text}".ljust(80))])

    def _get_status_line2(self) -> FormattedText:
        """Get the second status line."""
        return FormattedText([("class:status-bar", f" {self.context_text}".ljust(80))])

    def _add_output(self, text: str):
        """Add text to the output buffer."""
        current_text = self.output_buffer.text
        if current_text:
            new_text = current_text + "\n" + text
        else:
            new_text = text

        self.output_buffer.text = new_text
        # Move cursor to end
        self.output_buffer.cursor_position = len(new_text)

    def update_status(self, message: str = "Ready"):
        """Update the status message."""
        self.status_text = f"Dana REPL | {message}"
        self._update_context_info()

        # Trigger a refresh of the application
        if hasattr(self, "app") and self.app.is_running:
            self.app.invalidate()

    def _update_context_info(self):
        """Update context information."""
        try:
            # Count variables in different scopes
            var_count = 0
            func_count = 0
            context = self.repl.context

            for scope in ["private", "public", "local", "system"]:
                scope_vars = context._state.get(scope, {})
                for var_name in scope_vars.keys():
                    if not var_name.startswith("_"):  # Skip internal variables
                        var_count += 1

            # Count available functions
            try:
                registry = self.repl.interpreter.function_registry
                for scope in ["system", "private", "public"]:
                    functions = registry.list_functions(scope) or []
                    func_count += len(functions)
            except Exception:
                pass

            self.context_text = f"Variables: {var_count} | Functions: {func_count} | Mode: Interactive"

        except Exception:
            self.context_text = "Variables: ? | Functions: ? | Mode: Interactive"

    async def _execute_code(self, code: str):
        """Execute Dana code asynchronously."""
        try:
            # Show the input in the output
            self._add_output(f">>> {code}")
            self.update_status("Executing...")

            # Execute the code
            result = await asyncio.get_event_loop().run_in_executor(None, self.repl.execute, code)

            # Show result in output area
            if result is not None:
                self._add_output(f"{result}")

            self.update_status("Ready")

        except Exception as e:
            # Show error in output area
            self._add_output(f"Error: {e}")
            error_msg = str(e)[:40] + "..." if len(str(e)) > 40 else str(e)
            self.update_status(f"Error: {error_msg}")

    async def run_async(self):
        """Run the full-screen REPL application."""
        self.update_status("Ready")
        await self.app.run_async()

    def run(self):
        """Run the full-screen REPL application (synchronous)."""
        asyncio.run(self.run_async())
