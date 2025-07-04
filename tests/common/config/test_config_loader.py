"""Tests for ConfigLoader class."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from dana.common.config.config_loader import ConfigLoader
from dana.common.exceptions import ConfigurationError


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
        """Test that config_dir returns correct dana library directory."""
        loader = ConfigLoader()
        config_dir = loader.config_dir

        # Should point to dana library directory (where default config is stored)
        assert config_dir.name == "dana", f"Expected dana library directory, got {config_dir}"

        # Verify it contains the expected library files
        assert (config_dir / "__init__.py").exists(), "Library directory should contain __init__.py"
        assert (config_dir / "dana_config.json").exists(), "Library directory should contain default dana_config.json"

    def test_load_config_from_path_valid_json(self):
        """Test loading valid JSON config from specific path."""
        loader = ConfigLoader()
        test_config = {"test_key": "test_value", "nested": {"key": 123}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
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
            with open(config_path, "w") as f:
                json.dump(test_config, f)

            result = loader.load_config("test_config.json")
            assert result == test_config, "Should load specific config file"
        finally:
            if config_path.exists():
                config_path.unlink()

    def test_get_default_config_env_var_priority(self):
        """Test that DANA_CONFIG environment variable takes priority."""
        loader = ConfigLoader()
        test_config = {"env_config": "priority_value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_config, f)
            temp_path = Path(f.name)

        try:
            with patch.dict(os.environ, {"DANA_CONFIG": str(temp_path)}):
                result = loader.get_default_config()
                assert result == test_config, "Should load from DANA_CONFIG path"
        finally:
            temp_path.unlink()

    def test_get_default_config_cwd_fallback(self):
        """Test that CWD is checked when env var not set."""
        loader = ConfigLoader()
        test_config = {"cwd_config": "fallback_value"}

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / loader.DEFAULT_CONFIG_FILENAME

            with open(config_file, "w") as f:
                json.dump(test_config, f)

            with patch("pathlib.Path.cwd", return_value=temp_path):
                with patch.dict(os.environ, {}, clear=True):
                    result = loader.get_default_config()
                    assert result == test_config, "Should load from CWD"

    def test_get_default_config_library_fallback(self):
        """Test that library directory is checked as final fallback."""
        loader = ConfigLoader()

        # The library should have a default config file
        lib_config_path = loader.config_dir / loader.DEFAULT_CONFIG_FILENAME
        assert lib_config_path.exists(), "Library should have default config"

        # Mock CWD to not have config file
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pathlib.Path.cwd", return_value=Path(temp_dir)):
                with patch.dict(os.environ, {}, clear=True):
                    result = loader.get_default_config()
                    assert isinstance(result, dict), "Should load from library default"
                    # Verify it has expected structure (based on current config)
                    assert "llm" in result, "Default config should have llm section"
                    assert "preferred_models" in result["llm"], "Default config should have preferred_models under llm"

    def test_get_default_config_no_file_found(self):
        """Test error when no config file found anywhere (corrupted installation)."""
        loader = ConfigLoader()

        # Mock CWD to empty directory and simulate missing library config by mocking Path(__file__)
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pathlib.Path.cwd", return_value=Path(temp_dir)):
                with patch.dict(os.environ, {}, clear=True):
                    # Mock __file__ to point to a fake location where no config exists
                    fake_config_file = Path(temp_dir) / "fake" / "common" / "config" / "config_loader.py"
                    with patch("dana.common.config.config_loader.__file__", str(fake_config_file)):
                        with pytest.raises(ConfigurationError, match="Default config .* not found"):
                            loader.get_default_config()

    def test_get_default_config_env_var_invalid_path(self):
        """Test error handling for invalid DANA_CONFIG path."""
        loader = ConfigLoader()

        with patch.dict(os.environ, {"DANA_CONFIG": "/invalid/path/config.json"}):
            with pytest.raises(ConfigurationError, match="Failed to load config from DANA_CONFIG"):
                loader.get_default_config()

    def test_user_override_behavior(self):
        """Test that user config in CWD overrides library default."""
        loader = ConfigLoader()

        # Create user override config
        user_config = {"user_override": True, "preferred_models": [{"name": "user:model"}]}

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            user_config_file = temp_path / loader.DEFAULT_CONFIG_FILENAME

            with open(user_config_file, "w") as f:
                json.dump(user_config, f)

            # User config should take precedence over library default
            with patch("pathlib.Path.cwd", return_value=temp_path):
                with patch.dict(os.environ, {}, clear=True):
                    result = loader.get_default_config()
                    assert result == user_config, "User config should override library default"
                    assert result["user_override"] is True, "Should contain user-specific config"


if __name__ == "__main__":
    unittest.main()
