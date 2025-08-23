"""
Prompt session management for Dana REPL.

This module provides the PromptSessionManager class that sets up
and manages the prompt session with history, completion, and key bindings.

ENHANCED VERSION: Provides intelligent completion while managing async performance.
"""

import os
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame

from dana.apps.repl.repl import REPL
from dana.apps.repl.ui.status_display import StatusDisplay
from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme, get_dana_lexer

# Constants
HISTORY_FILE = os.path.expanduser("~/.dana/history_repl.txt")
MULTILINE_PROMPT = "... "
STANDARD_PROMPT = ">>> "
MAX_HISTORY_SIZE = 50000  # 50KB max for auto-suggest to prevent blocking


class StatusBarManager:
    """Manages the status bar content for the Dana REPL."""

    def __init__(self, repl: "REPL"):
        """Initialize the status bar manager."""
        self.repl = repl
        self._status_line1 = "Dana REPL | Ready"
        self._status_line2 = "Variables: 0 | Functions: 0 | Mode: Interactive"

    def get_status_text(self):
        """Get the current status text for display."""
        return [
            ("class:status-bar", f" {self._status_line1}".ljust(80)),
            ("class:status-bar", "\n"),
            ("class:status-bar", f" {self._status_line2}".ljust(80)),
        ]

    def update_context_info(self):
        """Update status with current context information."""
        try:
            # Count variables in different scopes
            var_count = 0
            func_count = 0
            context = self.repl.context

            for scope in ["private", "public", "local", "system"]:
                scope_vars = context._state.get(scope, {})
                for var_name, _var_value in scope_vars.items():
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

            self._status_line2 = f"Variables: {var_count} | Functions: {func_count} | Mode: Interactive"

        except Exception:
            self._status_line2 = "Variables: ? | Functions: ? | Mode: Interactive"

    def set_execution_status(self, status: str):
        """Set the execution status message."""
        self._status_line1 = f"Dana REPL | {status}"

    def set_error_status(self, error_msg: str):
        """Set an error status message."""
        # Truncate long error messages
        if len(error_msg) > 60:
            error_msg = error_msg[:57] + "..."
        self._status_line1 = f"Dana REPL | Error: {error_msg}"


class DanaCompleter(Completer):
    """Custom completer for Dana REPL with context awareness."""

    def __init__(self, repl: "REPL"):
        """Initialize the Dana completer."""
        self.repl = repl
        self.keywords = [
            # Commands
            "help",
            "exit",
            "quit",
            # Dana scopes
            "local",
            "private",
            "public",
            "system",
            # Common prefixes
            "local:",
            "private:",
            "public:",
            "system:",
            # Keywords
            "if",
            "else",
            "elif",
            "while",
            "func",
            "return",
            "try",
            "except",
            "for",
            "in",
            "break",
            "continue",
            "import",
            "not",
            "and",
            "or",
            "true",
            "false",
            "struct",
            "agent",
            "use",
            "export",
            # Common functions
            "print",
            "log",
            "reason",
            "len",
            "str",
            "int",
            "float",
            "bool",
            "list",
            "dict",
            "tuple",
            "set",
            "range",
            "enumerate",
            "zip",
        ]

    def get_completions(self, document: Document, complete_event):
        """Get completion suggestions for the current document."""
        current_word = document.get_word_before_cursor()

        # Get basic keyword completions
        for keyword in self.keywords:
            if keyword.startswith(current_word):
                yield Completion(keyword, start_position=-len(current_word))

        # Get context-aware variable completions
        try:
            context_vars = self._get_context_variables()
            for var_name in context_vars:
                if var_name.startswith(current_word):
                    yield Completion(var_name, start_position=-len(current_word))
        except Exception:
            pass  # Continue with basic completions if context fails

        # Get function completions from the function registry
        try:
            registry = self.repl.interpreter.function_registry
            for scope in ["system", "private", "public"]:
                functions = registry.list_functions(scope) or []
                for func_name in functions:
                    if func_name.startswith(current_word):
                        # Add parentheses for function calls
                        completion_text = f"{func_name}()"
                        yield Completion(completion_text, start_position=-len(current_word))
        except Exception:
            pass  # Continue with basic completions if registry fails

    def _get_context_variables(self):
        """Get available variables from the current sandbox context."""
        variables = []
        try:
            context = self.repl.context
            for scope in ["private", "public", "local", "system"]:
                scope_vars = context._state.get(scope, {})
                for var_name in scope_vars.keys():
                    if not var_name.startswith("_"):  # Skip internal variables
                        variables.append(f"{scope}:{var_name}")
                        variables.append(var_name)  # Also suggest without scope prefix
        except Exception:
            pass
        return variables


class PromptSessionManager(Loggable):
    """Manages the prompt session for the Dana REPL."""

    def __init__(self, repl: REPL, colors: ColorScheme):
        """Initialize the prompt session manager."""
        super().__init__()
        self.repl = repl
        self.colors = colors
        self.dana_lexer = get_dana_lexer()
        self.status_manager = StatusBarManager(repl)
        self.status_display = StatusDisplay(repl)
        self.prompt_session = self._setup_prompt_session()
        self.app = self._setup_application()

    def _setup_prompt_session(self) -> PromptSession:
        """Set up the prompt session with history and completion."""
        kb = KeyBindings()

        @kb.add(Keys.Tab)
        def _(event):
            """Handle tab completion."""
            b = event.app.current_buffer
            if b.complete_state:
                b.complete_next()
            else:
                b.start_completion(select_first=True)

        # Add Ctrl+R binding for reverse history search
        @kb.add("c-r")
        def _(event):
            """Start reverse incremental search."""
            b = event.app.current_buffer
            b.start_history_lines_completion()

        # Add ESC key binding for cancellation during execution
        @kb.add(Keys.Escape)
        def _(event):
            """Handle ESC key for operation cancellation."""
            # Check if we're currently executing a program
            if hasattr(self.repl, "_cancellation_requested"):
                # Signal cancellation
                self.repl.request_cancellation()
                event.app.output.write("\n⏹️  Cancelling operation...\n")
                event.app.output.flush()
            else:
                # Normal ESC behavior (clear current input)
                event.app.current_buffer.reset()

        # Use our custom Dana completer instead of simple word completer
        dana_completer = DanaCompleter(self.repl)

        # Define syntax highlighting style
        style = Style.from_dict(
            {
                # Prompt styles
                "prompt": "ansicyan bold",
                "prompt.dots": "ansiblue",
                # Syntax highlighting styles
                "pygments.keyword": "ansigreen",  # Keywords like if, else, while
                "pygments.name.builtin": "ansiyellow",  # Built-in names like private, public
                "pygments.string": "ansimagenta",  # String literals
                "pygments.number": "ansiblue",  # Numbers
                "pygments.operator": "ansicyan",  # Operators like =, +, -
                "pygments.comment": "ansibrightblack",  # Comments starting with #
                # Status bar styles
                "status-bar": "bg:ansiblue ansiwhite",  # Blue background, white text
                "status-bar.error": "bg:ansired ansiwhite bold",  # Red background for errors
            }
        )

        # Smart history and auto-suggest configuration to prevent blocking
        history = None
        auto_suggest = None
        enable_history_search = True

        # Ensure the .dana directory exists
        history_dir = os.path.dirname(HISTORY_FILE)
        if not os.path.exists(history_dir):
            os.makedirs(history_dir, exist_ok=True)

        if os.path.exists(HISTORY_FILE):
            history_size = os.path.getsize(HISTORY_FILE)
            history = FileHistory(HISTORY_FILE)

            # Enable auto-suggest for reasonably sized history files
            if history_size <= MAX_HISTORY_SIZE:
                auto_suggest = AutoSuggestFromHistory()
                enable_history_search = True
                self.debug(f"Auto-suggest and history search enabled for history file ({history_size} bytes)")
            else:
                # Still enable auto-suggest but with smaller history window for large files
                auto_suggest = AutoSuggestFromHistory()
                enable_history_search = True
                self.info(f"Auto-suggest enabled with potential performance impact: large history file ({history_size} bytes)")
        else:
            history = FileHistory(HISTORY_FILE)
            auto_suggest = AutoSuggestFromHistory()
            enable_history_search = True

        return PromptSession(
            history=history,
            auto_suggest=auto_suggest,  # Conditionally enabled based on history size
            completer=dana_completer,
            key_bindings=kb,
            multiline=False,
            style=style,
            lexer=self.dana_lexer,  # Use our pygments lexer for syntax highlighting
            enable_history_search=enable_history_search,  # Conditionally enabled
            # Re-enable intelligent completion features with careful async handling
            complete_while_typing=True,  # Enable real-time completion as you type
            complete_in_thread=True,  # Use threads to avoid blocking the main asyncio loop
            # Balanced approach: Enable useful features while maintaining performance
            swap_light_and_dark_colors=False,  # Keep disabled for performance
            mouse_support=False,  # Keep disabled to prevent terminal issues
            enable_system_prompt=True,  # Enable system prompt for better terminal compatibility
            enable_suspend=True,  # Allow suspending the REPL with Ctrl+Z
            refresh_interval=0.1,  # Faster refresh to reduce perceived lag
        )

    def _setup_application(self) -> Application:
        """Set up the full-screen application with status bar."""
        # Create a buffer for the main input
        input_buffer = Buffer(
            completer=DanaCompleter(self.repl),
            complete_while_typing=True,
            multiline=False,
            history=self.prompt_session.history,
            auto_suggest=self.prompt_session.auto_suggest,
        )

        # Create the status bar control
        status_control = FormattedTextControl(
            text=self.status_manager.get_status_text,
            show_cursor=False,
        )

        # Create the main input control
        input_control = BufferControl(
            buffer=input_buffer,
            lexer=self.dana_lexer,
            search_buffer_control=None,
        )

        # Create the layout
        layout = Layout(
            HSplit(
                [
                    # Main input area (takes most of the space)
                    Window(
                        content=input_control,
                        height=None,  # Take remaining space
                        wrap_lines=True,
                    ),
                    # Status bar (fixed 2 rows at bottom)
                    Frame(
                        Window(
                            content=status_control,
                            height=2,  # Exactly 2 rows
                            wrap_lines=False,
                            style="class:status-bar",
                        ),
                        title="Status",
                        style="class:status-bar",
                    ),
                ]
            )
        )

        # Create the application
        return Application(
            layout=layout,
            style=self.prompt_session.style,
            key_bindings=self.prompt_session.key_bindings,
            full_screen=True,
            mouse_support=False,
        )

    def get_prompt(self, in_multiline: bool) -> Any:
        """Get the appropriate prompt based on current state."""
        if self.colors.use_colors:
            # Use HTML formatting for the prompt which is more reliable than ANSI
            if in_multiline:
                return HTML("<ansicyan>... </ansicyan>")
            else:
                return HTML("<ansicyan>>>> </ansicyan>")
        else:
            return MULTILINE_PROMPT if in_multiline else STANDARD_PROMPT

    async def prompt_async(self, prompt_text: Any, show_status: bool = False) -> str:
        """Get input asynchronously with the given prompt."""
        # Disabled status display by default to avoid output interference
        # Can be enabled with show_status=True when needed

        try:
            result = await self.prompt_session.prompt_async(prompt_text)
            return result
        except Exception as e:
            if show_status:
                self.status_display.show_error(str(e))
            raise

    def update_status(self, message: str = "Ready", error: str = None):
        """Update the status display with current information."""
        if error:
            self.status_display.show_error(error)
        else:
            self.status_display.show_status(message)

    def clear_status(self):
        """Clear the status display."""
        self.status_display.clear_status()

    def get_status_display(self) -> StatusDisplay:
        """Get the status display for direct access."""
        return self.status_display
