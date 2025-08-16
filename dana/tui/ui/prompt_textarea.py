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

        # Multi-line mode management
        self._multiline_mode = False
        self._multiline_buffer: list[str] = []

        # The Input widgets are the source of truth for user interaction.
        self._input_lines: list[_DanaInput] = []
        # Removed autocomplete - using history navigation only

        # Reference to prompt widget (will be set by parent)
        self._prompt = None

        # Load history from file
        self._load_history()

    def on_mount(self) -> None:
        """Set up the initial input line and autocomplete."""
        # Create and set up the first input line
        self._focus_on_input_line(0)

    def set_prompt_widget(self, prompt):
        """Set reference to the prompt widget for updating continuation prompt."""
        self._prompt = prompt

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
        # Removed autocomplete setup - using history navigation only

    @on(Input.Changed)
    def _on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for syntax highlighting."""
        # Autocomplete removed - just handle text changes for syntax highlighting
        pass

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
        # Backslash - create new line and enter/stay in multi-line mode
        if event.key == "backslash":
            current_line = self._input_lines[line_index].value.rstrip()

            # Enter multi-line mode if not already in it
            if not self._multiline_mode:
                self._multiline_mode = True
                self._multiline_buffer = [current_line]
                # Update prompt to show continuation
                if self._prompt:
                    self._prompt.update("...")
            else:
                # Already in multi-line mode, add current line to buffer
                self._multiline_buffer.append(current_line)

            # Create a new input line for continuation
            self._focus_on_input_line(line_index + 1)
            event.prevent_default()

        # Up/Down arrows - navigate history (basic implementation)
        elif event.key in ("up", "down", "pageup", "pagedown"):
            # Only allow history navigation when not in multi-line mode
            if not self._multiline_mode:
                current_input = self._get_current_input_content()
                if current_input == "" or self._history_index != -1:
                    if event.key in ("up", "pageup"):
                        self._navigate_history(-1)
                    else:
                        self._navigate_history(1)

        # Enter - handle based on multi-line mode
        elif event.key == "enter":
            current_line = self._input_lines[line_index].value.rstrip()  # Strip trailing whitespace

            if not self._multiline_mode:
                # Check if we should enter multi-line mode
                if current_line.endswith(":"):
                    self._multiline_mode = True
                    self._multiline_buffer = [current_line]
                    # Create a new input line for continuation
                    self._focus_on_input_line(line_index + 1)
                    # Update prompt to show continuation
                    if self._prompt:
                        self._prompt.update("...")
                    event.prevent_default()
                else:
                    # Single-line submission
                    self._on_input_submitted()
                    event.key = "escape"
            else:
                # We're in multi-line mode
                if current_line == "":  # Empty line signals end of multi-line
                    # Check if there are any non-empty lines after this one
                    has_content_after = False
                    for i in range(line_index + 1, len(self._input_lines)):
                        if self._input_lines[i].value.strip():
                            has_content_after = True
                            break

                    if not has_content_after:
                        # End multi-line mode and submit
                        self._multiline_mode = False
                        # Reset prompt
                        if self._prompt:
                            self._prompt.update("⏵")
                        self._on_input_submitted()
                        event.key = "escape"
                    else:
                        # Continue multi-line mode
                        self._multiline_buffer.append(current_line)
                        self._focus_on_input_line(line_index + 1)
                        event.prevent_default()
                else:
                    # Add line to buffer and continue
                    self._multiline_buffer.append(current_line)
                    self._focus_on_input_line(line_index + 1)
                    event.prevent_default()

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

        # Reset multi-line mode
        self._multiline_mode = False
        self._multiline_buffer = []

        # Reset prompt if we have reference to it
        if self._prompt:
            self._prompt.update("⏵")

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
