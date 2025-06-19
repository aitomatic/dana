"""
Tests for gateway.dana_module - Main Dana Module Implementation
"""

from unittest.mock import Mock, patch

import pytest

from opendxa.contrib.python_to_dana.core.exceptions import DanaCallError
from opendxa.contrib.python_to_dana.dana_module import Dana

# Test parameters for various Dana module initialization scenarios
dana_init_params = [
    {"debug": False, "expected_debug": False},
    {"debug": True, "expected_debug": True},
]


@pytest.mark.parametrize("params", dana_init_params)
def test_dana_initialization(params):
    """Test Dana module initialization with different parameters."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(debug=params["debug"])
        assert dana.debug == params["expected_debug"]


def test_dana_reason_basic_functionality():
    """Test basic Dana reasoning functionality."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(debug=True)

        # Mock the sandbox interface response
        mock_response = "The answer is 4"
        dana._sandbox_interface.reason = Mock(return_value=mock_response)

        result = dana.reason("What is 2+2?")
        assert result == mock_response


# Test data for type validation
type_validation_test_data = [
    {
        "name": "valid_string_prompt",
        "prompt": "What is the weather?",
        "options": None,
        "should_pass": True,
        "expected_error": None,
    },
    {
        "name": "valid_string_prompt_with_options",
        "prompt": "Analyze this text",
        "options": {"temperature": 0.5},
        "should_pass": True,
        "expected_error": None,
    },
    {
        "name": "invalid_prompt_type_int",
        "prompt": 123,
        "options": None,
        "should_pass": False,
        "expected_error": TypeError,
    },
    {
        "name": "invalid_prompt_type_list",
        "prompt": ["hello", "world"],
        "options": None,
        "should_pass": False,
        "expected_error": TypeError,
    },
    {
        "name": "invalid_options_type_string",
        "prompt": "Hello",
        "options": "invalid options",
        "should_pass": False,
        "expected_error": TypeError,
    },
    {
        "name": "invalid_options_type_int",
        "prompt": "Hello",
        "options": 42,
        "should_pass": False,
        "expected_error": TypeError,
    },
]


@pytest.fixture
def mock_sandbox_interface():
    """Create a mock sandbox interface for testing."""
    mock = Mock()
    mock.reason = Mock(return_value="Mocked response")
    mock.close = Mock()
    return mock


@pytest.mark.parametrize("test_data", type_validation_test_data, ids=lambda x: x["name"])
def test_dana_reason_type_validation(test_data):
    """Test type validation in Dana.reason() method."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface") as mock_interface_class:
        mock_interface = Mock()
        mock_interface.reason.return_value = "Valid response"
        mock_interface_class.return_value = mock_interface

        dana = Dana(debug=False)

        if test_data["should_pass"]:
            # Should not raise an exception
            result = dana.reason(test_data["prompt"], test_data["options"])
            assert result == "Valid response"
        else:
            # Should raise the expected exception
            with pytest.raises(test_data["expected_error"]):
                dana.reason(test_data["prompt"], test_data["options"])


def test_dana_call_count_tracking():
    """Test that Dana tracks call count correctly."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(debug=True)

        # Initial call count should be 0
        assert dana._call_count == 0

        # Mock sandbox interface
        dana._sandbox_interface.reason = Mock(return_value="Response 1")

        # Make some calls
        dana.reason("Question 1")
        assert dana._call_count == 1

        dana.reason("Question 2")
        assert dana._call_count == 2

        dana.reason("Question 3", {"temperature": 0.5})
        assert dana._call_count == 3


def test_dana_error_handling():
    """Test Dana error handling for various scenarios."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(debug=True)

        # Test DanaCallError propagation
        dana._sandbox_interface.reason = Mock(side_effect=DanaCallError("Dana failed"))

        with pytest.raises(DanaCallError, match="Dana failed"):
            dana.reason("Test question")

        # Test unexpected error wrapping
        dana._sandbox_interface.reason = Mock(side_effect=RuntimeError("Unexpected error"))

        with pytest.raises(DanaCallError, match="Unexpected error in reasoning"):
            dana.reason("Test question")


def test_dana_properties():
    """Test Dana properties and accessors."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(debug=True)

        # Test debug property
        assert dana.debug is True

        # Test sandbox property
        assert dana.sandbox is not None
        assert dana.sandbox == dana._sandbox_interface


def test_dana_close_functionality():
    """Test Dana close functionality."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(debug=False)

        # Mock the close method
        dana._sandbox_interface.close = Mock()

        # Call close
        dana.close()

        # Verify close was called on sandbox interface
        dana._sandbox_interface.close.assert_called_once()


def test_dana_repr():
    """Test Dana string representation."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        # Test normal mode
        dana_normal = Dana(debug=False)
        repr_str = repr(dana_normal)
        assert "Dana(" in repr_str
        assert "mode=normal" in repr_str
        assert "calls=0" in repr_str

        # Test debug mode
        dana_debug = Dana(debug=True)
        repr_str_debug = repr(dana_debug)
        assert "mode=debug" in repr_str_debug


def test_dana_debug_output(capsys):
    """Test debug output functionality."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(debug=True)

        # Mock sandbox response
        dana._sandbox_interface.reason = Mock(return_value="Debug test response")

        # Make a call
        dana.reason("Debug test question")

        # Check debug output
        captured = capsys.readouterr()
        assert "DEBUG:" in captured.out
        assert "Dana call #1" in captured.out


# Test parameters for sandbox interface delegation
interface_delegation_tests = [
    {
        "name": "reason_delegates_correctly",
        "method": "reason",
        "args": ("Test prompt",),
        "kwargs": {"options": {"temperature": 0.5}},
        "expected_call_args": ("Test prompt", {"temperature": 0.5}),
    },
    {
        "name": "reason_with_none_options",
        "method": "reason",
        "args": ("Test prompt",),
        "kwargs": {"options": None},
        "expected_call_args": ("Test prompt", None),
    },
]


@pytest.mark.parametrize("test_case", interface_delegation_tests, ids=lambda x: x["name"])
def test_sandbox_interface_delegation(test_case):
    """Test that Dana properly delegates to sandbox interface."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface") as mock_interface_class:
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface

        # Set up mock return value
        mock_interface.reason.return_value = "Delegated response"

        dana = Dana(debug=False)

        # Call the method
        method = getattr(dana, test_case["method"])
        result = method(*test_case["args"], **test_case["kwargs"])

        # Verify delegation
        sandbox_method = getattr(mock_interface, test_case["method"])
        sandbox_method.assert_called_once_with(*test_case["expected_call_args"])
        assert result == "Delegated response"


def test_dana_context_manager():
    """Test Dana can be used as a context manager."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        mock_close = Mock()

        with patch.object(Dana, "close", mock_close):
            with Dana(debug=False) as dana:
                assert isinstance(dana, Dana)

            # Should call close when exiting context
            mock_close.assert_called_once()


# Process isolation tests
def test_dana_subprocess_isolation_placeholder():
    """Test subprocess isolation placeholder functionality."""
    with (
        patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface") as mock_inprocess,
        patch("opendxa.contrib.python_to_dana.dana_module.SubprocessSandboxInterface") as mock_subprocess,
    ):
        # Test that subprocess isolation is requested but falls back
        dana = Dana(use_subprocess_isolation=True, debug=True)

        # Should use in-process due to placeholder
        mock_inprocess.assert_called_once()
        mock_subprocess.assert_not_called()


def test_dana_subprocess_properties():
    """Test subprocess-related properties."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(use_subprocess_isolation=True, debug=True)

        # Should indicate subprocess isolation is not actually enabled
        assert dana.is_subprocess_isolated is False

        # Should have restart method
        assert hasattr(dana, "restart_subprocess")


def test_dana_subprocess_restart():
    """Test subprocess restart functionality."""
    with patch("opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface", return_value=mock_sandbox_interface):
        dana = Dana(debug=True)

        # Should handle restart gracefully even for in-process
        dana.restart_subprocess()  # Should not raise an error
