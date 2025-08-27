"""
Log panel for Dana TUI that displays Python logging messages.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
import queue
import threading

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Static

from .copyable_richlog import CopyableRichLog


class LogMessage(Message):
    """Message for log updates from background thread."""

    def __init__(self, level: str, message: str):
        self.level = level
        self.message = message
        super().__init__()


class TextualLogHandler(logging.Handler):
    """Logging handler that sends messages to Textual UI."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.message_queue = queue.Queue()
        self._running = True

        # Start background thread
        self._thread = threading.Thread(target=self._process_messages, daemon=True)
        self._thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        if not self._running:
            return

        try:
            msg = self.format(record)
            self.message_queue.put((record.levelname, msg))
        except Exception:
            pass  # Don't crash on logging errors

    def _process_messages(self) -> None:
        """Process messages in background thread."""
        while self._running:
            try:
                level, message = self.message_queue.get(timeout=0.1)
                self.callback(level, message)
            except queue.Empty:
                continue
            except Exception:
                continue

    def close(self) -> None:
        """Close the handler."""
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
        super().close()


class LogPanel(Vertical):
    """Panel that displays logging messages."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._log_widget: CopyableRichLog | None = None
        self._handler: TextualLogHandler | None = None
        self._visible = False

    def compose(self) -> ComposeResult:
        """Create the log panel UI."""
        # Header
        with Horizontal(classes="panel-title"):
            yield Static("📋 Log Messages", id="log-title")
            yield Button("🗑️ Clear", id="log-clear-btn", variant="primary")
            yield Button("👁️ Show", id="log-toggle-btn", variant="default")

        # Log display - with copy functionality
        self._log_widget = CopyableRichLog(highlight=True, markup=True, wrap=False, id="log-output", auto_scroll=True)
        yield self._log_widget

    def on_mount(self) -> None:
        """Initialize when mounted."""
        # Set up logging handler
        self._setup_logging_handler()

        # Initially hidden
        self.display = False

    def _setup_logging_handler(self) -> None:
        """Set up the logging handler."""
        if not self._log_widget:
            return

        # Create handler with callback
        self._handler = TextualLogHandler(self._add_log_message)
        self._handler.setFormatter(logging.Formatter(fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s", datefmt="%H:%M:%S"))

        # Add to loggers
        dana_logger = logging.getLogger("dana")
        dana_logger.addHandler(self._handler)

        root_logger = logging.getLogger()
        root_logger.addHandler(self._handler)

    def _add_log_message(self, level: str, message: str) -> None:
        """Add a log message to the display (called from background thread)."""
        # Post to main thread
        self.post_message(LogMessage(level=level, message=message))

    def on_log_message(self, event: LogMessage) -> None:
        """Handle log message from background thread."""
        if not self._log_widget:
            return

        # Color coding
        colors = {"DEBUG": "cyan", "INFO": "green", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "magenta"}

        color = colors.get(event.level, "white")
        self._log_widget.write(f"[{color}]{event.message}[/{color}]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "log-clear-btn":
            self._clear_logs()
        elif event.button.id == "log-toggle-btn":
            self._toggle_visibility()

    def _clear_logs(self) -> None:
        """Clear the log display."""
        if self._log_widget:
            self._log_widget.clear()

    def _toggle_visibility(self) -> None:
        """Toggle panel visibility."""
        self._visible = not self._visible
        self.display = self._visible

        # Update button
        toggle_btn = self.query_one("#log-toggle-btn", Button)
        if toggle_btn:
            toggle_btn.label = "👁️ Hide" if self._visible else "👁️ Show"

    def show(self) -> None:
        """Show the panel."""
        self._visible = True
        self.display = True
        toggle_btn = self.query_one("#log-toggle-btn", Button)
        if toggle_btn:
            toggle_btn.label = "👁️ Hide"

    def hide(self) -> None:
        """Hide the panel."""
        self._visible = False
        self.display = False
        toggle_btn = self.query_one("#log-toggle-btn", Button)
        if toggle_btn:
            toggle_btn.label = "👁️ Show"

    def is_visible(self) -> bool:
        """Check if panel is visible."""
        return self._visible

    def on_unmount(self) -> None:
        """Clean up when unmounted."""
        if self._handler:
            self._handler.close()

            # Remove from loggers
            dana_logger = logging.getLogger("dana")
            root_logger = logging.getLogger()

            try:
                dana_logger.removeHandler(self._handler)
                root_logger.removeHandler(self._handler)
            except ValueError:
                pass
