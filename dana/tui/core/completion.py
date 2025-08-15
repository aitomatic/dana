"""
Dana language completion provider for textual-autocomplete.

Provides intelligent autocompletion for Dana keywords, built-in functions,
variables, and language constructs.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os

from textual import events
from textual.widgets import Input
from textual_autocomplete import AutoComplete, DropdownItem, TargetState

from dana.libs.corelib.py_builtins.register_py_builtins import PythonicBuiltinsFactory

from .runtime import DanaSandbox


def get_dana_completion_candidates(state: TargetState) -> list[DropdownItem]:
    """Generate Dana completion candidates based on the current input state."""
    candidates = []

    # Get current text and find the word being typed
    text = state.text
    current_word = _get_current_word(text)

    # Dana language keywords with categorized prefixes
    keywords = [
        # Control flow
        ("if", "🔀", "keyword"),
        ("else", "🔀", "keyword"),
        ("elif", "🔀", "keyword"),
        ("while", "🔄", "keyword"),
        ("for", "🔄", "keyword"),
        ("in", "🔄", "keyword"),
        ("break", "⏹️", "keyword"),
        ("continue", "⏭️", "keyword"),
        ("pass", "⏸️", "keyword"),
        ("return", "↩️", "keyword"),
        ("deliver", "📦", "keyword"),
        # Functions and classes
        ("def", "⚙️", "keyword"),
        ("lambda", "λ", "keyword"),
        ("struct", "🏗️", "keyword"),
        ("resource", "📊", "keyword"),
        ("agent", "🤖", "keyword"),
        ("agent_blueprint", "🤖", "keyword"),
        ("agent_pool", "🤖", "keyword"),
        # Exception handling
        ("try", "🛡️", "keyword"),
        ("except", "🛡️", "keyword"),
        ("finally", "🛡️", "keyword"),
        ("raise", "🚨", "keyword"),
        ("assert", "✅", "keyword"),
        # Import and modules
        ("import", "📦", "keyword"),
        ("from", "📦", "keyword"),
        ("as", "📦", "keyword"),
        ("export", "📤", "keyword"),
        ("use", "📥", "keyword"),
        # Context management
        ("with", "🔒", "keyword"),
        # Logical operators
        ("and", "🔣", "keyword"),
        ("or", "🔣", "keyword"),
        ("not", "🔣", "keyword"),
        ("is", "🔣", "keyword"),
        # Scoping
        ("private", "🔒", "scope"),
        ("public", "🌐", "scope"),
        ("local", "📍", "scope"),
        ("system", "💻", "scope"),
        # Literals
        ("True", "✅", "literal"),
        ("False", "❌", "literal"),
        ("None", "⭕", "literal"),
        ("null", "⭕", "literal"),
    ]

    # Dana type keywords
    types = [
        ("int", "🔢", "type"),
        ("float", "🔢", "type"),
        ("str", "📝", "type"),
        ("bool", "✅", "type"),
        ("list", "📋", "type"),
        ("dict", "📚", "type"),
        ("tuple", "📦", "type"),
        ("set", "🎯", "type"),
        ("any", "❓", "type"),
    ]

    # Built-in functions from Dana's Pythonic factory
    factory = PythonicBuiltinsFactory()
    builtin_functions = [(name, "🏗️", "builtin") for name in factory.get_available_functions()]

    # Common Dana functions
    core_functions = [
        ("print", "🖨️", "function"),
        ("log", "📝", "function"),
        ("case", "🔄", "function"),
        ("reason", "🧠", "function"),
        ("llm", "🤖", "function"),
        ("poet", "✨", "function"),
    ]

    # Combine all completion sources
    all_completions = keywords + types + builtin_functions + core_functions

    # Filter based on current word (if any)
    if current_word:
        current_word_lower = current_word.lower()
        filtered_completions = [
            (name, prefix, category) for name, prefix, category in all_completions if name.lower().startswith(current_word_lower)
        ]
    else:
        # If no current word, show most common completions
        common_items = [
            ("if", "🔀", "keyword"),
            ("for", "🔄", "keyword"),
            ("def", "⚙️", "keyword"),
            ("return", "↩️", "keyword"),
            ("import", "📦", "keyword"),
            ("print", "🖨️", "function"),
            ("len", "🏗️", "builtin"),
            ("range", "🏗️", "builtin"),
            ("True", "✅", "literal"),
            ("False", "❌", "literal"),
            ("None", "⭕", "literal"),
        ]
        filtered_completions = common_items

    # Convert to DropdownItem objects
    for name, prefix, category in filtered_completions:
        # Add parentheses for functions
        if category in ("function", "builtin"):
            completion_text = f"{name}("
        else:
            completion_text = name

        candidates.append(DropdownItem(main=completion_text, prefix=prefix))

    return candidates


def _get_current_word(text: str) -> str:
    """Extract the current word being typed."""
    if not text:
        return ""

    # Find the start of the current word
    i = len(text) - 1
    while i >= 0 and (text[i].isalnum() or text[i] == "_"):
        i -= 1

    return text[i + 1 :]


class DanaInput(Input):
    """Dana Input widget with integrated autocomplete and command history."""

    def __init__(self, sandbox: DanaSandbox = None, **kwargs):
        """Initialize Dana input with autocomplete and history.

        Args:
            sandbox: Optional DanaSandbox for context-aware completions
            **kwargs: Additional arguments passed to Input
        """
        super().__init__(**kwargs)
        self.sandbox = sandbox
        self._autocomplete: AutoComplete = None

        # Command history management
        self._history: list[str] = []
        self._history_index: int = -1
        self._current_input: str = ""
        self._max_history: int = 1000

        # Load persistent history
        self._load_history()

    def on_mount(self) -> None:
        """Set up autocomplete when the widget is mounted."""
        # Create autocomplete with dynamic candidates
        self._autocomplete = AutoComplete(
            target=self,
            candidates=get_dana_completion_candidates,
            prevent_default_enter=False,  # Allow Enter to submit
            prevent_default_tab=True,  # Tab for completion
        )

        # Mount the autocomplete widget
        self.app.mount(self._autocomplete)

    def add_to_history(self, command: str) -> None:
        """Add a command to the history.

        Args:
            command: The command to add to history
        """
        if not command or not command.strip():
            return

        command = command.strip()

        # Remove from history if it already exists (move to end)
        if command in self._history:
            self._history.remove(command)

        # Add to end of history
        self._history.append(command)

        # Limit history size
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # Reset history navigation
        self._history_index = -1
        self._current_input = ""

        # Save to persistent storage
        self._save_history()

    def _navigate_history(self, direction: int) -> None:
        """Navigate through command history.

        Args:
            direction: -1 for previous (up), 1 for next (down)
        """
        if not self._history:
            return

        # Save current input when starting history navigation
        if self._history_index == -1:
            self._current_input = self.value

        # Calculate new index
        if direction == -1:  # Up arrow - go to previous (older)
            if self._history_index == -1:
                self._history_index = len(self._history) - 1
            elif self._history_index > 0:
                self._history_index -= 1
        elif direction == 1:  # Down arrow - go to next (newer)
            if self._history_index == -1:
                return  # Already at newest
            elif self._history_index < len(self._history) - 1:
                self._history_index += 1
            else:
                # Return to current input
                self._history_index = -1
                self.value = self._current_input
                self.cursor_position = len(self.value)
                return

        # Set the input to the history item
        if 0 <= self._history_index < len(self._history):
            self.value = self._history[self._history_index]
            self.cursor_position = len(self.value)

    def _on_key(self, event: events.Key) -> None:
        """Handle key events for history navigation."""
        if event.key == "up":
            self._navigate_history(-1)
            event.prevent_default()
            event.stop()
        elif event.key == "down":
            self._navigate_history(1)
            event.prevent_default()
            event.stop()
        else:
            # Reset history navigation on any other key
            if self._history_index != -1 and event.key not in ("left", "right", "home", "end", "shift+left", "shift+right"):
                self._history_index = -1
                self._current_input = ""

    def _get_history_file(self) -> str:
        """Get the path to the history file."""
        # Store history in user's home directory
        home_dir = os.path.expanduser("~")
        dana_dir = os.path.join(home_dir, ".dana")

        # Create directory if it doesn't exist
        os.makedirs(dana_dir, exist_ok=True)

        return os.path.join(dana_dir, "tui_history.txt")

    def _load_history(self) -> None:
        """Load command history from persistent storage."""
        try:
            history_file = self._get_history_file()
            if os.path.exists(history_file):
                with open(history_file, encoding="utf-8") as f:
                    lines = f.read().splitlines()
                    # Remove empty lines and limit to max history
                    self._history = [line.strip() for line in lines if line.strip()][-self._max_history :]
        except Exception:
            # Fail gracefully if history loading fails
            self._history = []

    def _save_history(self) -> None:
        """Save command history to persistent storage."""
        try:
            history_file = self._get_history_file()
            with open(history_file, "w", encoding="utf-8") as f:
                for command in self._history:
                    f.write(f"{command}\n")
        except Exception:
            # Fail gracefully if history saving fails
            pass

    def get_history(self) -> list[str]:
        """Get a copy of the command history.

        Returns:
            List of historical commands
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear the command history."""
        self._history.clear()
        self._history_index = -1
        self._current_input = ""
        self._save_history()
