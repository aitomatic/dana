"""Tests for the Configurable mixin."""

import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from dana.common.exceptions import ConfigurationError
from dana.common.mixins.configurable import Configurable


# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
class TestConfigurable:
    """Test suite for the Configurable mixin."""

    def setup_method(self):
        """Clear any cached configurations."""
        Configurable.default_config = {}

    def test_default_initialization(self):
        """Test initialization with no parameters."""

        class TestConfig(Configurable):
            default_config = {"setting1": "default_value", "setting2": 42}

        obj = TestConfig()
        assert obj.config == TestConfig.default_config

    def test_initialization_with_overrides(self):
        """Test initialization with configuration overrides."""

        class TestConfig(Configurable):
            default_config = {"setting1": "default_value", "setting2": 42}

        obj = TestConfig(setting1="new_value", setting3="additional")
        assert obj.config["setting1"] == "new_value"
        assert obj.config["setting2"] == 42
        assert obj.config["setting3"] == "additional"

    def test_get_config_path(self):
        """Test getting configuration file path."""

        class TestConfig(Configurable):
            pass

        # Test with no path (should use default)
        path = TestConfig.get_config_path()
        assert path.name == "test_configurable.yaml"
        assert path.parent.name == "yaml"

        # Test with relative path
        path = TestConfig.get_config_path("test_configurable")
        assert path.name == "test_configurable.yaml"
        assert path.parent.name == "yaml"

        # Test with absolute path
        if os.name == 'nt':  # Windows
            abs_path = Path("C:/absolute/path/config.yaml")
        else:  # Unix-like systems
            abs_path = Path("/absolute/path/config.yaml")
        path = TestConfig.get_config_path(abs_path)
        assert path == abs_path

    @patch("builtins.open", new_callable=mock_open, read_data="setting1: test_value\nsetting2: 123")
    @patch("dana.common.utils.misc.Misc.load_yaml_config")
    # pylint: disable=unused-argument
    def test_load_config_from_file(self, mock_load_yaml, mock_file):
        """Test loading configuration from file."""

        class TestConfig(Configurable):
            default_config = {"setting1": "default_value", "setting2": 42}

        # Mock the YAML loading to return the expected config
        mock_load_yaml.return_value = {"setting1": "test_value", "setting2": 123}

        obj = TestConfig(config_path="test_configurable.yaml")
        # File values should override defaults (this fixes the original bug)
        assert obj.config["setting1"] == "test_value"  # From file
        assert obj.config["setting2"] == 123  # From file

    def test_validation_required(self):
        """Test required field validation."""

        class TestConfig(Configurable):
            def _validate_config(self):
                self._validate_required("required_field")

        with pytest.raises(ConfigurationError, match="Required configuration 'required_field' is missing"):
            TestConfig()

    def test_validation_type(self):
        """Test type validation."""

        class TestConfig(Configurable):
            def _validate_config(self):
                self._validate_type("setting1", str)

        with pytest.raises(ConfigurationError, match="Configuration 'setting1' must be of type str"):
            TestConfig(setting1=123)

    def test_validation_enum(self):
        """Test enum validation."""

        class TestConfig(Configurable):
            def _validate_config(self):
                self._validate_enum("setting1", ["value1", "value2"])

        with pytest.raises(ConfigurationError, match=r"Configuration 'setting1' must be one of \['value1', 'value2'\]"):
            TestConfig(setting1="invalid_value")

    def test_validation_path(self):
        """Test path validation."""

        class TestConfig(Configurable):
            def _validate_config(self):
                self._validate_path("setting1")

        with pytest.raises(ConfigurationError, match="Invalid path 'nonexistent'"):
            TestConfig(setting1="nonexistent")

    def test_get_set_methods(self):
        """Test get and set methods."""

        class TestConfig(Configurable):
            pass

        obj = TestConfig()
        obj.set("setting1", "value1")
        assert obj.get("setting1") == "value1"
        assert obj.get("nonexistent", "default") == "default"

    def test_update_method(self):
        """Test update method."""

        class TestConfig(Configurable):
            pass

        obj = TestConfig()
        obj.update({"setting1": "value1", "setting2": "value2"})
        assert obj.config["setting1"] == "value1"
        assert obj.config["setting2"] == "value2"

    @patch("builtins.open", new_callable=mock_open)
    def test_save_method(self, mock_file):
        """Test save method."""

        class TestConfig(Configurable):
            pass

        obj = TestConfig()
        obj.config = {"setting1": "value1"}
        obj.save("test_configurable.yaml")

        # Verify YAML was written correctly
        write_calls = mock_file().write.call_args_list
        written_content = "".join(call[0][0] for call in write_calls)
        assert written_content == "setting1: value1\n"

    def test_from_dict_method(self):
        """Test from_dict method."""

        class TestConfig(Configurable):
            pass

        config_dict = {"setting1": "value1"}
        obj = TestConfig.from_dict(config_dict)
        assert obj.config == config_dict

    def test_cross_os_path_handling(self):
        """Test cross-OS path handling with dot notation."""

        class TestConfig(Configurable):
            pass

        # Test that path handling works correctly across different OS
        # Test with a simple filename that should get .yaml extension
        path = TestConfig.get_config_path("testfile")
        assert path.name == "testfile.yaml"
        assert path.parent.name == "yaml"
        
        # Test with explicit extension
        path_with_ext = TestConfig.get_config_path("testfile.yaml")
        assert path_with_ext.name == "testfile.yaml"
        
        # Test that the path construction is cross-OS compatible
        # The path should be properly constructed regardless of OS
        path_str = str(path)
        assert "testfile" in path_str
        assert path_str.endswith(".yaml")

    def test_absolute_path_cross_os(self):
        """Test absolute path handling across different operating systems."""

        class TestConfig(Configurable):
            pass

        # Test that absolute paths work correctly on different OS
        if os.name == 'nt':  # Windows
            abs_path = Path("C:/test/config.yaml")
        else:  # Unix-like systems
            abs_path = Path("/test/config.yaml")
            
        result_path = TestConfig.get_config_path(abs_path)
        assert result_path == abs_path
        assert result_path.is_absolute()
