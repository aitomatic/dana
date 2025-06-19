"""Test ConfigLoader debug/logging functionality."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from opendxa.common.config.config_loader import ConfigLoader
from opendxa.common.exceptions import ConfigurationError


class TestConfigLoaderDebug(unittest.TestCase):
    """Test ConfigLoader debug/logging functionality."""

    def setUp(self):
        """Reset singleton for clean tests."""
        ConfigLoader._instance = None

    def tearDown(self):
        """Clean up after tests."""
        ConfigLoader._instance = None

    def test_log_debug_method_exists(self):
        """Test that log_debug method exists and is callable."""
        loader = ConfigLoader()
        # This should not raise an error
        loader.log_debug("test message")

    def test_get_default_config_calls_log_debug_with_env_var(self):
        """Test that get_default_config calls log_debug when OPENDXA_CONFIG is set."""
        loader = ConfigLoader()
        test_config = {"env_config": "test_value"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_path = Path(f.name)
        
        try:
            # This should trigger the log_debug call at line 127-129
            with patch.dict(os.environ, {'OPENDXA_CONFIG': str(temp_path)}):
                with patch.object(loader, 'log_debug') as mock_log:
                    result = loader.get_default_config()
                    mock_log.assert_called_with(f"Attempting to load config from OPENDXA_CONFIG: {temp_path}")
        finally:
            temp_path.unlink()

    def test_get_default_config_calls_log_debug_with_cwd(self):
        """Test that get_default_config calls log_debug when loading from CWD."""
        loader = ConfigLoader()
        test_config = {"cwd_config": "test_value"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / loader.DEFAULT_CONFIG_FILENAME
            
            with open(config_file, 'w') as f:
                json.dump(test_config, f)
            
            # This should trigger the log_debug call at line 139
            with patch('pathlib.Path.cwd', return_value=temp_path):
                with patch.dict(os.environ, {}, clear=True):
                    with patch.object(loader, 'log_debug') as mock_log:
                        result = loader.get_default_config()
                        mock_log.assert_called_with(f"Attempting to load config from CWD: {config_file}")

    def test_get_default_config_calls_log_debug_with_project_root(self):
        """Test that get_default_config calls log_debug when loading from project root."""
        loader = ConfigLoader()
        test_config = {"root_config": "test_value"}
        
        # Create config in project root
        config_path = loader.config_dir / loader.DEFAULT_CONFIG_FILENAME
        
        try:
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # This should trigger the log_debug call at line 146
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                    with patch.dict(os.environ, {}, clear=True):
                        with patch.object(loader, 'log_debug') as mock_log:
                            result = loader.get_default_config()
                            mock_log.assert_called_with(f"Attempting to load config from project root: {config_path}")
        finally:
            if config_path.exists():
                config_path.unlink()


if __name__ == "__main__":
    unittest.main()