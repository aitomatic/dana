"""
Prompt session management for Dana REPL.

This module provides the PromptSessionManager class that sets up
and manages the prompt session with history, completion, and key bindings.
"""

import os
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style

from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme, get_dana_lexer
from dana.core.repl.repl import REPL

# Constants
HISTORY_FILE = os.path.expanduser("~/.dana_history")
MULTILINE_PROMPT = "... "
STANDARD_PROMPT = ">>> "


class PromptSessionManager(Loggable):
    """Manages the prompt session for the Dana REPL."""

    def __init__(self, repl: REPL, colors: ColorScheme):
        """Initialize the prompt session manager."""
        super().__init__()
        self.repl = repl
        self.colors = colors
        self.dana_lexer = get_dana_lexer()
        self.prompt_session = self._setup_prompt_session()

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

        keywords = self._get_completion_keywords()

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
            }
        )

        return PromptSession(
            history=FileHistory(HISTORY_FILE),
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter(keywords, ignore_case=True),
            key_bindings=kb,
            multiline=False,
            style=style,
            lexer=self.dana_lexer,  # Use our pygments lexer for syntax highlighting
            enable_history_search=True,
            complete_while_typing=True,
            complete_in_thread=True,
            mouse_support=False,  # Disable mouse support to prevent terminal issues
            enable_system_prompt=True,  # Enable system prompt for better terminal compatibility
            enable_suspend=True,  # Allow suspending the REPL with Ctrl+Z
        )

    def _get_completion_keywords(self) -> list[str]:
        """Get keywords for tab completion."""
        keywords = [
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
        ]

        # Dynamically add core function names to keywords
        try:
            registry = self.repl.interpreter.function_registry
            core_functions = registry.list("local")
            if core_functions:
                keywords.extend(core_functions)
                self.debug(f"Added {len(core_functions)} core functions to tab completion: {core_functions}")
        except Exception as e:
            self.debug(f"Could not add core functions to tab completion: {e}")
            # Fallback: add known common functions
            keywords.extend(["print", "log", "log_level", "reason"])

        return keywords

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

    async def prompt_async(self, prompt_text: Any) -> str:
        """Get input asynchronously with the given prompt."""
        return await self.prompt_session.prompt_async(prompt_text)
