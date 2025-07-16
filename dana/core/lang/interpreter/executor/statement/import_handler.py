"""
Optimized import handler for Dana statements.

This module provides high-performance import processing with
optimizations for module resolution, caching, and namespace management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import ImportFromStatement, ImportStatement
from dana.core.lang.sandbox_context import SandboxContext


class ModuleNamespace:
    """Optimized namespace class for holding submodules."""

    def __init__(self, name: str):
        self.__name__ = name
        self.__dict__.update({"__name__": name})

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "__name__":
            object.__setattr__(self, name, value)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name: str) -> Any:
        if name in self.__dict__:
            return self.__dict__[name]
        raise AttributeError(f"Module namespace '{self.__name__}' has no attribute '{name}'")


class ImportHandler(Loggable):
    """Optimized import handler for Dana statements."""

    # Performance constants
    MODULE_CACHE_SIZE = 150  # Cache for loaded modules
    NAMESPACE_CACHE_SIZE = 100  # Cache for created namespaces
    IMPORT_TRACE_THRESHOLD = 50  # Number of imports before tracing

    def __init__(self, parent_executor: Any = None, function_registry: Any = None):
        """Initialize the import handler."""
        super().__init__()
        self.parent_executor = parent_executor
        self.function_registry = function_registry
        self._module_cache = {}
        self._namespace_cache = {}
        self._import_count = 0
        self._module_loader_initialized = False

    def execute_import_statement(self, node: ImportStatement, context: SandboxContext) -> Any:
        """Execute an import statement with optimized processing.

        Args:
            node: The import statement to execute
            context: The execution context

        Returns:
            None (import statements don't return values)
        """
        self._import_count += 1
        module_name = node.module

        # For context naming: use alias if provided, otherwise use clean module name
        if node.alias:
            context_name = node.alias
        else:
            # Strip .py extension for context naming if present
            context_name = module_name[:-3] if module_name.endswith(".py") else module_name

        try:
            self._trace_import("import", module_name, context_name)

            if module_name.endswith(".py"):
                # Explicitly Python module
                return self._execute_python_import(module_name, context_name, context)
            else:
                # Dana module (implicit .na)
                return self._execute_dana_import(module_name, context_name, context)

        except SandboxError:
            # Re-raise SandboxErrors directly
            raise
        except Exception as e:
            # Convert other errors to SandboxErrors for consistency
            raise SandboxError(f"Error importing module '{module_name}': {e}") from e

    def execute_import_from_statement(self, node: ImportFromStatement, context: SandboxContext) -> Any:
        """Execute a from-import statement with optimized processing.

        Args:
            node: The from-import statement to execute
            context: The execution context

        Returns:
            None (import statements don't return values)
        """
        self._import_count += 1
        module_name = node.module

        try:
            self._trace_import("from_import", module_name, f"names={[name for name, _ in node.names]}")

            if module_name.endswith(".py"):
                # Explicitly Python module
                return self._execute_python_from_import(module_name, node.names, context)
            else:
                # Dana module (implicit .na)
                return self._execute_dana_from_import(module_name, node.names, context)

        except SandboxError:
            # Re-raise SandboxErrors directly
            raise
        except Exception as e:
            # Convert other errors to SandboxErrors for consistency
            raise SandboxError(f"Error importing from module '{module_name}': {e}") from e

    def _execute_python_import(self, module_name: str, context_name: str, context: SandboxContext) -> None:
        """Execute import of a Python module with caching.

        Args:
            module_name: Full module name with .py extension
            context_name: Name to use in context
            context: The execution context
        """
        import importlib

        # Strip .py extension for Python import
        import_name = module_name[:-3] if module_name.endswith(".py") else module_name

        # Check cache first
        cache_key = f"py:{import_name}"
        if cache_key in self._module_cache:
            module = self._module_cache[cache_key]
            context.set(f"local:{context_name}", module)
            return None

        try:
            module = importlib.import_module(import_name)

            # Cache the module
            if len(self._module_cache) < self.MODULE_CACHE_SIZE:
                self._module_cache[cache_key] = module

            # Set the module in the local context
            context.set(f"local:{context_name}", module)
            return None

        except ImportError as e:
            raise SandboxError(f"Python module '{import_name}' not found: {e}") from e

    def _execute_dana_import(self, module_name: str, context_name: str, context: SandboxContext) -> None:
        """Execute Dana module import with caching.

        Args:
            module_name: Dana module name (may be relative)
            context_name: Name to use in context
            context: The execution context
        """
        self._ensure_module_system_initialized()

        # Handle relative imports
        absolute_module_name = self._resolve_relative_import(module_name, context)

        # Check cache first
        cache_key = f"dana:{absolute_module_name}"
        if cache_key in self._module_cache:
            module = self._module_cache[cache_key]
            context.set_in_scope(context_name, module, scope="local")

            # For submodule imports, also create parent namespace
            if "." in context_name:
                self._create_parent_namespaces(context_name, module, context)
            return

        # Get the module loader
        from dana.core.runtime.modules.core import get_module_loader

        loader = get_module_loader()

        try:
            # Find and load the module
            spec = loader.find_spec(absolute_module_name)
            if spec is None:
                raise ModuleNotFoundError(f"Dana module '{absolute_module_name}' not found")

            # Create and execute the module
            module = loader.create_module(spec)
            if module is None:
                raise ImportError(f"Could not create Dana module '{absolute_module_name}'")

            loader.exec_module(module)

            # Cache the module
            if len(self._module_cache) < self.MODULE_CACHE_SIZE:
                self._module_cache[cache_key] = module

            # Set module in context using the context name
            context.set_in_scope(context_name, module, scope="local")

            # For submodule imports like 'utils.text', also create parent namespace
            if "." in context_name:
                self._create_parent_namespaces(context_name, module, context)

        except Exception as e:
            # Convert to SandboxError for consistency
            raise SandboxError(f"Error loading Dana module '{absolute_module_name}': {e}") from e

    def _execute_python_from_import(self, module_name: str, names: list[tuple[str, str | None]], context: SandboxContext) -> None:
        """Execute from-import of a Python module with caching.

        Args:
            module_name: Full module name with .py extension
            names: List of (name, alias) tuples to import
            context: The execution context
        """
        import importlib

        # Strip .py extension for Python import
        import_name = module_name[:-3]

        # Check cache first
        cache_key = f"py:{import_name}"
        if cache_key in self._module_cache:
            module = self._module_cache[cache_key]
        else:
            try:
                module = importlib.import_module(import_name)

                # Cache the module
                if len(self._module_cache) < self.MODULE_CACHE_SIZE:
                    self._module_cache[cache_key] = module

            except ImportError as e:
                raise SandboxError(f"Python module '{import_name}' not found: {e}") from e

        # Import specific names from the module
        for name, alias in names:
            # Check if the name exists in the module
            if not hasattr(module, name):
                raise SandboxError(f"Cannot import name '{name}' from Python module '{import_name}'")

            # Get the object from the module
            obj = getattr(module, name)

            # Determine the name to use in the context
            context_name = alias if alias else name

            # Set the object in the local context
            context.set(f"local:{context_name}", obj)

            # If it's a function, also register it in the function registry for calls
            if callable(obj) and self.function_registry:
                self._register_imported_function(obj, context_name, module_name, name)

    def _execute_dana_from_import(self, module_name: str, names: list[tuple[str, str | None]], context: SandboxContext) -> None:
        """Execute Dana module from-import with caching.

        Args:
            module_name: Dana module name (may be relative)
            names: List of (name, alias) tuples to import
            context: The execution context
        """
        self._ensure_module_system_initialized()

        # Handle relative imports
        absolute_module_name = self._resolve_relative_import(module_name, context)

        # Check cache first
        cache_key = f"dana:{absolute_module_name}"
        if cache_key in self._module_cache:
            module = self._module_cache[cache_key]
        else:
            # Get the module loader
            from dana.core.runtime.modules.core import get_module_loader

            loader = get_module_loader()

            try:
                # Find and load the module
                spec = loader.find_spec(absolute_module_name)
                if spec is None:
                    raise ModuleNotFoundError(f"Dana module '{absolute_module_name}' not found")

                # Create and execute the module
                module = loader.create_module(spec)
                if module is None:
                    raise ImportError(f"Could not create Dana module '{absolute_module_name}'")

                loader.exec_module(module)

                # Cache the module
                if len(self._module_cache) < self.MODULE_CACHE_SIZE:
                    self._module_cache[cache_key] = module

            except Exception as e:
                # Convert to SandboxError for consistency
                raise SandboxError(f"Error loading Dana module '{absolute_module_name}': {e}") from e

        # Import specific names from the module
        for name, alias in names:
            # Check if the name exists in the module
            if not hasattr(module, name):
                raise SandboxError(f"Cannot import name '{name}' from Dana module '{absolute_module_name}'")

            # Get the object from the module
            obj = getattr(module, name)

            # Determine the name to use in the context
            context_name = alias if alias else name

            # Set the object in the local context
            context.set(f"local:{context_name}", obj)

            # If it's a function, also register it in the function registry for calls
            if callable(obj) and self.function_registry:
                self._register_imported_function(obj, context_name, module_name, name)

    def _register_imported_function(self, func: callable, context_name: str, module_name: str, original_name: str) -> None:
        """Register an imported function in the function registry with optimized handling.

        Args:
            func: The function to register
            context_name: The name to use in the context
            module_name: The module name
            original_name: The original function name
        """
        if not self.function_registry:
            return

        try:
            # Import here to avoid circular imports
            from dana.core.lang.interpreter.executor.function_resolver import FunctionType
            from dana.core.lang.interpreter.functions.python_function import PythonFunction

            # Wrap the function in a PythonFunction wrapper for Dana compatibility
            wrapped_func = PythonFunction(
                func=func,
                trusted_for_context=True,
            )

            # Register in the appropriate scope
            self.function_registry.register(
                name=context_name,
                func=wrapped_func,
                func_type=FunctionType.PYTHON,
                namespace="local",
                overwrite=True,  # Allow overwriting for imports
            )
            self.debug(f"Registered imported function '{context_name}' from module '{module_name}'")

        except Exception as reg_err:
            # Registration failed, but import to context succeeded
            # This is not fatal - function can still be accessed as module attribute
            self.warning(f"Failed to register imported function '{context_name}': {reg_err}")

    def _ensure_module_system_initialized(self) -> None:
        """Ensure the Dana module system is initialized with caching."""
        if self._module_loader_initialized:
            return

        from dana.core.runtime.modules.core import get_module_loader, initialize_module_system

        try:
            # Try to get the loader (this will raise if not initialized)
            get_module_loader()
            self._module_loader_initialized = True
        except Exception:
            # Initialize the module system if not already done
            initialize_module_system()
            self._module_loader_initialized = True

    def _create_parent_namespaces(self, context_name: str, module: Any, context: SandboxContext) -> None:
        """Create parent namespace objects for submodule imports with caching.

        Args:
            context_name: The full module name (e.g., 'utils.text')
            module: The loaded module object
            context: The execution context
        """
        parts = context_name.split(".")

        # Build up the namespace hierarchy
        for i in range(len(parts) - 1):  # Don't process the last part (that's the actual module)
            parent_path = ".".join(parts[: i + 1])
            child_name = parts[i + 1]

            # Check namespace cache first
            cache_key = f"ns:{parent_path}"
            if cache_key in self._namespace_cache:
                parent_ns = self._namespace_cache[cache_key]
            else:
                # Get or create the parent namespace
                try:
                    parent_ns = context.get_from_scope(parent_path, scope="local")
                    if parent_ns is None:
                        # Create new namespace
                        parent_ns = ModuleNamespace(parent_path)
                        context.set_in_scope(parent_path, parent_ns, scope="local")
                except Exception:
                    # Create new namespace
                    parent_ns = ModuleNamespace(parent_path)
                    context.set_in_scope(parent_path, parent_ns, scope="local")

                # Cache the namespace
                if len(self._namespace_cache) < self.NAMESPACE_CACHE_SIZE:
                    self._namespace_cache[cache_key] = parent_ns

            # Set the child in the parent namespace
            if i == len(parts) - 2:  # This is the direct parent of our module
                setattr(parent_ns, child_name, module)
            else:
                # This is an intermediate parent, set the next namespace level
                child_path = ".".join(parts[: i + 2])
                child_cache_key = f"ns:{child_path}"

                if child_cache_key in self._namespace_cache:
                    child_ns = self._namespace_cache[child_cache_key]
                else:
                    try:
                        child_ns = context.get_from_scope(child_path, scope="local")
                        if child_ns is None:
                            child_ns = ModuleNamespace(child_path)
                            context.set_in_scope(child_path, child_ns, scope="local")
                    except Exception:
                        child_ns = ModuleNamespace(child_path)
                        context.set_in_scope(child_path, child_ns, scope="local")

                    # Cache the namespace
                    if len(self._namespace_cache) < self.NAMESPACE_CACHE_SIZE:
                        self._namespace_cache[child_cache_key] = child_ns

                setattr(parent_ns, child_name, child_ns)

    def _resolve_relative_import(self, module_name: str, context: SandboxContext) -> str:
        """Resolve relative import names to absolute names with caching.

        Args:
            module_name: The module name (may be relative)
            context: The execution context

        Returns:
            The absolute module name
        """
        # If not relative, return as-is
        if not module_name.startswith("."):
            return module_name

        # Check cache first
        cache_key = f"rel:{module_name}:{getattr(context, '_current_package', None)}"
        if hasattr(self, "_relative_cache") and cache_key in self._relative_cache:
            return self._relative_cache[cache_key]

        # Get the current package name from context
        current_package = getattr(context, "_current_package", None)
        if not current_package:
            raise SandboxError(f"Relative import '{module_name}' attempted without package context")

        # Count leading dots
        leading_dots = 0
        for char in module_name:
            if char == ".":
                leading_dots += 1
            else:
                break

        # Get remaining path after dots
        remaining_path = module_name[leading_dots:]

        # Split current package into parts
        package_parts = current_package.split(".")

        # Calculate target package
        if leading_dots > len(package_parts):
            raise SandboxError(f"Relative import '{module_name}' goes beyond top-level package")

        # Go up the hierarchy
        target_package_parts = package_parts[:-leading_dots] if leading_dots > 0 else package_parts
        target_package = ".".join(target_package_parts) if target_package_parts else ""

        # Build final absolute module name
        if remaining_path:
            result = f"{target_package}.{remaining_path}" if target_package else remaining_path
        else:
            result = target_package

        # Cache the result
        if not hasattr(self, "_relative_cache"):
            self._relative_cache = {}
        if len(self._relative_cache) < 50:  # Small cache for relative imports
            self._relative_cache[cache_key] = result

        return result

    def _trace_import(self, import_type: str, module_name: str, context_info: str) -> None:
        """Trace import operations for debugging when enabled.

        Args:
            import_type: The type of import (import, from_import)
            module_name: The module being imported
            context_info: Additional context information
        """
        if self._import_count >= self.IMPORT_TRACE_THRESHOLD:
            try:
                self.debug(f"Import #{self._import_count}: {import_type} {module_name} ({context_info})")
            except Exception:
                # Don't let tracing errors affect execution
                pass

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._module_cache.clear()
        self._namespace_cache.clear()
        if hasattr(self, "_relative_cache"):
            self._relative_cache.clear()
        self._import_count = 0
        self._module_loader_initialized = False

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        return {
            "module_cache_size": len(self._module_cache),
            "namespace_cache_size": len(self._namespace_cache),
            "relative_cache_size": len(getattr(self, "_relative_cache", {})),
            "total_imports": self._import_count,
            "module_cache_utilization_percent": round(len(self._module_cache) / max(self.MODULE_CACHE_SIZE, 1) * 100, 2),
            "namespace_cache_utilization_percent": round(len(self._namespace_cache) / max(self.NAMESPACE_CACHE_SIZE, 1) * 100, 2),
        }
