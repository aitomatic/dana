"""
Tests for the main package initialization and imports.
"""

from unittest.mock import patch

import pytest

# Table-driven test parameters for core component imports
core_import_params = [
    {
        "name": "sandbox_interface",
        "import_name": "SandboxInterface",
        "expected_not_none": True,
    },
    {
        "name": "inprocess_sandbox_interface", 
        "import_name": "InProcessSandboxInterface",
        "expected_not_none": True,
    },
    {
        "name": "subprocess_sandbox_interface",
        "import_name": "SubprocessSandboxInterface", 
        "expected_not_none": True,
    },
    {
        "name": "dana_type",
        "import_name": "DanaType",
        "expected_not_none": True,
    },
    {
        "name": "type_converter",
        "import_name": "TypeConverter",
        "expected_not_none": True,
    },
    {
        "name": "dana_call_error",
        "import_name": "DanaCallError",
        "expected_not_none": True,
    },
]

# Table-driven test parameters for dana instance methods
dana_method_params = [
    {
        "name": "reason_method",
        "method_name": "reason",
        "should_be_callable": True,
    },
    {
        "name": "close_method", 
        "method_name": "close",
        "should_be_callable": True,
    },
]

# Table-driven test parameters for dana instance properties
dana_property_params = [
    {
        "name": "debug_property",
        "property_name": "debug",
        "should_exist": True,
    },
    {
        "name": "sandbox_property",
        "property_name": "sandbox", 
        "should_exist": True,
    },
]

# Table-driven test parameters for stable API components
stable_api_params = [
    {
        "name": "main_dana_instance",
        "import_path": "opendxa.contrib.python_to_dana",
        "component_name": "dana",
        "expected_not_none": True,
    },
    {
        "name": "dana_call_error",
        "import_path": "opendxa.contrib.python_to_dana.core",
        "component_name": "DanaCallError", 
        "expected_not_none": True,
    },
    {
        "name": "dana_class",
        "import_path": "opendxa.contrib.python_to_dana.dana_module",
        "component_name": "Dana",
        "expected_not_none": True,
    },
]


class TestPackageImports:
    """Test that the package can be imported correctly."""
    
    def test_main_import(self):
        """Test that the main package can be imported."""
        from opendxa.contrib.python_to_dana import dana
        assert dana is not None
    
    @pytest.mark.parametrize("test_case", core_import_params, ids=lambda x: x["name"])
    def test_core_imports(self, test_case):
        """Test that core components can be imported."""
        from opendxa.contrib.python_to_dana.core import (
            DanaCallError,
            DanaType,
            InProcessSandboxInterface,
            SandboxInterface,
            SubprocessSandboxInterface,
            TypeConverter,
        )
        
        # Create a lookup dict for imported components
        imports = {
            "SandboxInterface": SandboxInterface,
            "InProcessSandboxInterface": InProcessSandboxInterface,
            "SubprocessSandboxInterface": SubprocessSandboxInterface,
            "DanaType": DanaType,
            "TypeConverter": TypeConverter,
            "DanaCallError": DanaCallError,
        }
        
        # Get the imported component by name
        component = imports[test_case["import_name"]]
        
        # Assert
        if test_case["expected_not_none"]:
            assert component is not None
    
    def test_gateway_imports(self):
        """Test that gateway components can be imported."""
        from opendxa.contrib.python_to_dana.dana_module import Dana
        assert Dana is not None
    
    def test_utils_imports(self):
        """Test that utils can be imported."""
        from opendxa.contrib.python_to_dana.utils import BasicTypeConverter
        assert BasicTypeConverter is not None


class TestMainDanaInstance:
    """Test the main dana instance and its functionality."""
    
    def test_dana_instance_exists(self):
        """Test that the main dana instance exists."""
        from opendxa.contrib.python_to_dana import dana
        assert dana is not None
        assert hasattr(dana, 'reason')
    
    def test_dana_instance_type(self):
        """Test that dana instance is of correct type."""
        from opendxa.contrib.python_to_dana import dana
        from opendxa.contrib.python_to_dana.dana_module import Dana
        
        assert isinstance(dana, Dana)
    
    @pytest.mark.parametrize("test_case", dana_method_params, ids=lambda x: x["name"])
    def test_dana_instance_methods(self, test_case):
        """Test that dana instance has expected methods."""
        from opendxa.contrib.python_to_dana import dana
        
        # Act
        method = getattr(dana, test_case["method_name"], None)
        
        # Assert
        assert hasattr(dana, test_case["method_name"])
        if test_case["should_be_callable"]:
            assert callable(method)
    
    @pytest.mark.parametrize("test_case", dana_property_params, ids=lambda x: x["name"])
    def test_dana_instance_properties(self, test_case):
        """Test that dana instance has expected properties."""
        from opendxa.contrib.python_to_dana import dana
        
        # Act & Assert
        if test_case["should_exist"]:
            assert hasattr(dana, test_case["property_name"])


class TestInitializationOrder:
    """Test that components initialize in the correct order."""
    
    def test_dana_imports_without_errors(self):
        """Test that dana can be imported without circular import errors."""
        # This should not raise any exceptions
        from opendxa.contrib.python_to_dana import dana
        assert dana is not None
    
    def test_core_before_gateway(self):
        """Test that core components can be imported before gateway."""
        from opendxa.contrib.python_to_dana.core import SandboxInterface
        from opendxa.contrib.python_to_dana.dana_module import Dana
        
        # Both should work
        assert SandboxInterface is not None
        assert Dana is not None


class TestDefaultDanaConfiguration:
    """Test the default configuration of the dana instance."""
    
    @patch('opendxa.contrib.python_to_dana.dana_module.InProcessSandboxInterface')
    def test_default_dana_is_not_debug_mode(self, mock_sandbox_class):
        """Test that default dana instance is not in debug mode."""
        # Import after patching to ensure clean state
        from opendxa.contrib.python_to_dana import dana
        
        # Should not be in debug mode by default
        assert dana.debug is False
    
    def test_default_dana_uses_inprocess_sandbox(self):
        """Test that default dana uses in-process sandbox."""
        from opendxa.contrib.python_to_dana import dana
        from opendxa.contrib.python_to_dana.core.inprocess_sandbox import InProcessSandboxInterface
        
        # Verify that the dana instance uses InProcessSandboxInterface
        assert isinstance(dana._sandbox_interface, InProcessSandboxInterface)


class TestPackageStructure:
    """Test that the package structure is correct."""
    
    def test_all_exports_defined(self):
        """Test that __all__ is properly defined in submodules."""
        from opendxa.contrib.python_to_dana import core
        
        # Core should have __all__ defined
        assert hasattr(core, '__all__')
        assert isinstance(core.__all__, list)
        assert len(core.__all__) > 0
    
    def test_no_internal_imports_in_all(self):
        """Test that __all__ doesn't export internal implementation details."""
        from opendxa.contrib.python_to_dana import core
        
        # Should not export private/internal items
        private_items = [item for item in core.__all__ if item.startswith('_')]
        assert len(private_items) == 0


class TestExampleCompatibility:
    """Test that examples work with the package structure."""
    
    def test_simple_usage_pattern(self):
        """Test that simple usage pattern works."""
        # This is the pattern shown in examples
        from opendxa.contrib.python_to_dana import dana
        
        # Should be able to access dana instance
        assert dana is not None
        assert hasattr(dana, 'reason')
    
    def test_advanced_usage_pattern(self):
        """Test that advanced usage pattern works."""
        # Advanced pattern for custom configuration
        from opendxa.contrib.python_to_dana.dana_module import Dana
        
        # Should be able to create custom instances
        assert Dana is not None
        
        # Should work with debug mode
        custom_dana = Dana(debug=True)
        assert custom_dana.debug is True
    
    def test_core_access_pattern(self):
        """Test that direct core access pattern works."""
        # For advanced users who want direct core access
        from opendxa.contrib.python_to_dana.core import InProcessSandboxInterface
        
        # Should be able to create sandbox directly
        sandbox = InProcessSandboxInterface(debug=False)
        assert sandbox is not None
        assert hasattr(sandbox, 'reason')


class TestBackwardCompatibility:
    """Test backward compatibility considerations."""
    
    @pytest.mark.parametrize("test_case", stable_api_params, ids=lambda x: x["name"])
    def test_module_structure_stable(self, test_case):
        """Test that the module structure is stable."""
        # Import the module dynamically
        import importlib
        module = importlib.import_module(test_case["import_path"])
        
        # Get the component
        component = getattr(module, test_case["component_name"])
        
        # Assert
        if test_case["expected_not_none"]:
            assert component is not None
    
    def test_main_api_stable(self):
        """Test that the main API remains stable."""
        from opendxa.contrib.python_to_dana import dana
        
        # Core API should remain stable
        assert hasattr(dana, 'reason')
        assert callable(dana.reason)
        
        # Properties should be stable
        assert hasattr(dana, 'debug')
        assert hasattr(dana, 'sandbox') 