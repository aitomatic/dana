"""
Optimized import handler for Dana statements.

This module provides high-performance import processing with
optimizations for module resolution, caching, and namespace management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, cast

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import ExportStatement, ImportFromStatement, ImportStatement
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

        Examples:
            - Dana module: ``import utils.text`` or with alias ``import utils.text as txt``
            - Python module: ``import os.py`` or with alias ``import os.py as osmod``

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

        Examples:
            - Dana module: ``from math_utils import add, sub as subtract``
            - Python module: ``from os.py import path, getenv as env``
            - Star import: ``from math import *``

        Args:
            node: The from-import statement to execute
            context: The execution context

        Returns:
            None (import statements don't return values)
        """
        self._import_count += 1
        module_name = node.module

        try:
            if node.is_star_import:
                self._trace_import("from_import", module_name, "names=*")
            else:
                self._trace_import("from_import", module_name, f"names={[name for name, _ in node.names]}")

            if module_name.endswith(".py"):
                # Explicitly Python module
                return self._execute_python_from_import(module_name, node.names, context, is_star=node.is_star_import)
            else:
                # Dana module (implicit .na)
                return self._execute_dana_from_import(module_name, node.names, context, is_star=node.is_star_import)

        except SandboxError:
            # Re-raise SandboxErrors directly
            raise
        except Exception as e:
            # Convert other errors to SandboxErrors for consistency
            raise SandboxError(f"Error importing from module '{module_name}': {e}") from e

    def execute_export_statement(self, node: ExportStatement, context: SandboxContext) -> None:
        """Execute an export statement with optimized processing.

        Args:
            node: The export statement node
            context: The execution context

        Returns:
            None
        """
        # Get the name to export
        name = node.name

        # Validate presence in local scope if already defined (best-effort)
        try:
            context.get_from_scope(name, scope="local")
        except Exception:
            # If not defined yet, that's acceptable; it may be defined later in the module
            pass

        # Track exports on the context
        if not hasattr(context, "_exports"):
            context._exports = set()
        context._exports.add(name)

        # Trace export operation
        try:
            self.debug(f"Exporting name: {name}")
        except Exception:
            pass

        return None

    def _execute_python_import(self, module_name: str, context_name: str, context: SandboxContext) -> None:
        """Execute import of a Python module with caching.

        Example:
            ``import os.py as osmod``  -> binds module to ``local:osmod``

        Args:
            module_name: Full module name with .py extension
            context_name: Name to use in context
            context: The execution context
        """
        import importlib
        import sys
        from pathlib import Path

        # Strip .py extension for Python import
        import_name = module_name[:-3] if module_name.endswith(".py") else module_name

        # Check cache first
        cache_key = f"py:{import_name}"
        if cache_key in self._module_cache:
            module = self._module_cache[cache_key]
            context.set(f"local:{context_name}", module)
            return None

        # Get the current executing file's directory to add to sys.path temporarily
        current_file_dir = None
        if hasattr(context, "error_context") and context.error_context and context.error_context.current_file:
            current_file_dir = str(Path(context.error_context.current_file).parent)

        # Temporarily add the script's directory to sys.path for relative Python imports
        path_added = False
        try:
            if current_file_dir and current_file_dir not in sys.path:
                sys.path.insert(0, current_file_dir)
                path_added = True
                self.debug(f"Temporarily added '{current_file_dir}' to sys.path for Python import '{import_name}'")

            module = importlib.import_module(import_name)

            # Cache the module
            if len(self._module_cache) < self.MODULE_CACHE_SIZE:
                self._module_cache[cache_key] = module

            # Set the module in the local context
            context.set(f"local:{context_name}", module)
            return None

        except ImportError as e:
            raise SandboxError(f"Python module '{import_name}' not found: {e}") from e
        finally:
            # Clean up sys.path modification
            if path_added and current_file_dir in sys.path:
                sys.path.remove(current_file_dir)
                self.debug(f"Removed '{current_file_dir}' from sys.path after Python import attempt")

    def _execute_dana_import(self, module_name: str, context_name: str, context: SandboxContext) -> None:
        """Execute Dana module import with caching.

        Example:
            ``import utils.text as txt``  -> binds module to ``local:txt`` and merges public data

        Args:
            module_name: Dana module name (may be relative)
            context_name: Name to use in context
            context: The execution context
        """
        self._ensure_module_system_initialized(context)

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
        from dana.__init__.init_modules import get_module_loader, get_module_registry

        loader = get_module_loader()

        # Get the current module's file path if available
        current_module_file = None
        current_module_name = getattr(context, "_current_module", None)
        if current_module_name:
            try:
                registry = get_module_registry()
                if registry:
                    current_module = registry.get_module(current_module_name)
                    current_module_file = current_module.__file__
            except Exception:
                # Module not found in registry, that's okay
                pass

        try:
            # Find and load the module
            # Pass the current module's file path as a hint via the path parameter
            path = [f"__dana_importing_from__:{current_module_file}"] if current_module_file else None
            spec = loader.find_spec(absolute_module_name, path=path)
            if spec is None:
                raise ModuleNotFoundError(f"Dana module '{absolute_module_name}' not found")

            # Create and execute the module
            module = loader.create_module(spec)
            if module is None:
                raise ImportError(f"Could not create Dana module '{absolute_module_name}'")

            loader.exec_module(cast(Any, module))

            # Cache the module
            if len(self._module_cache) < self.MODULE_CACHE_SIZE:
                self._module_cache[cache_key] = module

            # Set module in context using the context name
            context.set_in_scope(context_name, module, scope="local")

            # Merge public variables from the module into the global public scope
            if hasattr(module, "__dict__"):
                for key, value in module.__dict__.items():
                    if not key.startswith("_") and not callable(value):
                        # This is a public variable from the module
                        context.set_in_scope(key, value, scope="public")

            # For submodule imports like 'utils.text', also create parent namespace
            if "." in context_name:
                self._create_parent_namespaces(context_name, module, context)

        except Exception as e:
            # Convert to SandboxError for consistency
            raise SandboxError(f"Error loading Dana module '{absolute_module_name}': {e}") from e

    def _execute_python_from_import(
        self, module_name: str, names: list[tuple[str, str | None]], context: SandboxContext, is_star: bool = False
    ) -> None:
        """Execute from-import of a Python module with caching (refactored).

        Example:
            ``from os.py import path, getenv as env``  -> binds ``local:path`` and ``local:env``
            ``from math.py import *``  -> imports all public names
        """
        module, import_name = self._get_module(kind="py", module_name=module_name, context=context)

        if is_star:
            # Star import: import all public names from the module
            self._import_all_from_module(
                module,
                context,
                module_name_for_errors=import_name,
                enforce_exports=False,
                enforce_underscore_privacy=True,  # Even for Python, don't import private names
                crosswire_dana_functions=False,
            )
        else:
            # Explicit imports
            self._import_names_from_module(
                module,
                names,
                context,
                module_name_for_errors=import_name,
                enforce_exports=False,
                enforce_underscore_privacy=False,
                crosswire_dana_functions=False,
            )

    def _execute_dana_from_import(
        self, module_name: str, names: list[tuple[str, str | None]], context: SandboxContext, is_star: bool = False
    ) -> None:
        """Execute Dana module from-import with caching (refactored).

        Example:
            ``from core.math import add, sub as subtract``  -> binds ``local:add`` and ``local:subtract``
            ``from dana.libs.corelib.na_modules import *``  -> imports all exported names
        """
        self._ensure_module_system_initialized(context)
        # Resolve the base module path
        base_absolute_module = self._resolve_relative_import(module_name, context)

        if is_star:
            # Star import: load the base module and import all names
            module, absolute_module_name = self._get_module(kind="dana", module_name=module_name, context=context)
            self._import_all_from_module(
                module,
                context,
                module_name_for_errors=absolute_module_name,
                enforce_exports=True,
                enforce_underscore_privacy=True,
                crosswire_dana_functions=True,
            )
        else:
            # Explicit imports: try to load from base module first, then as submodules
            for name, alias in names:
                context_name = alias if alias else name
                imported_successfully = False

                # First attempt: load the base module and extract the name
                try:
                    base_module, _ = self._get_module(kind="dana", module_name=module_name, context=context)

                    # Use try/except instead of hasattr() to work within Dana sandbox
                    try:
                        getattr(base_module, name)
                        has_attribute = True
                    except AttributeError:
                        has_attribute = False

                    if has_attribute:
                        # Check privacy before importing
                        if name.startswith("_"):
                            raise SandboxError(
                                f"Cannot import name '{name}' from Dana module '{base_absolute_module}': names starting with '_' are private"
                            )
                        # Found the name in the base module - import it
                        imported_obj = getattr(base_module, name)

                        # Check if this is a lazy loader function and resolve it
                        if callable(imported_obj):
                            # Check if it's our lazy loader by examining the __NAME__ attribute
                            if hasattr(imported_obj, "__NAME__") and imported_obj.__NAME__ == "__LAZY_MODULE_LOADER__":
                                # This is a lazy loader, call it to get the actual module
                                try:
                                    potential_module = imported_obj()
                                    # If it returns a Module object, this was a lazy loader
                                    if hasattr(potential_module, "__name__") and hasattr(potential_module, "__file__"):
                                        imported_obj = potential_module
                                except Exception:
                                    # If calling fails, it's not a lazy loader, leave as-is
                                    pass
                        context.set_in_scope(context_name, imported_obj, scope="local")
                        imported_successfully = True
                except SandboxError as e:
                    # Re-raise SandboxError (privacy violations, etc) immediately
                    if "names starting with '_' are private" in str(e):
                        raise
                    # Other SandboxErrors fall through to submodule attempt
                except Exception:
                    # Base module loading failed, will try submodule approach
                    pass

                # Second attempt: try loading as a submodule
                if not imported_successfully:
                    try:
                        submodule_name = f"{base_absolute_module}.{name}"
                        submodule, _ = self._get_module(kind="dana", module_name=submodule_name, context=context)
                        context.set_in_scope(context_name, submodule, scope="local")
                        imported_successfully = True
                    except Exception:
                        pass

                if not imported_successfully:
                    # Check if this might be a circular import timing issue
                    error_message = f"Cannot import name '{name}' from Dana module '{base_absolute_module}'"

                    # Try to determine if it's a circular import issue
                    is_circular_import = False
                    try:
                        # Check if we can load the base module
                        base_module, _ = self._get_module(kind="dana", module_name=module_name, context=context)

                        # Check if any modules in the chain are currently loading
                        from dana.__init__.init_modules import get_module_loader, get_module_registry

                        try:
                            _loader = get_module_loader()
                            registry = get_module_registry()
                            module_parts = base_absolute_module.split(".")
                            for i in range(len(module_parts)):
                                partial_module_name = ".".join(module_parts[: i + 1])
                                if registry and hasattr(registry, "is_module_loading") and registry.is_module_loading(partial_module_name):
                                    error_message += (
                                        f" (module '{partial_module_name}' is currently being loaded - circular import detected)"
                                    )
                                    is_circular_import = True
                                    break
                        except Exception:
                            # If we can't check module loading status, continue with other error detection
                            pass

                        if not is_circular_import and hasattr(base_module, "__file__") and base_module.__file__:
                            # Module exists but doesn't have the attribute - check if it's timing related
                            module_attrs = [attr for attr in dir(base_module) if not attr.startswith("_")]
                            if module_attrs:
                                error_message += (
                                    f" (available attributes: {', '.join(module_attrs[:5])}{'...' if len(module_attrs) > 5 else ''})"
                                )
                                # If module has other attributes but not this one, likely a timing issue
                                is_circular_import = True
                            else:
                                error_message += " (module appears to be partially initialized)"
                                is_circular_import = True
                        elif not is_circular_import:
                            error_message += ": name not found"
                    except Exception as e:
                        # If we can't even load the base module, it might be circular
                        if "circular" in str(e).lower() or "loading" in str(e).lower():
                            error_message += f" (circular import issue: {e})"
                            is_circular_import = True
                        else:
                            error_message += ": name not found"

                    # Add helpful hint for circular imports (avoid duplicates)
                    if (
                        is_circular_import or "circular import" in error_message or "partially initialized" in error_message
                    ) and "Hint:" not in error_message:
                        error_message += "\n\nHint: This error often occurs when modules import from each other and attributes are accessed before they're defined. Try defining variables before importing submodules that might need them."

                    raise SandboxError(error_message)

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

        # If this is an alias import, update the function's __name__ attribute
        # But only if it's writable (not for builtin functions)
        if context_name != original_name and hasattr(func, "__name__"):
            try:
                func.__name__ = context_name
            except (AttributeError, TypeError):
                # __name__ is not writable (e.g., builtin functions), skip modification
                pass

        try:
            # Import here to avoid circular imports
            from dana.core.lang.interpreter.executor.function_resolver import FunctionType
            from dana.core.lang.interpreter.functions.dana_function import DanaFunction
            from dana.registry.function_registry import FunctionMetadata

            # Determine function type and create metadata
            if isinstance(func, DanaFunction):
                func_type = FunctionType.DANA
                metadata = FunctionMetadata(source_file=f"<imported from {module_name}>")
                metadata.context_aware = True
                metadata.is_public = True
            else:
                func_type = FunctionType.PYTHON
                metadata = FunctionMetadata(source_file=f"<imported from {module_name}>")
                metadata.context_aware = False
                metadata.is_public = True

            metadata.doc = f"Imported from {module_name}.{original_name}"

            # Register the function under the alias name (or original name if no alias)
            self.function_registry.register(
                name=context_name, func=func, namespace="local", func_type=func_type, metadata=metadata, overwrite=True
            )

            self.debug(f"Registered imported function '{context_name}' from module '{module_name}'")

        except Exception as reg_err:
            # Registration failed, but import to context succeeded
            # This is not fatal - function can still be accessed as module attribute
            self.warning(f"Failed to register imported function '{context_name}': {reg_err}")

    def _ensure_module_system_initialized(self, context: SandboxContext | None = None) -> None:
        """Ensure the Dana module system is initialized with caching."""

        if self._module_loader_initialized:
            return

        from dana.__init__.init_modules import get_module_loader, initialize_module_system

        try:
            # Try to get the loader (this will raise if not initialized)
            get_module_loader()
            self._module_loader_initialized = True
        except Exception:
            # Get custom search paths from context if provided
            search_paths = None
            if context:
                search_paths = context.get("system:module_search_paths")

            # Initialize the module system if not already done
            initialize_module_system(search_paths=search_paths)
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
        # For relative imports:
        #   .module = same package (0 levels up)
        #   ..module = parent package (1 level up)
        #   ...module = grandparent package (2 levels up)
        # So we need to go up (leading_dots - 1) levels
        if leading_dots > 1:
            # Go up (leading_dots - 1) levels
            levels_up = leading_dots - 1
            if levels_up >= len(package_parts):
                raise SandboxError(f"Relative import '{module_name}' goes beyond top-level package")
            target_package_parts = package_parts[:-levels_up]
        elif leading_dots == 1:
            # Same package (0 levels up)
            target_package_parts = package_parts
        else:
            # This shouldn't happen since we already checked for leading dots
            target_package_parts = package_parts

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

    def _get_module(self, kind: str, module_name: str, context: SandboxContext) -> tuple[Any, str]:
        """Fetch a module (Python or Dana) with caching and return (module, name_for_errors).

        kind: "py" or "dana"
        module_name: For Python, may end with ".py"; for Dana, may be relative (e.g., ".utils").
        name_for_errors: Stripped import name (py) or absolute module name (dana).
        """
        if kind == "py":
            import importlib
            import sys
            from pathlib import Path

            import_name = module_name[:-3] if module_name.endswith(".py") else module_name
            cache_key = f"py:{import_name}"
            if cache_key in self._module_cache:
                return self._module_cache[cache_key], import_name

            # Get the current executing file's directory to add to sys.path temporarily
            current_file_dir = None
            if hasattr(context, "error_context") and context.error_context and context.error_context.current_file:
                current_file_dir = str(Path(context.error_context.current_file).parent)

            # Temporarily add the script's directory to sys.path for relative Python imports
            path_added = False
            try:
                if current_file_dir and current_file_dir not in sys.path:
                    sys.path.insert(0, current_file_dir)
                    path_added = True
                    self.debug(f"Temporarily added '{current_file_dir}' to sys.path for Python import '{import_name}'")

                module = importlib.import_module(import_name)
                if len(self._module_cache) < self.MODULE_CACHE_SIZE:
                    self._module_cache[cache_key] = module
                return module, import_name
            except ImportError as e:
                raise SandboxError(f"Python module '{import_name}' not found: {e}") from e
            finally:
                # Clean up sys.path modification
                if path_added and current_file_dir in sys.path:
                    sys.path.remove(current_file_dir)
                    self.debug(f"Removed '{current_file_dir}' from sys.path after Python import attempt")
        elif kind == "dana":
            absolute_module_name = self._resolve_relative_import(module_name, context)
            cache_key = f"dana:{absolute_module_name}"
            if cache_key in self._module_cache:
                return self._module_cache[cache_key], absolute_module_name
            try:
                from dana.__init__.init_modules import get_module_loader

                loader = get_module_loader()
                spec = loader.find_spec(absolute_module_name)
                if spec is None:
                    raise SandboxError(f"Module '{module_name}' not found")
                module = loader.create_module(spec)
                if module is None:
                    raise SandboxError(f"Could not create module '{module_name}'")
                loader.exec_module(cast(Any, module))
                if len(self._module_cache) < self.MODULE_CACHE_SIZE:
                    self._module_cache[cache_key] = module
                return module, absolute_module_name
            except Exception as e:
                raise SandboxError(f"Error loading Dana module '{absolute_module_name}': {e}") from e
        else:
            raise SandboxError(f"Unknown module kind '{kind}'")

    def _import_names_from_module(
        self,
        module: Any,
        names: list[tuple[str, str | None]],
        context: SandboxContext,
        *,
        module_name_for_errors: str,
        enforce_exports: bool,
        enforce_underscore_privacy: bool,
        crosswire_dana_functions: bool,
    ) -> None:
        """Common implementation for importing specific names from a module.

        Applies optional privacy/export enforcement and handles function registration.
        """
        for name, alias in names:
            if not hasattr(module, name):
                raise SandboxError(
                    f"Cannot import name '{name}' from {'Dana' if enforce_exports else 'Python'} module '{module_name_for_errors}': name not found"
                )
            if enforce_underscore_privacy and name.startswith("_"):
                raise SandboxError(
                    f"Cannot import name '{name}' from Dana module '{module_name_for_errors}': names starting with '_' are private"
                )
            # Check for exports using try/except instead of hasattr()
            try:
                module_exports = getattr(module, "__exports__", None)
                has_exports = module_exports is not None
            except AttributeError:
                has_exports = False

            if enforce_exports and has_exports and name not in module_exports:
                raise SandboxError(f"Cannot import name '{name}' from Dana module '{module_name_for_errors}': not in module exports")
            obj = getattr(module, name)
            context_name = alias if alias else name
            context.set(f"local:{context_name}", obj)
            if callable(obj) and self.function_registry:
                self._register_imported_function(obj, context_name, module_name_for_errors, name)
                if crosswire_dana_functions:
                    try:
                        from dana.core.lang.interpreter.functions.dana_function import DanaFunction  # type: ignore

                        if isinstance(obj, DanaFunction) and obj.context is not None:
                            for module_name_key, module_obj in module.__dict__.items():
                                if callable(module_obj) and not module_name_key.startswith("__"):
                                    obj.context.set_in_scope(module_name_key, module_obj, scope="local")
                    except Exception:
                        # Best-effort: do not fail import due to cross-wiring issues
                        pass

    def _import_all_from_module(
        self,
        module: Any,
        context: SandboxContext,
        *,
        module_name_for_errors: str,
        enforce_exports: bool,
        enforce_underscore_privacy: bool,
        crosswire_dana_functions: bool,
    ) -> None:
        """Import all public/exported names from a module (star import).

        For Dana modules: respects __exports__ if present, otherwise imports all public names.
        For Python modules: imports all names except those starting with underscore.
        """
        # Determine which names to import
        # Use try/except instead of hasattr() to work within Dana sandbox
        try:
            module_exports = getattr(module, "__exports__", None)
            has_exports = module_exports is not None
        except AttributeError:
            has_exports = False

        try:
            module_all = getattr(module, "__all__", None)
            has_all = module_all is not None
        except AttributeError:
            has_all = False

        if enforce_exports and has_exports:
            # Dana module with explicit exports
            names_to_import = module_exports
        elif has_all:
            # Python module with __all__ defined
            names_to_import = module_all
        else:
            # Default: import all attributes that don't start with underscore
            names_to_import = []
            for name in dir(module):
                if enforce_underscore_privacy and name.startswith("_"):
                    continue
                # Skip special attributes
                if name.startswith("__") and name.endswith("__"):
                    continue
                names_to_import.append(name)

        # Import each name
        for name in names_to_import:
            # Use try/except instead of hasattr() to work within Dana sandbox
            try:
                getattr(module, name)
                has_name = True
            except AttributeError:
                has_name = False

            if not has_name:
                # Skip names that don't exist (e.g., from __all__ but not actually defined)
                self.warning(f"Name '{name}' listed in exports but not found in module '{module_name_for_errors}'")
                continue

            obj = getattr(module, name)
            context.set(f"local:{name}", obj)

            # Register functions
            if callable(obj) and self.function_registry:
                self._register_imported_function(obj, name, module_name_for_errors, name)

                # Cross-wire Dana functions if needed
                if crosswire_dana_functions:
                    try:
                        from dana.core.lang.interpreter.functions.dana_function import DanaFunction  # type: ignore

                        if isinstance(obj, DanaFunction) and obj.context is not None:
                            for module_name_key, module_obj in module.__dict__.items():
                                if callable(module_obj) and not module_name_key.startswith("__"):
                                    obj.context.set_in_scope(module_name_key, module_obj, scope="local")
                    except Exception:
                        # Best-effort: do not fail import due to cross-wiring issues
                        pass
