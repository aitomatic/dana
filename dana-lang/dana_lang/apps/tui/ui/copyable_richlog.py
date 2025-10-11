"""
Copyable RichLog widget that supports text selection and clipboard operations.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from textual.binding import Binding
from textual.widgets import RichLog


class CopyableRichLog(RichLog):
    """RichLog widget with copy/paste functionality."""

    BINDINGS = [
        Binding("ctrl+shift+c", "copy_selection", "Copy", show=False),
        Binding("ctrl+shift+a", "select_all", "Select All", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_text = ""

    def action_copy_selection(self) -> None:
        """Copy selected text to clipboard using Textual's built-in functionality."""
        # For RichLog, we'll copy all visible text since RichLog doesn't have text selection
        # This is a limitation of RichLog - it's primarily for display, not interaction

        # Get the console content
        if hasattr(self, "_console") and self._console:
            try:
                # Get the text content from the console
                text = self._console.export_text(clear=False)
                if text.strip():
                    self.app.copy_to_clipboard(text)
                    if hasattr(self.app, "notify"):
                        self.app.notify("Output copied to clipboard", timeout=1)
                else:
                    if hasattr(self.app, "notify"):
                        self.app.notify("No content to copy", timeout=1)
            except Exception:
                # Fallback: copy from internal lines if available
                try:
                    if hasattr(self, "_lines") and self._lines:
                        text = "\n".join(str(line) for line in self._lines)
                        self.app.copy_to_clipboard(text)
                        if hasattr(self.app, "notify"):
                            self.app.notify("Output copied to clipboard", timeout=1)
                    else:
                        if hasattr(self.app, "notify"):
                            self.app.notify("No content to copy", timeout=1)
                except Exception:
                    if hasattr(self.app, "notify"):
                        self.app.notify("Failed to copy content", timeout=1)

    def action_select_all(self) -> None:
        """Select all text (and copy it since RichLog doesn't support visual selection)."""
        self.action_copy_selection()
