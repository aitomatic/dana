"""Tests for the Loggable mixin."""

import logging
from unittest.mock import patch, MagicMock
from opendxa.common.mixins.loggable import Loggable

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
class TestLoggable:
    """Test suite for the Loggable mixin."""
    
    @patch('opendxa.common.utils.logging.dxa_logger.DXA_LOGGER')
    @patch('opendxa.common.utils.logging.dxa_logger.DXALogger')
    def test_custom_prefix(self, mock_dxalogger_class, mock_dxa_logger):
        """Test initialization with custom prefix."""
        mock_logger = MagicMock()
        mock_dxalogger_class.return_value = mock_logger
        mock_dxa_logger.getLogger.return_value = mock_logger
        
        obj = Loggable(prefix="custom_prefix")
        assert obj.logger.prefix == "custom_prefix"
    
    @patch('opendxa.common.utils.logging.dxa_logger.DXA_LOGGER')
    @patch('opendxa.common.utils.logging.dxa_logger.DXALogger')
    def test_custom_level(self, mock_dxalogger_class, mock_dxa_logger):
        """Test initialization with custom logging level."""
        mock_logger = MagicMock()
        mock_dxalogger_class.return_value = mock_logger
        mock_dxa_logger.getLogger.return_value = mock_logger
        
        Loggable(level=logging.DEBUG)
        mock_logger.configure.assert_called_once_with(
            console=True,
            level=logging.DEBUG,
            log_data=False,
            fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
    
    @patch('opendxa.common.utils.logging.dxa_logger.DXA_LOGGER')
    @patch('opendxa.common.utils.logging.dxa_logger.DXALogger')
    def test_log_data_enabled(self, mock_dxalogger_class, mock_dxa_logger):
        """Test initialization with log_data enabled."""
        mock_logger = MagicMock()
        mock_dxalogger_class.return_value = mock_logger
        mock_dxa_logger.getLogger.return_value = mock_logger
        
        Loggable(log_data=True)
        mock_logger.configure.assert_called_once_with(
            console=True,
            level=logging.INFO,
            log_data=True,
            fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
    
    @patch('opendxa.common.utils.logging.dxa_logger.DXA_LOGGER')
    @patch('opendxa.common.utils.logging.dxa_logger.DXALogger')
    def test_logging_methods(self, mock_dxalogger_class, mock_dxa_logger):
        """Test all logging methods."""
        mock_logger = MagicMock()
        mock_dxalogger_class.return_value = mock_logger
        mock_dxa_logger.getLogger.return_value = mock_logger
        
        obj = Loggable()
        message = "test message"
        context = {"key": "value"}
        
        obj.debug(message, **context)
        mock_logger.debug.assert_called_once_with(message, **context)
        
        obj.info(message, **context)
        mock_logger.info.assert_called_once_with(message, **context)
        
        obj.warning(message, **context)
        mock_logger.warning.assert_called_once_with(message, **context)
        
        obj.error(message, **context)
        mock_logger.error.assert_called_once_with(message, **context)
    