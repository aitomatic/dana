"""Tests for the DXALogger class."""

import logging

from opendxa.common.utils.logging.dxa_logger import DXALogger


def test_set_level_no_scope():
    """Test setting level for a specific logger instance only."""
    logger = DXALogger("test.logger")
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
    dxa_logger = DXALogger("test")
    dxa_logger.setLevel(logging.DEBUG, "*")

    # Verify all loggers have the new level
    assert logger1.level == logging.DEBUG
    assert logger2.level == logging.DEBUG
    assert logger3.level == logging.DEBUG


def test_set_level_module_path():
    """Test setting level for loggers with specific prefix."""
    # Create test loggers
    logger1 = logging.getLogger("opendxa.agent")
    logger2 = logging.getLogger("opendxa.base")
    logger3 = logging.getLogger("other.module")

    # Set different initial levels
    logger1.setLevel(logging.INFO)
    logger2.setLevel(logging.WARNING)
    logger3.setLevel(logging.ERROR)

    # Set level for opendxa loggers
    dxa_logger = DXALogger("test")
    dxa_logger.setLevel(logging.DEBUG, "opendxa")

    # Verify only opendxa loggers changed
    assert logger1.level == logging.DEBUG
    assert logger2.level == logging.DEBUG
    assert logger3.level == logging.ERROR  # Should remain unchanged


def test_set_level_submodule():
    """Test setting level for specific submodule."""
    # Create test loggers
    logger1 = logging.getLogger("opendxa.agent.core")
    logger2 = logging.getLogger("opendxa.agent.utils")
    logger3 = logging.getLogger("opendxa.base")

    # Set different initial levels
    logger1.setLevel(logging.INFO)
    logger2.setLevel(logging.WARNING)
    logger3.setLevel(logging.ERROR)

    # Set level for agent module only
    dxa_logger = DXALogger("test")
    dxa_logger.setLevel(logging.DEBUG, "opendxa.agent")

    # Verify only agent loggers changed
    assert logger1.level == logging.DEBUG
    assert logger2.level == logging.DEBUG
    assert logger3.level == logging.ERROR  # Should remain unchanged
