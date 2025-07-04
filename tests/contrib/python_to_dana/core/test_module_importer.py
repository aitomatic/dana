"""
Tests for Dana Module Import Functionality

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
from unittest.mock import Mock, patch

import pytest

from dana.integrations.python import Dana, disable_dana_imports, enable_dana_imports, list_dana_modules
from dana.integrations.python.core.module_importer import (
    DanaModuleLoader,
    DanaModuleWrapper,
    install_import_hook,
    uninstall_import_hook,
)


class TestDanaModuleWrapper:
    """Test the DanaModuleWrapper class."""

    def test_wrapper_initialization(self):
        """Test wrapper initialization."""
        mock_sandbox = Mock()
        mock_context = Mock()
        mock_context.get_scope.return_value = {}

        wrapper = DanaModuleWrapper("test_module", mock_sandbox, mock_context)

        assert wrapper._module_name == "test_module"
        assert wrapper._sandbox_interface == mock_sandbox
        assert wrapper._context == mock_context
        assert wrapper._functions == {}
        assert wrapper._variables == {}

    # Table-driven test parameters for module content extraction
    extract_module_contents_params = [
        {
            "name": "functions_and_variables_extraction",
            "local_scope": {"add": Mock(__call__=True), "multiply": Mock(__call__=True), "PI": 3.14159, "_private_var": "hidden"},
            "public_scope": {"VERSION": "1.0.0", "CONFIG": {"debug": True}},
            "system_scope": {"agent_name": "test_agent", "other_system_var": "not_included"},
            "expected_functions": ["add", "multiply"],
            "expected_variables": {"PI": 3.14159, "VERSION": "1.0.0", "CONFIG": {"debug": True}, "agent_name": "test_agent"},
            "excluded_items": ["_private_var", "other_system_var"],
        },
        {
            "name": "empty_scopes",
            "local_scope": {},
            "public_scope": {},
            "system_scope": {},
            "expected_functions": [],
            "expected_variables": {},
            "excluded_items": [],
        },
        {
            "name": "only_functions",
            "local_scope": {"func1": Mock(__call__=True), "func2": Mock(__call__=True)},
            "public_scope": {},
            "system_scope": {},
            "expected_functions": ["func1", "func2"],
            "expected_variables": {},
            "excluded_items": [],
        },
        {
            "name": "only_variables",
            "local_scope": {"var1": "value1", "var2": 42},
            "public_scope": {"var3": "value3"},
            "system_scope": {"agent_description": "test description"},
            "expected_functions": [],
            "expected_variables": {"var1": "value1", "var2": 42, "var3": "value3", "agent_description": "test description"},
            "excluded_items": [],
        },
    ]

    @pytest.mark.parametrize("test_case", extract_module_contents_params, ids=lambda x: x["name"])
    def test_extract_module_contents(self, test_case):
        """Test extraction of module contents."""
        mock_sandbox = Mock()
        mock_context = Mock()

        # Mock context scopes
        mock_context.get_scope.side_effect = lambda scope: {
            "local": test_case["local_scope"],
            "public": test_case["public_scope"],
            "system": test_case["system_scope"],
        }[scope]

        wrapper = DanaModuleWrapper("test_module", mock_sandbox, mock_context)

        # Check functions extracted (callables)
        for func_name in test_case["expected_functions"]:
            assert func_name in wrapper._functions

        # Check variables extracted
        for var_name, var_value in test_case["expected_variables"].items():
            assert wrapper._variables[var_name] == var_value

        # Check excluded items
        for excluded_item in test_case["excluded_items"]:
            assert excluded_item not in wrapper._functions
            assert excluded_item not in wrapper._variables

    # Table-driven test parameters for getattr access
    getattr_access_params = [
        {
            "name": "function_access",
            "setup_type": "function",
            "attribute_name": "add",
            "attribute_value": Mock(),
            "expected_type": "callable",
            "should_have_name": True,
        },
        {
            "name": "variable_access_number",
            "setup_type": "variable",
            "attribute_name": "PI",
            "attribute_value": 3.14159,
            "expected_type": "value",
            "should_have_name": False,
        },
        {
            "name": "variable_access_string",
            "setup_type": "variable",
            "attribute_name": "VERSION",
            "attribute_value": "1.0.0",
            "expected_type": "value",
            "should_have_name": False,
        },
        {
            "name": "variable_access_dict",
            "setup_type": "variable",
            "attribute_name": "CONFIG",
            "attribute_value": {"debug": True},
            "expected_type": "value",
            "should_have_name": False,
        },
    ]

    @pytest.mark.parametrize("test_case", getattr_access_params, ids=lambda x: x["name"])
    def test_getattr_access(self, test_case):
        """Test accessing functions and variables through __getattr__."""
        mock_sandbox = Mock()
        mock_context = Mock()
        mock_context.get_scope.return_value = {}

        wrapper = DanaModuleWrapper("test_module", mock_sandbox, mock_context)

        # Setup attribute based on type
        if test_case["setup_type"] == "function":
            wrapper._functions[test_case["attribute_name"]] = test_case["attribute_value"]
        else:
            wrapper._variables[test_case["attribute_name"]] = test_case["attribute_value"]

        # Access the attribute
        result = getattr(wrapper, test_case["attribute_name"])

        # Check expected behavior
        if test_case["expected_type"] == "callable":
            assert callable(result)
            if test_case["should_have_name"]:
                assert hasattr(result, "__name__")
                assert result.__name__ == test_case["attribute_name"]
        else:
            assert result == test_case["attribute_value"]

    # Table-driven test parameters for special attributes
    special_attributes_params = [
        {"name": "module_name_attribute", "attribute_name": "__name__", "expected_value": "test_module"},
        {"name": "dana_context_attribute", "attribute_name": "__dana_context__", "expected_value": "mock_context"},
        {"name": "dana_sandbox_attribute", "attribute_name": "__dana_sandbox__", "expected_value": "mock_sandbox"},
    ]

    @pytest.mark.parametrize("test_case", special_attributes_params, ids=lambda x: x["name"])
    def test_getattr_special_attributes(self, test_case):
        """Test accessing special attributes."""
        mock_sandbox = Mock()
        mock_context = Mock()
        mock_context.get_scope.return_value = {}

        wrapper = DanaModuleWrapper("test_module", mock_sandbox, mock_context)

        result = getattr(wrapper, test_case["attribute_name"])

        if test_case["expected_value"] == "mock_context":
            assert result == mock_context
        elif test_case["expected_value"] == "mock_sandbox":
            assert result == mock_sandbox
        else:
            assert result == test_case["expected_value"]

    def test_getattr_attribute_error(self):
        """Test AttributeError for missing attributes."""
        mock_sandbox = Mock()
        mock_context = Mock()
        mock_context.get_scope.return_value = {}

        wrapper = DanaModuleWrapper("test_module", mock_sandbox, mock_context)

        with pytest.raises(AttributeError, match="has no attribute 'nonexistent'"):
            _ = wrapper.nonexistent

    def test_dir_method(self):
        """Test __dir__ method."""
        mock_sandbox = Mock()
        mock_context = Mock()
        mock_context.get_scope.return_value = {}

        wrapper = DanaModuleWrapper("test_module", mock_sandbox, mock_context)
        wrapper._functions = {"add": Mock(), "multiply": Mock()}
        wrapper._variables = {"PI": 3.14159, "VERSION": "1.0"}

        attrs = dir(wrapper)

        assert "add" in attrs
        assert "multiply" in attrs
        assert "PI" in attrs
        assert "VERSION" in attrs
        assert "__name__" in attrs
        assert "__dana_context__" in attrs
        assert "__dana_sandbox__" in attrs

    def test_repr_method(self):
        """Test __repr__ method."""
        mock_sandbox = Mock()
        mock_context = Mock()
        mock_context.get_scope.return_value = {}

        wrapper = DanaModuleWrapper("test_module", mock_sandbox, mock_context)
        wrapper._functions = {"add": Mock()}
        wrapper._variables = {"PI": 3.14159}

        repr_str = repr(wrapper)

        assert "test_module" in repr_str
        assert "1 functions" in repr_str
        assert "1 variables" in repr_str


class TestDanaModuleLoader:
    """Test the DanaModuleLoader class."""

    # Table-driven test parameters for loader initialization
    loader_init_params = [
        {
            "name": "default_initialization",
            "search_paths": None,
            "debug": False,
            "expected_paths_length": 2,  # Default includes current dir and ./dana
            "expected_debug": False,
        },
        {
            "name": "with_search_paths",
            "search_paths": ["/test/path1", "/test/path2"],
            "debug": True,
            "expected_paths_length": 2,
            "expected_debug": True,
        },
        {
            "name": "single_search_path",
            "search_paths": ["/single/path"],
            "debug": False,
            "expected_paths_length": 1,
            "expected_debug": False,
        },
    ]

    @pytest.mark.parametrize("test_case", loader_init_params, ids=lambda x: x["name"])
    def test_loader_initialization(self, test_case):
        """Test loader initialization."""
        mock_sandbox = Mock()

        with patch("dana.contrib.python_to_dana.core.module_importer.initialize_module_system"):
            loader = DanaModuleLoader(test_case["search_paths"], mock_sandbox, debug=test_case["debug"])

            assert len(loader.search_paths) == test_case["expected_paths_length"]
            assert loader._debug is test_case["expected_debug"]
            assert loader._loaded_modules == {}

    def test_find_spec_existing_module(self):
        """Test find_spec returns None for existing modules."""
        with patch("dana.contrib.python_to_dana.core.module_importer.initialize_module_system"):
            loader = DanaModuleLoader()

        # Test with a module that's already in sys.modules
        with patch.dict(sys.modules, {"existing_module": Mock()}):
            spec = loader.find_spec("existing_module")
            assert spec is None

    # Table-driven test parameters for standard library modules
    standard_library_params = [
        {"name": "os_module", "module_name": "os", "expected_result": True},
        {"name": "sys_module", "module_name": "sys", "expected_result": True},
        {"name": "sys_submodule", "module_name": "sys.path", "expected_result": True},
        {"name": "dana_module", "module_name": "dana.core", "expected_result": True},
        {"name": "private_module", "module_name": "_private_module", "expected_result": True},
        {"name": "custom_module", "module_name": "simple_math", "expected_result": False},
        {"name": "another_custom_module", "module_name": "custom_module", "expected_result": False},
    ]

    @pytest.mark.parametrize("test_case", standard_library_params, ids=lambda x: x["name"])
    def test_find_spec_standard_library(self, test_case):
        """Test find_spec returns None for standard library modules."""
        with patch("dana.contrib.python_to_dana.core.module_importer.initialize_module_system"):
            loader = DanaModuleLoader()

        if test_case["expected_result"]:
            spec = loader.find_spec(test_case["module_name"])
            assert spec is None
        else:
            # For non-standard library modules, we expect the method to not return None immediately
            # (though it might return None for other reasons like file not found)
            pass  # This test case is handled by the is_standard_library_module test

    @pytest.mark.parametrize("test_case", standard_library_params, ids=lambda x: x["name"])
    def test_is_standard_library_module(self, test_case):
        """Test standard library module detection."""
        with patch("dana.contrib.python_to_dana.core.module_importer.initialize_module_system"):
            loader = DanaModuleLoader()

        result = loader._is_standard_library_module(test_case["module_name"])
        assert result == test_case["expected_result"]


class TestDanaClassImportFeatures:
    """Test the Dana class import features."""

    # Table-driven test parameters for Dana initialization
    dana_init_params = [
        {"name": "init_with_imports_enabled", "enable_imports": True, "expected_imports_enabled": True, "should_call_install": True},
        {"name": "init_with_imports_disabled", "enable_imports": False, "expected_imports_enabled": False, "should_call_install": False},
    ]

    @pytest.mark.parametrize("test_case", dana_init_params, ids=lambda x: x["name"])
    def test_dana_init_with_imports(self, test_case):
        """Test Dana initialization with enable_imports parameter."""
        with patch("dana.contrib.python_to_dana.dana_module.install_import_hook") as mock_install:
            dana = Dana(enable_imports=test_case["enable_imports"])

            assert dana._imports_enabled is test_case["expected_imports_enabled"]
            if test_case["should_call_install"]:
                mock_install.assert_called_once()
            else:
                mock_install.assert_not_called()

    def test_enable_module_imports(self):
        """Test enabling module imports."""
        dana = Dana()

        with patch("dana.contrib.python_to_dana.dana_module.install_import_hook") as mock_install:
            dana.enable_module_imports()

            assert dana._imports_enabled is True
            mock_install.assert_called_once_with(search_paths=None, sandbox_interface=dana._sandbox_interface, debug=dana._debug)

    def test_disable_module_imports(self):
        """Test disabling module imports."""
        dana = Dana()
        dana._imports_enabled = True

        with patch("dana.contrib.python_to_dana.dana_module.uninstall_import_hook") as mock_uninstall:
            dana.disable_module_imports()

            assert dana._imports_enabled is False
            mock_uninstall.assert_called_once()

    def test_list_modules(self):
        """Test listing available modules."""
        dana = Dana()

        with patch("dana.contrib.python_to_dana.dana_module.list_available_modules") as mock_list:
            mock_list.return_value = ["simple_math", "text_utils"]

            modules = dana.list_modules()

            assert modules == ["simple_math", "text_utils"]
            mock_list.assert_called_once_with(None)

    # Table-driven test parameters for imports_enabled property
    imports_enabled_params = [
        {"name": "imports_disabled", "imports_enabled": False, "expected_result": False},
        {"name": "imports_enabled", "imports_enabled": True, "expected_result": True},
    ]

    @pytest.mark.parametrize("test_case", imports_enabled_params, ids=lambda x: x["name"])
    def test_imports_enabled_property(self, test_case):
        """Test imports_enabled property."""
        dana = Dana()
        dana._imports_enabled = test_case["imports_enabled"]

        assert dana.imports_enabled is test_case["expected_result"]

    def test_close_with_imports_enabled(self):
        """Test close method disables imports."""
        dana = Dana()
        dana._imports_enabled = True

        with patch.object(dana, "disable_module_imports") as mock_disable:
            dana.close()
            mock_disable.assert_called_once()

    # Table-driven test parameters for repr method
    repr_params = [
        {"name": "repr_with_imports_disabled", "imports_enabled": False, "expected_substring": "imports-disabled"},
        {"name": "repr_with_imports_enabled", "imports_enabled": True, "expected_substring": "imports-enabled"},
    ]

    @pytest.mark.parametrize("test_case", repr_params, ids=lambda x: x["name"])
    def test_repr_with_imports(self, test_case):
        """Test __repr__ includes import status."""
        dana = Dana()
        dana._imports_enabled = test_case["imports_enabled"]

        repr_str = repr(dana)
        assert test_case["expected_substring"] in repr_str


class TestConvenienceFunctions:
    """Test convenience functions."""

    # Table-driven test parameters for convenience functions
    convenience_functions_params = [
        {
            "name": "enable_dana_imports_with_paths",
            "function_name": "enable_dana_imports",
            "function_args": [["/test/path"]],
            "mock_method": "enable_module_imports",
            "expected_call_args": [["/test/path"]],
        },
        {
            "name": "enable_dana_imports_no_paths",
            "function_name": "enable_dana_imports",
            "function_args": [None],
            "mock_method": "enable_module_imports",
            "expected_call_args": [None],
        },
        {
            "name": "disable_dana_imports",
            "function_name": "disable_dana_imports",
            "function_args": [],
            "mock_method": "disable_module_imports",
            "expected_call_args": [],
        },
    ]

    @pytest.mark.parametrize("test_case", convenience_functions_params, ids=lambda x: x["name"])
    def test_convenience_functions(self, test_case):
        """Test convenience functions for Dana imports."""
        from dana.integrations.python import dana

        with patch.object(dana, test_case["mock_method"]) as mock_method:
            # Get the function from the module
            if test_case["function_name"] == "enable_dana_imports":
                if test_case["function_args"]:
                    enable_dana_imports(*test_case["function_args"])
                else:
                    enable_dana_imports()
            elif test_case["function_name"] == "disable_dana_imports":
                disable_dana_imports()

            # Verify the call
            if test_case["expected_call_args"]:
                mock_method.assert_called_once_with(*test_case["expected_call_args"])
            else:
                mock_method.assert_called_once()

    def test_list_dana_modules(self):
        """Test list_dana_modules convenience function."""
        from dana.integrations.python import dana

        with patch.object(dana, "list_modules") as mock_list:
            mock_list.return_value = ["module1", "module2"]

            modules = list_dana_modules(["/test/path"])

            assert modules == ["module1", "module2"]
            mock_list.assert_called_once_with(["/test/path"])


class TestImportHookFunctions:
    """Test import hook utility functions."""

    def test_install_uninstall_import_hook(self):
        """Test installing and uninstalling import hook."""
        with patch("sys.meta_path", []) as mock_meta_path:
            # Install hook
            install_import_hook(debug=True)

            # Should add to sys.meta_path
            assert len(mock_meta_path) == 1

            # Uninstall hook
            uninstall_import_hook()

            # Should remove from sys.meta_path
            assert len(mock_meta_path) == 0


@pytest.fixture
def temp_dana_module(tmp_path):
    """Create a temporary Dana module for testing."""
    module_content = """
def add(x: int, y: int) -> int:
    return x + y

def greet(name: str) -> str:
    return f"Hello, {name}!"

PI: float = 3.14159
"""

    module_file = tmp_path / "test_math.na"
    module_file.write_text(module_content)

    return str(tmp_path), "test_math"


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    def test_full_import_workflow(self, temp_dana_module):
        """Test complete import workflow with temporary module."""
        search_path, module_name = temp_dana_module

        dana = Dana(debug=True)

        try:
            # Enable imports with custom search path
            dana.enable_module_imports([search_path])

            # Check module is listed
            modules = dana.list_modules([search_path])
            assert module_name in modules

            # Test that imports are enabled
            assert dana.imports_enabled is True

        finally:
            # Clean up
            dana.close()
            assert dana.imports_enabled is False
