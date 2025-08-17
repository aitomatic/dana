"""
Main entry point for Dana TUI.

Usage: python -m dana.apps.tui

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.common.utils.logging import DANA_LOGGER


def main():
    """Main entry point for the Dana TUI."""
    # Disable console logging when running TUI to avoid duplicate output
    # The TUI log panel will capture all logs instead
    DANA_LOGGER.disable_console_logging()

    from .tui_app import main as tui_main

    tui_main()


if __name__ == "__main__":
    main()
