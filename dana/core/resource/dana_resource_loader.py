"""
Dana Resource Loader

This module handles loading and execution of Dana resource implementations (.na files).
It integrates with the Dana parser and runtime to create functional resources from Dana code.
"""

import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dana.common.error_utils import ErrorUtils
from dana.core.lang.parser.utils.parsing_utils import ParserCache

from .base_resource import BaseResource

if TYPE_CHECKING:
    from dana.core.lang.sandbox_context import SandboxContext


class DanaResourceProxy(BaseResource):
    """
    Proxy that wraps a Dana resource implementation.

    This allows Dana-defined resources to be used through the same interface
    as Python resources.
    """

    def __init__(self, name: str, kind: str, dana_context: SandboxContext, resource_instance: Any, **kwargs):
        super().__init__(name=name, kind=kind, **kwargs)
        self.dana_context = dana_context
        self.resource_instance = resource_instance
        self._dana_functions = {}

        # Extract Dana functions that operate on this resource
        self._discover_dana_functions()

    def _discover_dana_functions(self):
        """Discover Dana functions that operate on this resource type."""
        # This would need to inspect the Dana context for functions
        # that have the pattern: def (resource: ResourceType) function_name(...)
        # For now, we'll assume standard functions exist

        standard_functions = ["initialize", "start", "stop", "query", "get_stats", "is_running"]

        for func_name in standard_functions:
            # Check if function exists in Dana context (stored in local scope)
            full_func_name = f"{self.kind}_resource_{func_name}"
            if self.dana_context.has(f"local:{full_func_name}"):
                self._dana_functions[func_name] = full_func_name

    def initialize(self) -> bool:
        """Initialize the Dana resource."""
        if "initialize" in self._dana_functions:
            try:
                result = self._call_dana_function("initialize")
                return bool(result)
            except Exception as e:
                print(f"Error initializing Dana resource {self.name}: {e}")
                return False
        return True

    def cleanup(self) -> bool:
        """Clean up the Dana resource."""
        if "stop" in self._dana_functions:
            try:
                result = self._call_dana_function("stop")
                return bool(result)
            except Exception as e:
                print(f"Error cleaning up Dana resource {self.name}: {e}")
                return False
        return True

    def query(self, request: Any) -> Any:
        """Query the Dana resource."""
        if "query" in self._dana_functions:
            try:
                return self._call_dana_function("query", request)
            except Exception as e:
                return f"Error querying Dana resource: {e}"
        return f"Query not implemented for {self.kind} resource"

    def start(self) -> bool:
        """Start the Dana resource."""
        if "start" in self._dana_functions:
            try:
                result = self._call_dana_function("start")
                return bool(result)
            except Exception as e:
                print(f"Error starting Dana resource {self.name}: {e}")
                return False
        return True

    def stop(self) -> bool:
        """Stop the Dana resource."""
        if "stop" in self._dana_functions:
            try:
                result = self._call_dana_function("stop")
                return bool(result)
            except Exception as e:
                print(f"Error stopping Dana resource {self.name}: {e}")
                return False
        return True

    def is_running(self) -> bool:
        """Check if Dana resource is running."""
        if "is_running" in self._dana_functions:
            try:
                result = self._call_dana_function("is_running")
                return bool(result)
            except Exception:
                pass

        # Fallback: check state field if it exists
        if hasattr(self.resource_instance, "state"):
            return self.resource_instance.state == "running"
        return True

    def _call_dana_function(self, func_name: str, *args) -> Any:
        """Call a Dana function with the resource instance."""
        if func_name in self._dana_functions:
            dana_func_name = self._dana_functions[func_name]
            if self.dana_context.exists(dana_func_name):
                func = self.dana_context.get(dana_func_name)
                if callable(func):
                    return func(self.resource_instance, *args)
        raise AttributeError(f"Dana function {func_name} not found")


class DanaResourceLoader:
    """
    Loads Dana resource implementations from .na files.

    This class handles parsing Dana code, executing resource definitions,
    and creating proxy objects that can be used by the resource system.
    """

    def __init__(self):
        self.parser = ParserCache.get_parser("dana")
        self.loaded_resources: dict[str, dict[str, Any]] = {}

    def load_dana_resource(self, na_file: Path) -> dict[str, Any] | None:
        """
        Load a Dana resource from a .na file.

        Returns:
            Dictionary with resource metadata and factory function, or None if failed
        """
        try:
            # Check if this resource is already loaded to avoid duplicate loading
            resource_key = str(na_file)
            if resource_key in self.loaded_resources:
                return self.loaded_resources[resource_key]

            # Read the Dana file
            with open(na_file, encoding="utf-8") as f:
                dana_code = f.read()

            # Parse the Dana code
            try:
                ast = self.parser.parse(dana_code)
            except Exception as e:
                # Provide a clearer, user-friendly error message (e.g., reserved keyword misuse)
                friendly = ErrorUtils.format_user_error(e, dana_code)
                print(f"Error loading Dana resource from {na_file}:\n{friendly}")
                return None
            if not ast:
                print(f"Failed to parse {na_file}")
                return None

            # Create a sandbox context for execution
            from dana.core.lang.sandbox_context import SandboxContext

            context = SandboxContext()
            from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

            interpreter = DanaInterpreter()
            context.interpreter = interpreter

            # Execute the Dana code to define the resource and functions
            try:
                # Use the current interpreter API
                interpreter.execute_program(ast, context)
            except Exception as e:
                # Format execution errors via ErrorUtils for consistency
                friendly = ErrorUtils.format_user_error(e)
                print(f"Error executing Dana resource {na_file}: {friendly}")
                return None

            # Extract resource information
            resource_info = self._extract_resource_info(context, na_file.stem)
            if not resource_info:
                print(f"No resource definition found in {na_file}")
                return None

            # Create factory function
            def resource_factory(name: str, kind: str, **kwargs) -> DanaResourceProxy:
                # Create a new context for each resource instance
                from dana.core.lang.sandbox_context import SandboxContext

                instance_context = SandboxContext()
                from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

                instance_interpreter = DanaInterpreter()
                instance_context.interpreter = instance_interpreter

                # Copy the resource type and functions from the original context
                # instead of re-executing the entire program
                resource_class = context.get(f"local:{resource_info['class_name']}")
                if not resource_class:
                    raise RuntimeError(f"Resource class {resource_info['class_name']} not found")

                # Copy functions to the new context
                for func_name in resource_info.get("functions", []):
                    # Look for the function in the original context
                    for possible_name in [
                        f"{resource_info['class_name'].lower()}_{func_name}",
                        f"{resource_info['class_name']}_{func_name}",
                        func_name,
                    ]:
                        if context.has(f"local:{possible_name}"):
                            func = context.get(f"local:{possible_name}")
                            instance_context.set(f"local:{possible_name}", func)
                            break

                # Create resource instance using the copied class
                resource_instance = resource_class(name=name, kind=kind, **kwargs)

                # Create and return proxy
                return DanaResourceProxy(name=name, kind=kind, dana_context=instance_context, resource_instance=resource_instance, **kwargs)

            result = {
                "name": resource_info["name"],
                "kind": resource_info["kind"],
                "class_name": resource_info["class_name"],
                "file_path": str(na_file),
                "factory": resource_factory,
                "metadata": {
                    "description": resource_info.get("description", ""),
                    "file_type": "dana",
                    "functions": resource_info.get("functions", []),
                },
            }

            # Cache the loaded resource to avoid duplicate loading
            self.loaded_resources[resource_key] = result
            return result

        except Exception as e:
            print(f"Error loading Dana resource from {na_file}: {e}")
            traceback.print_exc()
            return None

    def _extract_resource_info(self, context: SandboxContext, file_stem: str) -> dict[str, Any] | None:
        """
        Extract resource information from the executed Dana context.

        This looks for resource definitions and associated functions.
        """
        try:
            # Look for resource definitions in the context
            # This is a simplified approach - in a full implementation we'd
            # need to inspect the AST for resource definitions

            # Try common naming patterns
            possible_names = [file_stem, file_stem.replace("_", ""), "".join(word.capitalize() for word in file_stem.split("_"))]

            for name in possible_names:
                # Check if a resource class exists
                class_name = f"{name}Resource" if not name.endswith("Resource") else name

                if context.has(f"local:{class_name}"):
                    resource_class = context.get(f"local:{class_name}")

                    # Extract kind from resource class if possible
                    kind = getattr(resource_class, "kind", file_stem)
                    if isinstance(kind, str) and kind.startswith('"') and kind.endswith('"'):
                        kind = kind[1:-1]  # Remove quotes

                    return {
                        "name": file_stem,
                        "kind": kind,
                        "class_name": class_name,
                        "description": f"Dana resource from {file_stem}.na",
                        "functions": self._find_resource_functions(context, class_name),
                    }

            return None

        except Exception as e:
            print(f"Error extracting resource info: {e}")
            return None

    def _find_resource_functions(self, context: SandboxContext, class_name: str) -> list[str]:
        """Find functions that operate on the resource type."""
        functions = []

        # Standard resource functions to look for
        standard_functions = ["initialize", "start", "stop", "query", "get_stats", "is_running"]

        for func_name in standard_functions:
            # Check various naming patterns
            possible_func_names = [f"{class_name.lower()}_{func_name}", f"{class_name}_{func_name}", func_name]

            for full_func_name in possible_func_names:
                if context.has(f"local:{full_func_name}"):
                    functions.append(func_name)
                    break

        return functions

    def is_dana_resource_file(self, file_path: Path) -> bool:
        """Check if a file is a Dana resource file."""
        if not file_path.suffix == ".na":
            return False

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read(1000)  # Read first 1000 chars
                return "resource " in content
        except Exception:
            return False
