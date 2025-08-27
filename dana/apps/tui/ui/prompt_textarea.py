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

# Removed autocomplete imports - using history navigation only
from dana.common import DANA_LOGGER
from dana.core.lang.dana_sandbox import DanaSandbox

from ..ui.syntax_highlighter import dana_highlighter

# Removed Dana keywords and functions lists - no longer needed for autocomplete


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
    - Multi-line editing:
      • Lines ending with ':' automatically enter multi-line mode
      • \\ (backslash) adds new line and enters/stays in multi-line mode
      • Empty line executes multi-line code
    - Enter to execute (single-line or end of multi-line)
    - Enhanced history navigation with ↑/↓ arrows (disabled in multi-line mode)
    - Persistent command history
    - Dana syntax highlighting
    - Copy/paste support with Ctrl+Shift+C/Ctrl+Shift+V/Ctrl+Shift+X
    """

    BINDINGS = [
        Binding("ctrl+shift+c", "copy", "Copy", show=False),
        Binding("ctrl+shift+v", "paste", "Paste", show=False),
        Binding("ctrl+shift+x", "cut", "Cut", show=False),
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

        # History management - completely rewritten
        self._history: list[str] = []
        self._history_index = -1  # -1 means not navigating history
        self._current_input = ""  # Store current input when navigating history
        self._max_history = 1000

        # Multi-line mode management
        self._multiline_mode = False
        self._multiline_buffer: list[str] = []

        # The Input widgets are the source of truth for user interaction.
        self._input_lines: list[_DanaInput] = []
        # Removed autocomplete - using history navigation only

        # Load history from file
        self._load_history()

    # ============================================================================
    # Lifecycle Methods
    # ============================================================================

    def on_mount(self) -> None:
        """Set up the initial input line and autocomplete."""
        # Create and set up the first input line
        self._focus_on_input_line(0)

    # ============================================================================
    # Public Interface Methods
    # ============================================================================

    def focus(self, scroll_visible: bool = True) -> "PromptStyleTextArea":
        """Focus the last input line."""
        if self._input_lines:
            self._input_lines[-1].focus()
        return self

    def clear(self):
        """Clear the contents of all input lines."""
        if self._input_lines:
            # Remove all input lines except the first one
            while len(self._input_lines) > 1:
                line = self._input_lines.pop()
                line.remove()  # Remove from DOM

            # Clear the first line and focus it
            if self._input_lines:
                self._input_lines[0].value = ""
                self._input_lines[0].focus()

        # Also clear the display text area
        result = super().clear()

        self.text = ""
        self._history_index = -1
        self._current_input = ""

        # Reset multi-line mode
        self._multiline_mode = False
        self._multiline_buffer = []

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

    # ============================================================================
    # Input Line Management
    # ============================================================================

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
        # Removed autocomplete setup - using history navigation only

    @on(Input.Changed)
    def _on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for syntax highlighting."""
        # Reset history navigation when user types
        self._reset_history_navigation()

    @on(Input.Submitted)
    def _on_input_submitted(self, event: Input.Submitted | None = None) -> None:
        """Handle command submission from any Input widget."""
        if event and hasattr(event, "input"):
            if event.input not in self._input_lines:
                return

        # Combine text from all input lines, stripping trailing whitespace from each
        lines = [line.value.rstrip() for line in self._input_lines]
        full_command = "\n".join(lines)

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

    # ============================================================================
    # History Management - COMPLETELY REWRITTEN
    # ============================================================================

    def _get_history_file(self) -> Path:
        """Get path to history file."""
        dana_dir = Path.home() / ".dana"
        dana_dir.mkdir(exist_ok=True)
        return dana_dir / "history_tui.txt"

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
        self._current_input = ""

        # Save to file
        self._save_history()

    def get_history(self) -> list[str]:
        """Get command history."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear command history."""
        self._history.clear()
        self._history_index = -1
        self._current_input = ""
        self._save_history()

    def _navigate_history(self, direction: int) -> None:
        """
        Navigate through command history with prefix filtering.

        Expected behavior:
        1. With prefix: Up arrow finds last matching item, down arrow finds next matching item
        2. Without prefix: Up arrow finds last item, down arrow finds next item
        3. Typing: Resets history navigation
        """
        if not self._history:
            return

        # Get current input content
        current_input = self._get_current_input_content()
        DANA_LOGGER.debug(f"current_input: {current_input}")

        # If we're not currently navigating history, save current input and start
        if self._history_index == -1:
            self._current_input = current_input
            DANA_LOGGER.debug(f"Starting history navigation with current_input: '{current_input}'")
            DANA_LOGGER.debug(f"History: {self._history}")

            # If we have a prefix, filter history to matching items
            if current_input:
                matching_indices = [i for i, item in enumerate(self._history) if item.startswith(current_input)]
                DANA_LOGGER.debug(f"Matching indices for '{current_input}': {matching_indices}")
                if not matching_indices:
                    return  # No matches, don't navigate

                # Start with the appropriate item based on direction
                if direction < 0:  # Up arrow - go to last match
                    self._history_index = matching_indices[-1]
                else:  # Down arrow - go to first match
                    self._history_index = matching_indices[0]
            else:
                # No prefix - navigate through all history
                if direction < 0:  # Up arrow - go to last item
                    self._history_index = len(self._history) - 1
                else:  # Down arrow - go to first item
                    self._history_index = 0

            DANA_LOGGER.debug(f"Set history_index to: {self._history_index}")
        else:
            # We're already navigating history
            DANA_LOGGER.debug(f"Already navigating history, current_input: '{current_input}', history_index: {self._history_index}")

            # Always filter by the original prefix (which doesn't change while cycling)
            matching_indices = [i for i, item in enumerate(self._history) if item.startswith(self._current_input)]
            DANA_LOGGER.debug(f"Filtering by original prefix '{self._current_input}': {matching_indices}")

            if not matching_indices:
                return  # No matches, don't navigate

            # Find current position in filtered list
            try:
                current_filtered_index = matching_indices.index(self._history_index)
            except ValueError:
                # Current index not in filtered list, start from beginning
                current_filtered_index = -1

            # Calculate new filtered index
            new_filtered_index = current_filtered_index + direction

            # Handle wrap around
            if new_filtered_index < 0:
                # Going up past first match - wrap to last match
                self._history_index = matching_indices[-1]
                DANA_LOGGER.debug(f"Wrapped up to last match: {self._history_index}")
            elif new_filtered_index >= len(matching_indices):
                # Going down past last match - wrap to first match
                self._history_index = matching_indices[0]
                DANA_LOGGER.debug(f"Wrapped down to first match: {self._history_index}")
            else:
                # Normal navigation within filtered list
                self._history_index = matching_indices[new_filtered_index]
                DANA_LOGGER.debug(f"Normal navigation within filtered list: {self._history_index}")

            DANA_LOGGER.debug(f"Final history_index: {self._history_index}")

        # Update content with the selected history item
        if self._history_index != -1:
            self._set_input_content(self._history[self._history_index])

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

    def _reset_history_navigation(self) -> None:
        """Reset history navigation when user starts typing."""
        # Only reset if we're currently navigating history and the current content
        # doesn't match any history item (indicating user typed something new)
        if self._history_index != -1:
            current_content = self._get_current_input_content()
            # Check if current content matches the history item we're on
            if self._history_index < len(self._history):
                expected_content = self._history[self._history_index]
                if current_content != expected_content:
                    # User typed something different, reset navigation
                    self._history_index = -1
                    self._current_input = ""
                    DANA_LOGGER.debug("Reset history navigation - content changed")
                else:
                    # Content matches history item, don't reset
                    DANA_LOGGER.debug("Not resetting - content matches history item")
            else:
                # Invalid history index, reset
                self._history_index = -1
                self._current_input = ""
                DANA_LOGGER.debug("Reset history navigation - invalid index")

    # ============================================================================
    # Key Event Handling
    # ============================================================================

    async def _handle_input_key(self, event: Key, line_index: int) -> None:
        """Handle key events forwarded from the _DanaInput widget."""

        # Multi-line continuation and submission keys
        if event.key in ("backslash", "enter"):
            # Common preprocessing
            current_line = self._input_lines[line_index].value.rstrip()

            # Key-specific handling
            if event.key == "backslash":
                self._continue_multiline_mode(line_index, current_line)
                event.prevent_default()
            else:  # enter
                if not self._multiline_mode:
                    self._handle_single_line_enter(event, line_index, current_line)
                else:
                    self._handle_multiline_enter(event, line_index, current_line)

            # Common post-processing
            self._post_multiline_processing(event, line_index)

        # History navigation keys
        elif event.key in ("up", "down", "pageup", "pagedown"):
            self._handle_history_navigation(event)

    def _handle_history_navigation(self, event: Key) -> None:
        """Handle history navigation with up/down arrow keys."""
        # Only allow history navigation when not in multi-line mode
        if not self._multiline_mode:
            if event.key in ("up", "pageup"):
                self._navigate_history(-1)
            else:
                self._navigate_history(1)
            # Prevent default arrow key behavior (cursor movement)
            event.prevent_default()

    def _post_multiline_processing(self, event: Key, line_index: int) -> None:
        """Common post-processing for multi-line continuation keys."""
        # This method can be extended with common post-processing logic
        # such as updating UI state, logging, etc.
        pass

    # ============================================================================
    # Multi-line Mode Handling
    # ============================================================================

    def _continue_multiline_mode(self, line_index: int, current_line: str, update_prompt: bool = False) -> None:
        """Helper method to continue multi-line mode by adding current line to buffer and creating new input line."""
        if not self._multiline_mode:
            self._multiline_mode = True
            self._multiline_buffer = [current_line]
        else:
            self._multiline_buffer.append(current_line)

        # Create a new input line for continuation
        self._focus_on_input_line(line_index + 1)

    def _handle_single_line_enter(self, event: Key, line_index: int, current_line: str) -> None:
        """Handle enter key in single-line mode."""
        # Check if we should enter multi-line mode
        if current_line.endswith(":"):
            self._continue_multiline_mode(line_index, current_line, update_prompt=True)
            event.prevent_default()
        else:
            # Single-line submission
            self._on_input_submitted()
            event.key = "escape"

    def _handle_multiline_enter(self, event: Key, line_index: int, current_line: str) -> None:
        """Handle enter key in multi-line mode."""
        if current_line == "":  # Empty line signals end of multi-line
            self._handle_empty_line_in_multiline(event, line_index)
        else:
            # Add line to buffer and continue
            self._continue_multiline_mode(line_index, current_line)
            event.prevent_default()

    def _handle_empty_line_in_multiline(self, event: Key, line_index: int) -> None:
        """Handle empty line in multi-line mode - check if we should end or continue."""
        # Check if there are any non-empty lines after this one
        has_content_after = False
        for i in range(line_index + 1, len(self._input_lines)):
            if self._input_lines[i].value.strip():
                has_content_after = True
                break

        if not has_content_after:
            # End multi-line mode and submit
            self._multiline_mode = False
            self._on_input_submitted()
            event.key = "escape"
        else:
            # Continue multi-line mode
            self._continue_multiline_mode(line_index, "")
            event.prevent_default()

    # ============================================================================
    # Action Methods
    # ============================================================================

    def action_cut(self) -> None:
        """Cut selected text to clipboard using Textual's built-in functionality."""
        if self.selected_text:
            # Copy to clipboard using Textual's method
            self.app.copy_to_clipboard(self.selected_text)
            # Remove selected text
            self.delete_selection()
            # Show notification
            if hasattr(self.app, "notify"):
                self.app.notify("Text cut to clipboard", timeout=1)
