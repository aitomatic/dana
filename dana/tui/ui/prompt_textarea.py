"""
Prompt-toolkit inspired input widget for Dana TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from pathlib import Path

from textual import on
from textual.binding import Binding
from textual.events import Key
from textual.message import Message
from textual.widgets import Input, TextArea
from textual_autocomplete import AutoComplete, DropdownItem, TargetState

from dana.common import DANA_LOGGER
from dana.core.lang.dana_sandbox import DanaSandbox

from ..ui.syntax_highlighter import dana_highlighter

_DANA_KEYWORDS = [
    # Control flow
    "if",
    "else",
    "elif",
    "for",
    "while",
    "break",
    "continue",
    "pass",
    # Functions and methods
    "def",
    "return",
    "deliver",
    "lambda",
    # Data structures and types
    "struct",
    "resource",
    "agent",
    "agent_blueprint",
    "agent_pool",
    # Type annotations
    "int",
    "float",
    "str",
    "bool",
    "list",
    "dict",
    "tuple",
    "set",
    "None",
    "any",
    # Exception handling
    "try",
    "except",
    "finally",
    "raise",
    "assert",
    # Context management
    "with",
    "as",
    # Import/export
    "import",
    "from",
    "export",
    "use",
    # Scope modifiers
    "private",
    "public",
    "local",
    "system",
    # Logical operators
    "and",
    "or",
    "not",
    "in",
    "is",
    # Other keywords
    "True",
    "False",
    "None",
]

_DANA_FUNCTIONS = [
    "print",
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
    "sum",
    "max",
    "min",
    "abs",
    "sorted",
    "reversed",
    "filter",
    "map",
    "any",
    "all",
]


class _DanaInput(Input):
    """A custom Input widget to reliably handle key events for the REPL."""

    def __init__(self, owner: "PromptStyleTextArea", index: int = -1, **kwargs):
        super().__init__(**kwargs)
        self._owner = owner
        self._index = index

    async def on_key(self, event: Key) -> None:
        """Forward key events to the parent PromptStyleInput for handling."""
        await self._owner._handle_input_key(event, self._index)
        # await self._handle_input_key(event)


class PromptStyleTextArea(TextArea):
    """
    Enhanced input widget inspired by prompt-toolkit.

    Features:
    - Multi-line editing with \\ (backslash) for new lines
    - Enter to execute (single or multi-line)
    - Enhanced history navigation with / (forward slash) or ↑/↓ arrows
    - Persistent command history
    - Dana syntax highlighting
    - Copy/paste support with Ctrl+C/Ctrl+V
    """

    BINDINGS = [
        Binding("ctrl+c", "copy_selection", "Copy", show=False),
        Binding("ctrl+v", "paste_text", "Paste", show=False),
        Binding("ctrl+x", "cut_selection", "Cut", show=False),
    ]

    class Submitted(Message):
        """Message sent when user submits input."""

        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    class TextChanged(Message):
        """Message sent when input text changes."""

        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    def __init__(self, sandbox: DanaSandbox, **kwargs):
        # Configure for optimal Dana syntax highlighting
        super().__init__(
            language="python",  # Python syntax is closest to Dana - covers most keywords, strings, numbers
            theme="monokai",  # Built-in theme with good contrast for terminals
            show_line_numbers=False,
            soft_wrap=True,  # Enable soft wrapping for long lines
            tab_behavior="indent",  # Better for code editing
            **kwargs,
        )

        self.sandbox = sandbox
        self._history: list[str] = []
        self._history_index = -1
        self._temp_content = ""  # Store current content when navigating history
        self._max_history = 1000

        # The Input widgets are the source of truth for user interaction.
        self._input_lines: list[_DanaInput] = []
        self._autocomplete: AutoComplete | None = None

        # Load history from file
        self._load_history()

    def on_mount(self) -> None:
        """Set up the initial input line and autocomplete."""
        # Create and set up the first input line
        self._focus_on_input_line(0)

    def focus(self, scroll_visible: bool = True) -> "PromptStyleTextArea":
        """Focus the last input line."""
        if self._input_lines:
            self._input_lines[-1].focus()
        return self

    def _focus_on_input_line(self, index: int) -> None:
        """Focus the input line at the given index."""
        if not self._input_lines:
            self._input_lines = []

        # Add new input lines if needed
        existing_lines = len(self._input_lines)
        for i in range(existing_lines, index + 1):
            self._add_new_input_line(index=i)
        # Focus the input line at the given index
        self._input_lines[index].focus()

    def _add_new_input_line(self, placeholder: str = "", index: int = -1) -> None:
        """Creates, mounts, and focuses a new _DanaInput widget."""
        new_input = _DanaInput(owner=self, placeholder="", classes="overlay-input", index=index, highlighter=dana_highlighter)
        self._input_lines.append(new_input)
        self.mount(new_input)
        # new_input.focus()

        # Autocomplete is driven by the currently focused input widget
        self._autocomplete = AutoComplete(
            target=self._input_lines[0],
            candidates=self._get_dana_completions,
            prevent_default_enter=False,
        )
        self.app.mount(self._autocomplete)

    def _get_dana_completions(self, state) -> list[DropdownItem]:
        """Get Dana completion candidates for textual_autocomplete."""
        word = state.text
        if not word:
            return []

        completions: list[DropdownItem] = []

        # Filter keywords and functions that start with the word
        for keyword in _DANA_KEYWORDS:
            if keyword.startswith(word):
                completions.append(DropdownItem(keyword))

        for func in _DANA_FUNCTIONS:
            if func.startswith(word):
                completions.append(DropdownItem(f"{func}("))

        # Add history completions
        history_completions = self._get_history_completions(word)
        completions.extend(DropdownItem(c) for c in history_completions)

        return sorted(completions, key=lambda c: c.value)

    def _get_history_completions(self, word: str) -> list[str]:
        """Get completions from command history."""
        if not word or not self._history:
            return []

        completions = []

        # Look for history entries that start with the word
        for entry in reversed(self._history):  # Most recent first
            if entry.strip().startswith(word):
                # Extract the first word or identifier from the history entry
                first_word = self._extract_first_word(entry.strip())
                if first_word and first_word not in completions:
                    completions.append(first_word)

        # Also look for any word in history that starts with our word
        for entry in reversed(self._history):
            words = entry.split()
            for word_in_entry in words:
                if word_in_entry.startswith(word) and word_in_entry not in completions:
                    completions.append(word_in_entry)

        return completions[:10]  # Limit to 10 history completions

    def _extract_first_word(self, text: str) -> str:
        """Extract the first word or identifier from text."""
        if not text:
            return ""

        # Skip leading whitespace
        start = 0
        while start < len(text) and text[start].isspace():
            start += 1

        if start >= len(text):
            return ""

        # Find the end of the first word/identifier
        end = start
        while end < len(text) and (text[end].isalnum() or text[end] in "_"):
            end += 1

        return text[start:end]

    def _update_autocomplete_candidates(self) -> None:
        """Update the autocomplete candidates based on the current word."""
        if not self._input_lines or not self._autocomplete:
            return

        # Update candidates for the currently focused input widget
        word = self._get_word_under_cursor()
        if not word:
            self._autocomplete.candidates = []
            return

        # Update candidates
        self._autocomplete.candidates = self._get_dana_completions(TargetState(text=word, cursor_position=len(word)))

    def _get_word_under_cursor(self) -> str:
        """Extract the word under the cursor from the overlay input."""
        if not self._input_lines:
            return ""
        text = self._input_lines[-1].value
        cursor_pos = self._input_lines[-1].cursor_position

        start = cursor_pos
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
            start -= 1

        end = cursor_pos
        while end < len(text) and (text[end].isalnum() or text[end] == "_"):
            end += 1

        return text[start:end]

    @on(Input.Changed)
    def _on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes to update autocomplete and sync text for syntax highlighting."""
        if event.input in self._input_lines:
            self._update_autocomplete_candidates()

    @on(Input.Submitted)
    def _on_input_submitted(self, event: Input.Submitted | None = None) -> None:
        """Handle command submission from any Input widget."""
        if event and hasattr(event, "input"):
            if event.input not in self._input_lines:
                return

            # If autocomplete is open, Enter should select the item, not submit.
            if self._autocomplete and self._autocomplete.styles.display == "block":
                event.input.focus()
                return

        # Combine text from all input lines to form the complete command.
        full_command = "\n".join(line.value for line in self._input_lines)

        DANA_LOGGER.debug(f"posting message: {full_command}")

        # Post the submission message to the REPL.
        self.post_message(self.Submitted(full_command))

        # Clear everything for the next command.
        self.clear()

    def watch_text(self, text: str) -> None:
        """Called when text changes - emit TextChanged message and update autocomplete."""
        # The overlay input is no longer the single source of truth for text
        # and autocomplete, so we don't need to keep it in sync here.
        self.post_message(self.TextChanged(text))

    def _get_history_file(self) -> Path:
        """Get path to history file."""
        dana_dir = Path.home() / ".dana"
        dana_dir.mkdir(exist_ok=True)
        return dana_dir / "tui_prompt_history.txt"

    def _load_history(self) -> None:
        """Load command history from file."""
        history_file = self._get_history_file()
        if history_file.exists():
            try:
                with open(history_file, encoding="utf-8") as f:
                    lines = f.read().strip().split("\n")
                    self._history = [line for line in lines if line.strip()]
                    # Limit history size
                    if len(self._history) > self._max_history:
                        self._history = self._history[-self._max_history :]
            except Exception:
                # If history file is corrupted, start fresh
                self._history = []

    def _save_history(self) -> None:
        """Save command history to file."""
        try:
            history_file = self._get_history_file()
            with open(history_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self._history))
        except Exception:
            # Silently fail if we can't save history
            pass

    def add_to_history(self, command: str) -> None:
        """Add a command to history."""
        command = command.strip()
        if not command:
            return

        # Remove duplicate if it exists and move to end
        if command in self._history:
            self._history.remove(command)

        self._history.append(command)

        # Limit history size
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # Reset history navigation
        self._history_index = -1
        self._temp_content = ""

        # Save to file
        self._save_history()

    def get_history(self) -> list[str]:
        """Get command history."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear command history."""
        self._history.clear()
        self._history_index = -1
        self._temp_content = ""
        self._save_history()

    def _navigate_history(self, direction: int) -> None:
        """Navigate through command history."""
        if not self._history:
            return

        # Save current content when starting history navigation
        if self._history_index == -1:
            self._temp_content = self._get_current_input_content()

        # Calculate new index
        new_index = self._history_index + direction

        if new_index < -1:
            new_index = len(self._history) - 1
        elif new_index >= len(self._history):
            new_index = -1

        self._history_index = new_index

        # Update content
        if self._history_index == -1:
            # Back to current/temp content
            content = self._temp_content
        else:
            # Show history item
            content = self._history[self._history_index]

        # Update input lines with the content
        self._set_input_content(content)

    def _get_current_input_content(self) -> str:
        """Get the current content from all input lines."""
        if not self._input_lines:
            return ""
        return "\n".join(line.value for line in self._input_lines)

    def _set_input_content(self, content: str) -> None:
        """Set the content of input lines."""
        if not self._input_lines:
            return

        lines = content.split("\n") if content else [""]

        # Clear existing input lines
        for line in self._input_lines:
            line.value = ""

        # Set content in existing lines and create new ones if needed
        for i, line_content in enumerate(lines):
            if i < len(self._input_lines):
                self._input_lines[i].value = line_content
            else:
                # Need to create a new input line
                self._focus_on_input_line(i)
                self._input_lines[i].value = line_content

        # Focus the last line and move cursor to end
        if lines:
            last_line_index = len(lines) - 1
            if last_line_index < len(self._input_lines):
                self._input_lines[last_line_index].focus()
                # Move cursor to end of line
                self._input_lines[last_line_index].cursor_position = len(lines[last_line_index])

    async def _handle_input_key(self, event: Key, line_index: int) -> None:
        """Handle key events forwarded from the _DanaInput widget."""
        # Backslash on the last line creates a new input line
        # die(f"event: {event.control}")
        if event.key == "backslash":  # and event.control is self._input_lines[-1]:
            event.key = "enter"  # simulate enter key press
            self._focus_on_input_line(line_index + 1)
            event.prevent_default()

        # Up/Down arrows - navigate history (basic implementation)
        elif event.key in ("up", "down", "pageup", "pagedown"):
            current_input = self._get_current_input_content()
            if current_input == "" or self._history_index != -1:
                if event.key in ("up", "pageup"):
                    self._navigate_history(-1)
                else:
                    self._navigate_history(1)
                # event.prevent_default()

        # Enter - submit the command
        elif event.key == "enter":
            self._on_input_submitted()
            event.key = "escape"
            # event.prevent_default()

    def clear(self):
        """Clear the contents of all input lines."""
        if self._input_lines:
            for line in self._input_lines:
                line.value = ""
            self._input_lines[0].focus()

        # Also clear the display text area
        result = super().clear()

        self.text = ""
        self._history_index = -1
        self._temp_content = ""
        return result

    @property
    def value(self) -> str:
        """Get the current input value."""
        return self.text

    @value.setter
    def value(self, text: str) -> None:
        """Set the current input value."""
        self.text = text
        if text:
            lines = text.split("\n")
            last_line_index = len(lines) - 1
            last_line_length = len(lines[last_line_index])
            self.cursor_location = (last_line_index, last_line_length)

    def get_current_line(self) -> str:
        """Get the current line content (for autocomplete)."""
        if not self.text:
            return ""
        lines = self.text.split("\n")
        current_row = self.cursor_location[0]
        if 0 <= current_row < len(lines):
            return lines[current_row]
        return ""

    def get_cursor_column(self) -> int:
        """Get cursor column position in current line (for autocomplete)."""
        return self.cursor_location[1]

    def get_autocomplete_status(self) -> str | None:
        """Get current autocomplete status for display."""
        # The overlay input is no longer the single source of truth for autocomplete status
        # and is managed by the AutoComplete widget itself.
        return None

    def action_copy_selection(self) -> None:
        """Copy selected text to clipboard."""
        try:
            import pyperclip

            if self.selected_text:
                pyperclip.copy(self.selected_text)
                # Optionally show a brief notification
                if hasattr(self, "notify"):
                    self.notify("Text copied to clipboard", timeout=1)
        except Exception:
            # Fallback to app clipboard if available
            try:
                if hasattr(self.app, "copy_to_clipboard"):
                    self.app.copy_to_clipboard(self.selected_text or "")
            except Exception:
                pass  # Silent fail - clipboard might not be available

    def action_paste_text(self) -> None:
        """Paste text from clipboard."""
        try:
            import pyperclip

            clipboard_text = pyperclip.paste()
            if clipboard_text:
                # Insert at cursor position
                cursor_row, cursor_col = self.cursor_location
                lines = self.text.split("\n") if self.text else [""]

                if cursor_row < len(lines):
                    current_line = lines[cursor_row]
                    # Insert clipboard text at cursor position
                    new_line = current_line[:cursor_col] + clipboard_text + current_line[cursor_col:]
                    lines[cursor_row] = new_line
                    self.text = "\n".join(lines)

                    # Move cursor to end of pasted text
                    if "\n" in clipboard_text:
                        # Multi-line paste
                        pasted_lines = clipboard_text.split("\n")
                        new_row = cursor_row + len(pasted_lines) - 1
                        new_col = len(pasted_lines[-1]) if len(pasted_lines) > 1 else cursor_col + len(clipboard_text)
                        self.cursor_location = (new_row, new_col)
                    else:
                        # Single line paste
                        self.cursor_location = (cursor_row, cursor_col + len(clipboard_text))
        except Exception:
            pass  # Silent fail - clipboard might not be available

    def action_cut_selection(self) -> None:
        """Cut selected text to clipboard."""
        try:
            import pyperclip

            if self.selected_text:
                pyperclip.copy(self.selected_text)
                # Delete the selected text
                self.delete_selection()
                # Optionally show a brief notification
                if hasattr(self, "notify"):
                    self.notify("Text cut to clipboard", timeout=1)
        except Exception:
            # Fallback to app clipboard if available
            try:
                if hasattr(self.app, "copy_to_clipboard"):
                    self.app.copy_to_clipboard(self.selected_text or "")
                    self.delete_selection()
            except Exception:
                pass  # Silent fail - clipboard might not be available
