#!/usr/bin/env python3
"""
Test script to verify log level propagation to Loggable objects in the opendxa.dana namespace.
"""

import logging

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.sandbox.log_manager import LogLevel, LogManager


class TestLoggableDana(Loggable):
    """Test class in the opendxa.dana namespace."""

    def __init__(self):
        # Use a logger name in the opendxa.dana namespace
        super().__init__(logger_name="opendxa.dana.test")

    def log_all_levels(self):
        """Log messages at all levels."""
        self.debug("This is a DEBUG message from TestLoggableDana")
        self.info("This is an INFO message from TestLoggableDana")
        self.warning("This is a WARNING message from TestLoggableDana")
        self.error("This is an ERROR message from TestLoggableDana")


class TestLoggableOther(Loggable):
    """Test class in a different namespace."""

    def __init__(self):
        # Use a logger name outside the opendxa.dana namespace
        super().__init__(logger_name="opendxa.other.test")

    def log_all_levels(self):
        """Log messages at all levels."""
        self.debug("This is a DEBUG message from TestLoggableOther")
        self.info("This is an INFO message from TestLoggableOther")
        self.warning("This is a WARNING message from TestLoggableOther")
        self.error("This is an ERROR message from TestLoggableOther")


def print_separator(text):
    """Print a separator with text."""
    print("\n" + "=" * 70)
    print(f" {text} ".center(70, "="))
    print("=" * 70 + "\n")


def main():
    """Run the log level test."""
    # Create test objects
    dana_logger = TestLoggableDana()
    other_logger = TestLoggableOther()

    # Check initial log levels
    print_separator("INITIAL LOG LEVELS")
    print(f"DXA_LOGGER level: {logging.getLevelName(DXA_LOGGER.logger.level)}")
    print(f"Dana logger level: {logging.getLevelName(dana_logger.logger.logger.level)}")
    print(f"Other logger level: {logging.getLevelName(other_logger.logger.logger.level)}")

    # Check handlers
    print_separator("CHECKING LOGGER HANDLERS")
    print(f"Root logger handlers: {logging.getLogger().handlers}")
    print(f"DXA_LOGGER handlers: {DXA_LOGGER.logger.handlers}")
    print(f"Dana logger handlers: {dana_logger.logger.logger.handlers}")

    # Force debug configuration
    print_separator("FORCING DEBUG CONFIGURATION")
    # Configure with console handler at DEBUG level
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - [%(name)s] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)

    # Add handler to root logger if not already present
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    # Reconfigure DXA_LOGGER for debugging
    DXA_LOGGER.configure(level=logging.DEBUG, console=True)

    # Check handlers again
    print(f"Root logger handlers after config: {logging.getLogger().handlers}")
    print(f"Root logger level after config: {logging.getLevelName(logging.getLogger().level)}")
    print(f"DXA_LOGGER handlers after config: {DXA_LOGGER.logger.handlers}")
    print(f"DXA_LOGGER level after config: {logging.getLevelName(DXA_LOGGER.logger.level)}")

    # Log with default levels (minimal logs expected)
    print_separator("LOGS WITH DEFAULT LEVEL")
    dana_logger.log_all_levels()
    other_logger.log_all_levels()

    # Set debug level using LogManager for dana namespace
    print_separator("SETTING DEBUG LEVEL WITH LogManager")
    LogManager.set_system_log_level(LogLevel.DEBUG)

    # Check new log levels
    print_separator("NEW LOG LEVELS AFTER LogManager")
    print(f"DXA_LOGGER level: {logging.getLevelName(DXA_LOGGER.logger.level)}")
    print(f"Dana logger level: {logging.getLevelName(dana_logger.logger.logger.level)}")
    print(f"Other logger level: {logging.getLevelName(other_logger.logger.logger.level)}")

    # Log again with new levels (more logs expected for dana namespace)
    print_separator("LOGS AFTER SETTING DEBUG LEVEL")
    dana_logger.log_all_levels()
    other_logger.log_all_levels()

    # Test direct setting vs LogManager
    print_separator("TESTING DIRECT SETTING VS LogManager")
    # Reset levels
    DXA_LOGGER.setLevel(logging.WARNING)
    print(f"After direct reset - Dana logger level: {logging.getLevelName(dana_logger.logger.logger.level)}")

    # Set with LogManager again
    LogManager.set_system_log_level(LogLevel.DEBUG)
    print(f"After LogManager - Dana logger level: {logging.getLevelName(dana_logger.logger.logger.level)}")


if __name__ == "__main__":
    main()
