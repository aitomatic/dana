"""Tests for the DanaLogger class."""

import logging

from dana.common.utils.logging.dana_logger import DanaLogger


def test_set_level_no_scope():
    """Test setting level for a specific logger instance only."""
    logger = DanaLogger("test.logger")
    logger.setLevel(logging.DEBUG, scope=None)  # Use None to affect only this logger
    assert logger.logger.level == logging.DEBUG


def test_set_level_all_loggers():
    """Test setting level for all loggers."""
    # Create some test loggers
    logger1 = logging.getLogger("test.logger1")
    logger2 = logging.getLogger("test.logger2")
    logger3 = logging.getLogger("other.logger")

    # Set different initial levels
    logger1.setLevel(logging.INFO)
    logger2.setLevel(logging.WARNING)
    logger3.setLevel(logging.ERROR)

    # Set level for all loggers
    dana_logger = DanaLogger("test")
    dana_logger.setLevel(logging.DEBUG, "*")

    # Verify all loggers have the new level
    assert logger1.level == logging.DEBUG
    assert logger2.level == logging.DEBUG
    assert logger3.level == logging.DEBUG


def test_set_level_module_path():
    """Test setting level for loggers with specific prefix."""
    # Create test loggers
    logger1 = logging.getLogger("dana.builtin_types.agent")
    logger2 = logging.getLogger("dana.base")
    logger3 = logging.getLogger("other.module")

    # Set different initial levels
    logger1.setLevel(logging.INFO)
    logger2.setLevel(logging.WARNING)
    logger3.setLevel(logging.ERROR)

    # Set level for dana loggers
    dana_logger = DanaLogger("test")
    dana_logger.setLevel(logging.DEBUG, "dana")

    # Verify only dana loggers changed
    assert logger1.level == logging.DEBUG
    assert logger2.level == logging.DEBUG
    assert logger3.level == logging.ERROR  # Should remain unchanged


def test_set_level_submodule():
    """Test setting level for specific submodule."""
    # Create test loggers
    logger1 = logging.getLogger("dana.builtin_types.agent")
    logger2 = logging.getLogger("dana.builtin_types.agent")
    logger3 = logging.getLogger("dana.base")

    # Set different initial levels
    logger1.setLevel(logging.INFO)
    logger2.setLevel(logging.WARNING)
    logger3.setLevel(logging.ERROR)

    # Set level for agent module only
    dana_logger = DanaLogger("test")
    dana_logger.setLevel(logging.DEBUG, "dana.builtin_types.agent")

    # Verify only agent loggers changed
    assert logger1.level == logging.DEBUG
    assert logger2.level == logging.DEBUG
    assert logger3.level == logging.ERROR  # Should remain unchanged
