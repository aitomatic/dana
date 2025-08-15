#!/usr/bin/env python3
"""
Test script for Dana TUI logging functionality.

This script demonstrates how the TUI log panel captures existing logging messages
from the Dana logging system.

Usage:
    python demos/test_tui_logging.py
"""

import logging
import threading
import time

from dana.common.mixins.loggable import Loggable
from dana.common.utils import DANA_LOGGER


class TestService(Loggable):
    """Test service that demonstrates logging."""

    def __init__(self):
        super().__init__()
        self.info("TestService initialized")

    def process_data(self, data):
        self.debug(f"Processing {len(data)} items")
        for i, item in enumerate(data):
            self.debug(f"Processing item {i + 1}/{len(data)}: {item}")
            if i == 2:
                self.warning(f"Item {i + 1} might have issues")
            time.sleep(0.1)  # Simulate work
        self.info("Data processing completed")


def background_logging():
    """Generate logs in a background thread."""
    logger = logging.getLogger("dana.background")
    for i in range(10):
        logger.info(f"Background task {i + 1}/10")
        time.sleep(0.5)


def main():
    """Main test function."""
    print("Starting Dana TUI logging test...")
    print("Press Ctrl+Shift+L in the TUI to show/hide the log panel")
    print("You should see all these log messages appear in the panel:")
    print()

    # Configure logging to show all levels
    DANA_LOGGER.configure(level=logging.DEBUG, console=True)

    # Test basic logging
    DANA_LOGGER.debug("Debug message from DANA_LOGGER")
    DANA_LOGGER.info("Info message from DANA_LOGGER")
    DANA_LOGGER.warning("Warning message from DANA_LOGGER")
    DANA_LOGGER.error("Error message from DANA_LOGGER")

    # Test service logging
    service = TestService()
    service.process_data(["item1", "item2", "item3", "item4", "item5"])

    # Test different logger namespaces
    loggers = [
        ("dana.api", "API logger"),
        ("dana.core", "Core logger"),
        ("dana.agent", "Agent logger"),
        ("dana.framework", "Framework logger"),
    ]

    for logger_name, description in loggers:
        logger = logging.getLogger(logger_name)
        logger.info(f"Message from {description}")
        logger.warning(f"Warning from {description}")

    # Start background logging
    bg_thread = threading.Thread(target=background_logging, daemon=True)
    bg_thread.start()

    print("\nTest completed! Check the TUI log panel to see all messages.")
    print("The log panel should show:")
    print("- Messages from DANA_LOGGER")
    print("- Messages from Loggable mixin")
    print("- Messages from different logger namespaces")
    print("- Background thread messages")
    print("- Color-coded log levels")


if __name__ == "__main__":
    main()
