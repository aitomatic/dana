"""
Prompt session management for Dana REPL.

This module provides the PromptSessionManager class that sets up
and manages the prompt session with history, completion, and key bindings.

FIXED VERSION: Prevents blocking when background async tasks are running.
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
HISTORY_FILE = os.path.expanduser("~/.dana/repl_history")
MULTILINE_PROMPT = "... "
STANDARD_PROMPT = ">>> "
MAX_HISTORY_SIZE = 50000  # 50KB max for auto-suggest to prevent blocking


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

        # FIXED: Smart history and auto-suggest configuration to prevent blocking
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

            # Only enable auto-suggest and history search for reasonably sized history files
            if history_size <= MAX_HISTORY_SIZE:
                auto_suggest = AutoSuggestFromHistory()
                enable_history_search = True
                self.debug(f"Auto-suggest and history search enabled for history file ({history_size} bytes)")
            else:
                auto_suggest = None
                enable_history_search = False  # AGGRESSIVE FIX: Disable history search for large files
                self.info(f"Auto-suggest and history search disabled: history file too large ({history_size} bytes)")
        else:
            history = FileHistory(HISTORY_FILE)
            enable_history_search = True

        return PromptSession(
            history=history,
            auto_suggest=auto_suggest,  # Conditionally enabled based on history size
            completer=WordCompleter(keywords, ignore_case=True),
            key_bindings=kb,
            multiline=False,
            style=style,
            lexer=self.dana_lexer,  # Use our pygments lexer for syntax highlighting
            enable_history_search=enable_history_search,  # AGGRESSIVE FIX: Conditionally enabled
            # CRITICAL FIX: Disable features that cause blocking with background async tasks
            complete_while_typing=False,  # FIXED: Don't trigger completion on every keystroke
            complete_in_thread=False,  # FIXED: Don't use threads to avoid asyncio conflicts
            # AGGRESSIVE FIX: Disable additional features that could cause blocking
            swap_light_and_dark_colors=False,  # Disable color swapping
            mouse_support=False,  # Disable mouse support to prevent terminal issues
            enable_system_prompt=True,  # Enable system prompt for better terminal compatibility
            enable_suspend=True,  # Allow suspending the REPL with Ctrl+Z
            refresh_interval=0.1,  # Faster refresh to reduce perceived lag
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
            keywords.extend(["print", "log", "log_level", "reason", "llm"])

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
