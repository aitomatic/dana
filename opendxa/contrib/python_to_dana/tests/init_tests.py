"""
Tests for __init__.py module - Main entry point for Python-to-Dana Integration
"""

from unittest.mock import Mock, patch

import pytest

import opendxa.contrib.python_to_dana
from opendxa.contrib.python_to_dana import dana
from opendxa.contrib.python_to_dana.gateway.dana_module import Dana


def test_module_imports():
    """Test that all expected imports are available."""
    # Test that dana is imported
    assert hasattr(opendxa.contrib.python_to_dana, 'dana')
    
    # Test that dana is an instance of Dana class
    assert isinstance(opendxa.contrib.python_to_dana.dana, Dana)


def test_dana_singleton_instance():
    """Test that dana is a singleton instance."""
    # Import dana multiple times and verify it's the same instance
    from opendxa.contrib.python_to_dana import dana as dana1
    from opendxa.contrib.python_to_dana import dana as dana2
    
    assert dana1 is dana2
    assert dana1 is dana


def test_dana_instance_properties():
    """Test properties of the dana instance."""
    # Test that dana instance has expected properties
    assert hasattr(dana, 'reason')
    assert hasattr(dana, 'debug')
    assert hasattr(dana, 'sandbox')
    
    # Test that reason is callable
    assert callable(dana.reason)


def test_all_exports():
    """Test that __all__ contains expected exports."""
    assert hasattr(opendxa.contrib.python_to_dana, '__all__')
    assert opendxa.contrib.python_to_dana.__all__ == ["dana"]


def test_module_docstring():
    """Test that module has proper docstring."""
    module_doc = opendxa.contrib.python_to_dana.__doc__
    assert module_doc is not None
    assert "Python-to-Dana Integration" in module_doc
    assert "OpenDXA Framework" in module_doc


def test_dana_instance_initialization():
    """Test that dana instance is properly initialized."""
    # Test that dana is not in debug mode by default
    assert dana.debug is False
    
    # Test initial call count
    assert dana._call_count == 0


# Test parameters for dana module functionality  
dana_functionality_params = [
    {
        "name": "has_reason_method",
        "attribute": "reason",
        "expected_type": "method",
    },
    {
        "name": "has_debug_property",
        "attribute": "debug",
        "expected_type": "property",
    },
    {
        "name": "has_sandbox_property", 
        "attribute": "sandbox",
        "expected_type": "property",
    },
]


@pytest.mark.parametrize("test_case", dana_functionality_params, ids=lambda x: x["name"])
def test_dana_has_expected_attributes(test_case):
    """Test that dana instance has expected attributes."""
    # Act
    has_attribute = hasattr(dana, test_case["attribute"])
    
    # Assert
    assert has_attribute, f"dana should have {test_case['attribute']} attribute"
    
    # Get the attribute
    attr = getattr(dana, test_case["attribute"])
    
    # Basic type checking
    if test_case["expected_type"] == "method":
        assert callable(attr)
    elif test_case["expected_type"] == "property":
        # For properties, just check they're accessible
        assert attr is not None


def test_dana_reason_method_signature():
    """Test that dana.reason has the expected signature."""
    import inspect
    
    # Get the reason method signature
    sig = inspect.signature(dana.reason)
    
    # Check parameters
    params = list(sig.parameters.keys())
    assert "prompt" in params
    assert "options" in params
    
    # Check that options has a default value
    options_param = sig.parameters["options"]
    assert options_param.default is None


@patch('opendxa.contrib.python_to_dana.gateway.dana_module.DefaultSandboxInterface')
def test_dana_instance_creation_process(mock_interface_class):
    """Test the dana instance creation process."""
    # This test verifies the initialization happens as expected
    mock_interface = Mock()
    mock_interface_class.return_value = mock_interface
    
    # Re-import to trigger initialization
    import importlib
    module = importlib.reload(opendxa.contrib.python_to_dana)
    
    # Verify that DefaultSandboxInterface was called during module import
    mock_interface_class.assert_called_once_with(debug=False)
    
    # Verify the dana instance is properly created
    assert isinstance(module.dana, Dana)


def test_module_attributes():
    """Test module-level attributes."""
    # Test that module has expected attributes
    assert hasattr(opendxa.contrib.python_to_dana, 'Dana')
    assert opendxa.contrib.python_to_dana.Dana is Dana


def test_dana_is_usable_immediately():
    """Test that dana can be used immediately after import."""
    # This is an integration test to ensure the setup works
    with patch.object(dana._sandbox_interface, 'reason', return_value="test result") as mock_reason:
        # Act
        result = dana.reason("test prompt")
        
        # Assert
        assert result == "test result"
        mock_reason.assert_called_once_with("test prompt", None)


def test_import_star_behavior():
    """Test that importing * only imports what's in __all__."""
    # Use a separate namespace for the test
    test_namespace = {}
    
    # Import everything into test namespace
    exec("from opendxa.contrib.python_to_dana import *", test_namespace)
    
    # Check what was imported (excluding built-ins)
    imported_names = {name for name in test_namespace.keys() if not name.startswith('__')}
    expected_names = {"dana"}  # Only what's in __all__
    
    assert imported_names == expected_names
    
    # Verify dana is available and functional
    assert 'dana' in test_namespace
    assert isinstance(test_namespace['dana'], Dana)


def test_dana_repr_string():
    """Test that dana has a proper string representation."""
    repr_str = repr(dana)
    assert "Dana" in repr_str
    assert "mode=" in repr_str
    assert "calls=" in repr_str


def test_multiple_imports_same_instance():
    """Test that multiple import patterns return the same dana instance."""
    # Different import patterns should all give the same instance
    import opendxa.contrib.python_to_dana
    from opendxa.contrib.python_to_dana import dana as dana_import1
    dana_import2 = opendxa.contrib.python_to_dana.dana
    
    # All should be the same instance (same type and attributes)
    assert type(dana_import1) is type(dana)
    assert type(dana_import2) is type(dana)
    assert dana_import1 is dana_import2
    
    # Check that they have the same sandbox interface
    assert dana_import1._sandbox_interface is dana_import2._sandbox_interface


def test_module_constants():
    """Test module-level constants and metadata."""
    # Test that important metadata is available
    module = opendxa.contrib.python_to_dana
    
    # Check docstring contains key information
    assert module.__doc__ is not None
    assert "MIT License" in module.__doc__
    assert "Aitomatic" in module.__doc__
    assert "OpenDXA" in module.__doc__ 