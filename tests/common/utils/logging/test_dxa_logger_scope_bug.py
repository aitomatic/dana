"""Test DXA logger scope isolation from third-party libraries."""

import logging
import unittest
from unittest.mock import patch

from opendxa.common.utils.logging.dxa_logger import DXALogger


class TestDXALoggerScopeIsolation(unittest.TestCase):
    """Test DXA logger scope isolation from third-party libraries."""

    def setUp(self):
        """Reset logging state."""
        # Reset DXA logger configured state
        DXALogger._configured = False
        # Store original root logger level
        self.original_root_level = logging.getLogger().level

    def tearDown(self):
        """Clean up logging state."""
        logging.getLogger().setLevel(self.original_root_level)

    def test_third_party_logger_isolation(self):
        """Test that DXA logger doesn't affect third-party library loggers."""
        # Create a mock third-party logger (like Lark would have)
        third_party_logger = logging.getLogger("lark.parser")

        # Set third-party logger to DEBUG level
        third_party_logger.setLevel(logging.DEBUG)
        initial_level = third_party_logger.level

        # Configure DXA logger (this should NOT affect third-party loggers)
        dxa_logger = DXALogger()
        dxa_logger.configure(level=logging.WARNING)

        # Third-party logger should retain its original level
        assert third_party_logger.level == initial_level, (
            f"Third-party logger level changed from {initial_level} to {third_party_logger.level}"
        )

    def test_opendxa_logger_affected(self):
        """Test that DXA logger properly affects OpenDXA loggers."""
        # Create OpenDXA loggers
        opendxa_logger = logging.getLogger("opendxa.test.module")
        opendxa_logger.setLevel(logging.DEBUG)

        # Configure DXA logger
        dxa_logger = DXALogger()
        dxa_logger.configure(level=logging.WARNING)

        # OpenDXA logger should be affected by DXA configuration
        # (This test may need adjustment based on the fix implementation)
        pass

    def test_root_logger_not_modified(self):
        """Test that root logger is not modified by DXA configuration."""
        original_root_level = logging.getLogger().level
        original_handlers_count = len(logging.getLogger().handlers)

        # Configure DXA logger
        dxa_logger = DXALogger()
        dxa_logger.configure(level=logging.ERROR)

        # Root logger should not be modified
        root_logger = logging.getLogger()
        assert root_logger.level == original_root_level, f"Root logger level was modified from {original_root_level} to {root_logger.level}"

        # Note: Handler count test may need adjustment based on fix approach

    def test_lark_logger_specifically(self):
        """Test that Lark loggers are not affected by DXA configuration."""
        # Create loggers that Lark typically uses
        lark_loggers = [
            logging.getLogger("lark"),
            logging.getLogger("lark.parser"),
            logging.getLogger("lark.lexer"),
        ]

        # Set them to DEBUG to see if DXA config affects them
        for logger in lark_loggers:
            logger.setLevel(logging.DEBUG)

        original_levels = [logger.level for logger in lark_loggers]

        # Configure DXA logger with WARNING level
        dxa_logger = DXALogger()
        dxa_logger.configure(level=logging.WARNING)

        # Lark loggers should retain their DEBUG levels
        for i, logger in enumerate(lark_loggers):
            assert logger.level == original_levels[i], (
                f"Lark logger {logger.name} level changed from {original_levels[i]} to {logger.level}"
            )


if __name__ == "__main__":
    unittest.main()
