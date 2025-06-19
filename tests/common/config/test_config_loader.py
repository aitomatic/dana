"""Tests for ConfigLoader class."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from opendxa.common.config.config_loader import ConfigLoader
from opendxa.common.exceptions import ConfigurationError


class TestConfigLoader(unittest.TestCase):
    """Test cases for ConfigLoader functionality."""

    def setUp(self):
        """Reset singleton for clean tests."""
        ConfigLoader._instance = None

    def tearDown(self):
        """Clean up after tests."""
        ConfigLoader._instance = None

    def test_singleton_behavior(self):
        """Test that ConfigLoader implements singleton pattern correctly."""
        loader1 = ConfigLoader()
        loader2 = ConfigLoader()
        assert loader1 is loader2, "ConfigLoader should be a singleton"

    def test_config_dir_property(self):
        """Test that config_dir returns correct project root."""
        loader = ConfigLoader()
        config_dir = loader.config_dir
        
        # Should point to project root (3 levels up from this file)
        expected_path = Path(__file__).parent.parent.parent.parent / "opendxa"
        assert config_dir.name == "opendxa", f"Expected opendxa directory, got {config_dir}"

    def test_load_config_from_path_valid_json(self):
        """Test loading valid JSON config from specific path."""
        loader = ConfigLoader()
        test_config = {"test_key": "test_value", "nested": {"key": 123}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_path = Path(f.name)
        
        try:
            result = loader._load_config_from_path(temp_path)
            assert result == test_config, "Loaded config should match original"
        finally:
            temp_path.unlink()

    def test_load_config_from_path_nonexistent_file(self):
        """Test error handling when config file doesn't exist."""
        loader = ConfigLoader()
        nonexistent_path = Path("/this/path/does/not/exist.json")
        
        with pytest.raises(ConfigurationError, match="Config path does not point to a valid file"):
            loader._load_config_from_path(nonexistent_path)

    def test_load_config_from_path_invalid_json(self):
        """Test error handling for invalid JSON."""
        loader = ConfigLoader()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json content")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid JSON in config file"):
                loader._load_config_from_path(temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_specific_file(self):
        """Test loading a specific config file from project root."""
        loader = ConfigLoader()
        test_config = {"specific_config": "test_value"}
        
        # Create temp config in project root
        config_path = loader.config_dir / "test_config.json"
        
        try:
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            result = loader.load_config("test_config.json")
            assert result == test_config, "Should load specific config file"
        finally:
            if config_path.exists():
                config_path.unlink()

    def test_get_default_config_env_var_priority(self):
        """Test that OPENDXA_CONFIG environment variable takes priority."""
        loader = ConfigLoader()
        test_config = {"env_config": "priority_value"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_path = Path(f.name)
        
        try:
            with patch.dict(os.environ, {'OPENDXA_CONFIG': str(temp_path)}):
                result = loader.get_default_config()
                assert result == test_config, "Should load from OPENDXA_CONFIG path"
        finally:
            temp_path.unlink()

    def test_get_default_config_cwd_fallback(self):
        """Test that CWD is checked when env var not set."""
        loader = ConfigLoader()
        test_config = {"cwd_config": "fallback_value"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / loader.DEFAULT_CONFIG_FILENAME
            
            with open(config_file, 'w') as f:
                json.dump(test_config, f)
            
            with patch('pathlib.Path.cwd', return_value=temp_path):
                with patch.dict(os.environ, {}, clear=True):
                    result = loader.get_default_config()
                    assert result == test_config, "Should load from CWD"

    def test_get_default_config_project_root_fallback(self):
        """Test that project root is checked as final fallback."""
        loader = ConfigLoader()
        test_config = {"root_config": "final_fallback"}
        
        # Create config in project root
        config_path = loader.config_dir / loader.DEFAULT_CONFIG_FILENAME
        
        try:
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # Mock CWD to not have config file
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                    with patch.dict(os.environ, {}, clear=True):
                        result = loader.get_default_config()
                        assert result == test_config, "Should load from project root"
        finally:
            if config_path.exists():
                config_path.unlink()

    def test_get_default_config_no_file_found(self):
        """Test error when no config file found anywhere."""
        loader = ConfigLoader()
        
        # Mock CWD to empty directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):
                with patch.dict(os.environ, {}, clear=True):
                    # Ensure project root doesn't have config
                    config_path = loader.config_dir / loader.DEFAULT_CONFIG_FILENAME
                    if config_path.exists():
                        config_path.unlink()
                    
                    with pytest.raises(ConfigurationError, match="Default config .* not found"):
                        loader.get_default_config()

    def test_get_default_config_env_var_invalid_path(self):
        """Test error handling for invalid OPENDXA_CONFIG path."""
        loader = ConfigLoader()
        
        with patch.dict(os.environ, {'OPENDXA_CONFIG': '/invalid/path/config.json'}):
            with pytest.raises(ConfigurationError, match="Failed to load config from OPENDXA_CONFIG"):
                loader.get_default_config()


if __name__ == "__main__":
    unittest.main()