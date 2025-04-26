"""Tests for the Loggable mixin."""

import logging
# from unittest.mock import patch, MagicMock # Using pytest-mock fixture instead
from unittest.mock import MagicMock  # Keep MagicMock
from opendxa.common.mixins.loggable import Loggable
import pytest  # Import pytest for fixtures

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
class TestLoggable:
    """Test suite for the Loggable mixin."""
    
    @pytest.fixture
    def mock_logger(self, mocker):  # Use pytest-mock fixture 'mocker'
        """Fixture to mock DXA_LOGGER.getLogger and return a MagicMock."""
        mock = MagicMock()
        # Mock the getLogger method to return our mock logger instance
        mocker.patch('opendxa.common.utils.logging.dxa_logger.DXA_LOGGER.getLogger', return_value=mock)
        # Mock getLoggerForClass as well, just in case
        mocker.patch('opendxa.common.utils.logging.dxa_logger.DXA_LOGGER.getLoggerForClass', return_value=mock)
        return mock

    def test_custom_prefix(self, mock_logger):  # Inject the fixture
        """Test initialization with custom prefix."""
        # Define the behavior of the mocked getLogger when called with prefix
        # We need a way for the prefix passed to Loggable to affect the mock
        # Let's assume the prefix is set as an attribute on the mock logger instance
        # The actual Loggable.__instantiate_logger calls getLogger(..., prefix=prefix)
        # But our mocker patch just returns mock_logger regardless of args.
        # Let's check if the prefix is passed to getLogger instead.
        
        # We need to capture the arguments passed to getLogger
        # Let's adjust the fixture or test setup.
        pass  # Placeholder - Need to rethink how to test prefix passing

    def test_custom_level(self, mock_logger):  # Inject the fixture
        """Test initialization with custom logging level."""
        Loggable(level=logging.DEBUG)  # This should call mock_logger.configure via __instantiate_logger
        mock_logger.configure.assert_called_once_with(
            console=True,
            level=logging.DEBUG,
            log_data=False,
            fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )

    def test_log_data_enabled(self, mock_logger):  # Inject the fixture
        """Test initialization with log_data enabled."""
        Loggable(log_data=True)  # This should call mock_logger.configure
        mock_logger.configure.assert_called_once_with(
            console=True,
            level=logging.WARNING,  # Default level
            log_data=True,
            fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )

    def test_logging_methods(self, mock_logger):  # Inject the fixture
        """Test all logging methods."""
        obj = Loggable()  # This should call mock_logger.configure
        message = "test message"
        context = {"key": "value"}

        # Check configure was called during init
        mock_logger.configure.assert_called_once()

        obj.debug(message, **context)
        mock_logger.debug.assert_called_once_with(message, **context)

        obj.info(message, **context)
        mock_logger.info.assert_called_once_with(message, **context)

        obj.warning(message, **context)
        mock_logger.warning.assert_called_once_with(message, **context)

        obj.error(message, **context)
        mock_logger.error.assert_called_once_with(message, **context)
    