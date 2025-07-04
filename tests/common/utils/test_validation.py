"""Tests for validation utilities."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dana.common.utils.validation import ValidationError, ValidationUtilities


class TestValidationUtilities:
    """Test suite for ValidationUtilities class."""

    def test_validate_required_field_success(self):
        """Test successful validation of required fields."""
        # Valid values should not raise
        ValidationUtilities.validate_required_field("test", "field")
        ValidationUtilities.validate_required_field(42, "field")
        ValidationUtilities.validate_required_field([1, 2, 3], "field")
        ValidationUtilities.validate_required_field({"key": "value"}, "field")
        ValidationUtilities.validate_required_field({1, 2, 3}, "field")

    def test_validate_required_field_failures(self):
        """Test validation failures for required fields."""
        # None should raise
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_required_field(None, "test_field")
        assert "Required field 'test_field' is missing" in str(exc_info.value)
        assert exc_info.value.field_name == "test_field"

        # Empty string should raise
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_required_field("", "test_field")
        assert "Required field 'test_field' cannot be empty" in str(exc_info.value)

        # Whitespace-only string should raise
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_required_field("   ", "test_field")
        assert "Required field 'test_field' cannot be empty" in str(exc_info.value)

        # Empty list should raise
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_required_field([], "test_field")
        assert "Required field 'test_field' cannot be empty" in str(exc_info.value)

        # Empty dict should raise
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_required_field({}, "test_field")
        assert "Required field 'test_field' cannot be empty" in str(exc_info.value)

        # Empty set should raise
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_required_field(set(), "test_field")
        assert "Required field 'test_field' cannot be empty" in str(exc_info.value)

    def test_validate_required_field_with_context(self):
        """Test validation with context information."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_required_field(None, "test_field", "LLM configuration")
        assert "Required field 'test_field' is missing in LLM configuration" in str(exc_info.value)

    def test_validate_type_success(self):
        """Test successful type validation."""
        # Valid types should return the value
        assert ValidationUtilities.validate_type("test", str, "field") == "test"
        assert ValidationUtilities.validate_type(42, int, "field") == 42
        assert ValidationUtilities.validate_type(3.14, float, "field") == 3.14
        assert ValidationUtilities.validate_type([1, 2, 3], list, "field") == [1, 2, 3]
        assert ValidationUtilities.validate_type({"key": "value"}, dict, "field") == {"key": "value"}

        # None should be allowed for any type
        assert ValidationUtilities.validate_type(None, str, "field") is None
        assert ValidationUtilities.validate_type(None, int, "field") is None

    def test_validate_type_failures(self):
        """Test type validation failures."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_type("test", int, "test_field")
        assert "Field 'test_field' must be of type int, got str" in str(exc_info.value)
        assert exc_info.value.field_name == "test_field"
        assert exc_info.value.value == "test"

        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_type(42, str, "test_field", "config validation")
        assert "Field 'test_field' must be of type str, got int in config validation" in str(exc_info.value)

    def test_validate_enum_success(self):
        """Test successful enum validation."""
        # Valid values should return the value
        assert ValidationUtilities.validate_enum("option1", ["option1", "option2"], "field") == "option1"
        assert ValidationUtilities.validate_enum(42, [42, 43, 44], "field") == 42
        assert ValidationUtilities.validate_enum(None, ["option1", "option2"], "field") is None

    def test_validate_enum_failures(self):
        """Test enum validation failures."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_enum("invalid", ["option1", "option2"], "test_field")
        assert "Field 'test_field' must be one of ['option1', 'option2'], got 'invalid'" in str(exc_info.value)
        assert exc_info.value.field_name == "test_field"
        assert exc_info.value.value == "invalid"

    def test_validate_numeric_range_success(self):
        """Test successful numeric range validation."""
        # Valid ranges should return the value
        assert ValidationUtilities.validate_numeric_range(5, min_val=0, max_val=10, field_name="field") == 5
        assert ValidationUtilities.validate_numeric_range(3.14, min_val=0.0, max_val=10.0, field_name="field") == 3.14
        assert ValidationUtilities.validate_numeric_range(0, min_val=0, field_name="field") == 0
        assert ValidationUtilities.validate_numeric_range(10, max_val=10, field_name="field") == 10

    def test_validate_numeric_range_failures(self):
        """Test numeric range validation failures."""
        # Non-numeric value
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_numeric_range("not_a_number", field_name="test_field")  # type: ignore
        assert "Field 'test_field' must be numeric, got str" in str(exc_info.value)

        # Below minimum
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_numeric_range(-1, min_val=0, field_name="test_field")
        assert "Field 'test_field' must be >= 0, got -1" in str(exc_info.value)

        # Above maximum
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_numeric_range(11, max_val=10, field_name="test_field")
        assert "Field 'test_field' must be <= 10, got 11" in str(exc_info.value)

    def test_validate_path_success(self):
        """Test successful path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_file = temp_path / "test.txt"
            temp_file.write_text("test content")

            # Valid existing directory
            result = ValidationUtilities.validate_path(temp_dir, must_exist=True, must_be_dir=True)
            assert result == temp_path

            # Valid existing file
            result = ValidationUtilities.validate_path(temp_file, must_exist=True, must_be_file=True)
            assert result == temp_file

            # Valid non-existing path (when must_exist=False)
            non_existing = temp_path / "non_existing.txt"
            result = ValidationUtilities.validate_path(non_existing, must_exist=False)
            assert result == non_existing

    def test_validate_path_failures(self):
        """Test path validation failures."""
        # Non-existing path when must_exist=True
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_path("/non/existing/path", must_exist=True, field_name="test_field")
        assert "Path '/non/existing/path' does not exist" in str(exc_info.value)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_file = temp_path / "test.txt"
            temp_file.write_text("test content")

            # Directory when expecting file
            with pytest.raises(ValidationError) as exc_info:
                ValidationUtilities.validate_path(temp_dir, must_exist=True, must_be_file=True, field_name="test_field")
            assert "Path" in str(exc_info.value) and "must be a file" in str(exc_info.value)

            # File when expecting directory
            with pytest.raises(ValidationError) as exc_info:
                ValidationUtilities.validate_path(temp_file, must_exist=True, must_be_dir=True, field_name="test_field")
            assert "Path" in str(exc_info.value) and "must be a directory" in str(exc_info.value)

    def test_validate_config_structure_success(self):
        """Test successful config structure validation."""
        config = {"required_key": "value", "optional_key": "value", "extra_key": "value"}

        # Valid config with required keys
        result = ValidationUtilities.validate_config_structure(
            config, required_keys=["required_key"], optional_keys=["optional_key"], allow_extra_keys=True
        )
        assert result == config

        # Valid config without extra keys
        config_no_extra = {"required_key": "value", "optional_key": "value"}
        result = ValidationUtilities.validate_config_structure(
            config_no_extra, required_keys=["required_key"], optional_keys=["optional_key"], allow_extra_keys=False
        )
        assert result == config_no_extra

    def test_validate_config_structure_failures(self):
        """Test config structure validation failures."""
        # Non-dict config
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_config_structure("not_a_dict")  # type: ignore
        assert "Configuration must be a dictionary, got str" in str(exc_info.value)

        # Missing required key
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_config_structure({"optional_key": "value"}, required_keys=["required_key"])
        assert "Required configuration key 'required_key' is missing" in str(exc_info.value)

        # Extra keys when not allowed
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_config_structure(
                {"required_key": "value", "extra_key": "value"}, required_keys=["required_key"], optional_keys=[], allow_extra_keys=False
            )
        assert "Unexpected configuration keys: ['extra_key']" in str(exc_info.value)

    @patch.dict(os.environ, {"TEST_API_KEY": "test_value"})
    def test_validate_model_availability_success(self):
        """Test successful model availability validation."""
        # Model in available list with required env vars
        assert (
            ValidationUtilities.validate_model_availability(
                "test_model", available_models=["test_model", "other_model"], required_env_vars=["TEST_API_KEY"]
            )
            is True
        )

        # Model not in list but no list provided
        assert (
            ValidationUtilities.validate_model_availability("test_model", available_models=None, required_env_vars=["TEST_API_KEY"]) is True
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_model_availability_failures(self):
        """Test model availability validation failures."""
        # Invalid model name
        with pytest.raises(ValidationError):
            ValidationUtilities.validate_model_availability(None)  # type: ignore

        with pytest.raises(ValidationError):
            ValidationUtilities.validate_model_availability("")

        # Model not in available list
        assert ValidationUtilities.validate_model_availability("unavailable_model", available_models=["test_model", "other_model"]) is False

        # Missing environment variables
        assert ValidationUtilities.validate_model_availability("test_model", required_env_vars=["MISSING_API_KEY"]) is False

    def test_validate_decay_parameters_success(self):
        """Test successful decay parameters validation."""
        # Valid parameters
        decay_rate, decay_interval = ValidationUtilities.validate_decay_parameters(0.1, 3600)
        assert decay_rate == 0.1
        assert decay_interval == 3600

        # Permanent memory (decay_rate = 0)
        decay_rate, decay_interval = ValidationUtilities.validate_decay_parameters(0.0, 3600)
        assert decay_rate == 0.0
        assert decay_interval == 3600

    def test_validate_decay_parameters_failures(self):
        """Test decay parameters validation failures."""
        # Invalid decay rate
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_decay_parameters(1.5, 3600)
        assert "decay_rate" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_decay_parameters(-0.1, 3600)
        assert "decay_rate" in str(exc_info.value)

        # Invalid decay interval
        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_decay_parameters(0.1, 0)
        assert "decay_interval" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ValidationUtilities.validate_decay_parameters(0.1, -100)
        assert "decay_interval" in str(exc_info.value)

    @patch("dana.common.utils.validation.DANA_LOGGER")
    def test_validate_decay_parameters_warnings(self, mock_logger):
        """Test decay parameters validation warnings."""
        # High decay rate with long interval should warn about being long
        ValidationUtilities.validate_decay_parameters(0.9, 3600)
        mock_logger.warning.assert_called()
        warning_message = mock_logger.warning.call_args[0][0]
        assert "seems long" in warning_message

        # Reset mock
        mock_logger.reset_mock()

        # Low decay rate with short interval should warn about being short
        ValidationUtilities.validate_decay_parameters(0.001, 1)
        mock_logger.warning.assert_called()
        warning_message = mock_logger.warning.call_args[0][0]
        assert "seems short" in warning_message


class TestValidationError:
    """Test suite for ValidationError class."""

    def test_validation_error_creation(self):
        """Test ValidationError creation with different parameters."""
        # Basic error
        error = ValidationError("Test message")
        assert str(error) == "Test message"
        assert error.field_name is None
        assert error.value is None

        # Error with field name and value
        error = ValidationError("Test message", field_name="test_field", value="test_value")
        assert str(error) == "Test message"
        assert error.field_name == "test_field"
        assert error.value == "test_value"

    def test_validation_error_inheritance(self):
        """Test that ValidationError properly inherits from DanaError."""
        error = ValidationError("Test message")
        from dana.common.exceptions import DanaError

        assert isinstance(error, DanaError)
        assert isinstance(error, Exception)
