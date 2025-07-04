"""
Dana Dana Module System - Module Loader

This module provides the loader responsible for finding and loading Dana modules.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from __future__ import annotations

from collections.abc import Sequence
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec as PyModuleSpec
from pathlib import Path
from typing import TYPE_CHECKING

from dana.core.lang.parser.utils.parsing_utils import ParserCache

from .errors import ImportError, ModuleNotFoundError, SyntaxError
from .registry import ModuleRegistry
from .types import Module, ModuleSpec

if TYPE_CHECKING:
    from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
    from dana.core.lang.sandbox_context import SandboxContext


class ModuleLoader(MetaPathFinder, Loader):
    """Loader responsible for finding and loading Dana modules."""

    def __init__(self, search_paths: list[str], registry: ModuleRegistry):
        """Initialize a new module loader.

        Args:
            search_paths: List of paths to search for modules
            registry: Module registry instance
        """
        self.search_paths = [Path(p).resolve() for p in search_paths]
        self.registry = registry

    def find_spec(self, fullname: str, path: Sequence[str | bytes] | None = None, target: Module | None = None) -> PyModuleSpec | None:
        """Find a module specification.

        This implements the MetaPathFinder protocol for Python's import system.
        IMPORTANT: Only handles Dana modules (.na files). Returns None for all
        other modules to let Python's normal import system handle them.

        Args:
            fullname: Fully qualified module name
            path: Search path (unused, we use our own search paths)
            target: Module object if reload (unused)

        Returns:
            Module specification if found, None otherwise (does NOT raise)
        """
        # Only handle Dana module names (no internal Python modules)
        # Skip Python internal modules and standard library modules
        if (
            fullname.startswith("_")
            or "." in fullname
            and fullname.split(".")[0]
            in {
                "collections",
                "sys",
                "os",
                "json",
                "math",
                "datetime",
                "traceback",
                "importlib",
                "threading",
                "logging",
                "urllib",
                "http",
                "xml",
                "html",
                "email",
                "calendar",
                "time",
                "random",
                "hashlib",
                "pickle",
                "copy",
                "itertools",
                "functools",
                "operator",
                "pathlib",
                "re",
                "uuid",
                "base64",
                "binascii",
                "struct",
                "array",
                "weakref",
                "gc",
                "types",
                "inspect",
                "ast",
                "dis",
                "encodings",
                "codecs",
                "io",
                "tempfile",
                "shutil",
                "glob",
                "fnmatch",
                "subprocess",
                "signal",
                "socket",
                "select",
                "errno",
                "stat",
                "platform",
                "getpass",
                "pwd",
                "grp",
                "ctypes",
                "concurrent",
                "asyncio",
                "multiprocessing",
                "queue",
                "heapq",
                "bisect",
                "contextlib",
                "decimal",
                "fractions",
                "statistics",
                "zlib",
                "gzip",
                "bz2",
                "lzma",
                "zipfile",
                "tarfile",
                "csv",
                "configparser",
                "netrc",
                "xdrlib",
                "plistlib",
                "sqlite3",
                "dbm",
                "zoneinfo",
                "argparse",
                "getopt",
                "shlex",
                "readline",
                "rlcompleter",
                "cmd",
                "pdb",
                "profile",
                "pstats",
                "timeit",
                "trace",
                "cProfile",
                "unittest",
                "doctest",
                "test",
                "bdb",
                "faulthandler",
                "warnings",
                "dataclasses",
                "contextlib2",
                "typing_extensions",
                "packaging",
                "setuptools",
                "pip",
                "wheel",
                "distutils",
                "pkg_resources",
                "six",
                "certifi",
                "urllib3",
                "requests",
                "click",
                "jinja2",
                "werkzeug",
                "flask",
                "django",
                "lark",
                "pytest",
                "numpy",
                "pandas",
                "matplotlib",
                "scipy",
                "sklearn",
                "tensorflow",
                "torch",
                "boto3",
                "pydantic",
                "fastapi",
            }
        ):
            return None

        # Check if spec already exists in registry
        try:
            dana_spec = self.registry.get_spec(fullname)
            if dana_spec is not None:
                # Convert to Python spec
                py_spec = PyModuleSpec(name=dana_spec.name, loader=self, origin=dana_spec.origin)
                py_spec.has_location = dana_spec.has_location
                py_spec.submodule_search_locations = dana_spec.submodule_search_locations
                return py_spec
        except ModuleNotFoundError:
            pass  # Continue searching

        # Extract module name from fullname
        module_name = fullname.split(".")[-1]

        # If this is a submodule, check parent package's search paths
        if "." in fullname:
            parent_name = fullname.rsplit(".", 1)[0]
            try:
                parent_spec = self.find_spec(parent_name, None)
                if parent_spec is not None and parent_spec.submodule_search_locations:
                    # Search for module file in parent package's search paths
                    for search_path in parent_spec.submodule_search_locations:
                        module_file = Path(search_path) / f"{module_name}.na"
                        if module_file.is_file():
                            # Create and register Dana spec
                            dana_spec = ModuleSpec(name=fullname, loader=self, origin=str(module_file))
                            self.registry.register_spec(dana_spec)
                            # Convert to Python spec
                            py_spec = PyModuleSpec(name=dana_spec.name, loader=self, origin=dana_spec.origin)
                            py_spec.has_location = dana_spec.has_location
                            py_spec.submodule_search_locations = dana_spec.submodule_search_locations
                            return py_spec
            except ModuleNotFoundError:
                pass  # Continue searching

        # Search for module file in search paths
        module_file = self._find_module_file(module_name)
        if module_file is not None:
            # Create and register Dana spec
            dana_spec = ModuleSpec(name=fullname, loader=self, origin=str(module_file))
            self.registry.register_spec(dana_spec)
            # Convert to Python spec
            py_spec = PyModuleSpec(name=dana_spec.name, loader=self, origin=dana_spec.origin)
            py_spec.has_location = dana_spec.has_location
            py_spec.submodule_search_locations = dana_spec.submodule_search_locations
            return py_spec

        # Module not found after checking all paths - return None to let Python handle it
        return None

    def create_module(self, spec: PyModuleSpec) -> Module | None:
        """Create a new module object.

        Args:
            spec: Python module specification

        Returns:
            New module object, or None to use Python's default
        """
        if not spec.origin:
            raise ImportError(f"No origin specified for module {spec.name}")

        # If the input spec is a Dana spec, use it directly
        if isinstance(spec, ModuleSpec):
            dana_spec = spec
        else:
            # Get Dana spec from registry or create new one
            dana_spec = self.registry.get_spec(spec.name)
            if dana_spec is None:
                # Create new spec if not found
                dana_spec = ModuleSpec.from_py_spec(spec)
                self.registry.register_spec(dana_spec)

        # Create new module
        module = Module(__name__=spec.name, __file__=spec.origin)

        # Set up package attributes if this is a package
        if spec.origin.endswith("__init__.na"):
            module.__path__ = [str(Path(spec.origin).parent)]
            module.__package__ = spec.name
        elif "." in spec.name:
            # Submodule of a package
            module.__package__ = spec.name.rsplit(".", 1)[0]

        # Set spec
        module.__spec__ = dana_spec

        # Register module
        self.registry.register_module(module)

        return module

    def exec_module(self, module: Module) -> None:
        """Execute a module's code.

        Args:
            module: Module to execute
        """
        if not module.__file__:
            raise ImportError(f"No file path for module {module.__name__}")

        # Start loading
        self.registry.start_loading(module.__name__)
        try:
            # Read source
            source = Path(module.__file__).read_text()

            # Parse and compile
            from lark.exceptions import UnexpectedCharacters, UnexpectedToken

            parser = ParserCache.get_parser("dana")
            try:
                ast = parser.parse(source)
            except (UnexpectedToken, UnexpectedCharacters) as e:
                # Extract line number and source line from the error
                line_number = e.line
                source_line = source.splitlines()[line_number - 1] if line_number > 0 else None
                raise SyntaxError(str(e), module.__name__, module.__file__, line_number, source_line)

            # Execute
            from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
            from dana.core.lang.sandbox_context import SandboxContext

            interpreter = DanaInterpreter()
            context = SandboxContext()
            context._interpreter = interpreter  # Set the interpreter in the context

            # Set current module for relative import resolution
            context._current_module = module.__name__

            # Initialize module dict with context
            for key, value in module.__dict__.items():
                context.set_in_scope(key, value, scope="local")

            # Execute the module
            interpreter._execute(ast, context)

            # Update module dict with local scope
            module.__dict__.update(context.get_scope("local"))

            # Also include public scope variables in the module namespace
            # Public variables should be accessible as module attributes
            public_vars = context.get_scope("public")
            module.__dict__.update(public_vars)

            # Include system scope variables for agent functionality
            # This allows modules with system:agent_name and system:agent_description to be used as agents
            system_vars = context.get_scope("system")
            for key, value in system_vars.items():
                # Store system variables with their scope prefix for easy identification
                module.__dict__[f"system:{key}"] = value

            # Handle exports
            if hasattr(context, "_exports"):
                module.__exports__ = context._exports
            else:
                # If no explicit exports, export all local and public variables
                local_vars = set(context.get_scope("local").keys())
                public_vars_set = set(public_vars.keys())
                module.__exports__ = local_vars | public_vars_set

            # Remove internal variables from exports
            module.__exports__ = {name for name in module.__exports__ if not name.startswith("__")}

            # Post-process: Ensure DanaFunction objects can access each other for recursive calls
            self._setup_module_function_context(module, interpreter, context)

        finally:
            # Finish loading
            self.registry.finish_loading(module.__name__)

    def _setup_module_function_context(self, module: Module, interpreter: DanaInterpreter, context: SandboxContext) -> None:
        """Set up function contexts to enable recursive calls within the module.

        Args:
            module: The executed module
            interpreter: The interpreter used for execution
            context: The execution context
        """
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction
        from dana.core.lang.interpreter.functions.function_registry import FunctionMetadata, FunctionType

        # Find all DanaFunction objects in the module
        dana_functions = {}
        for name, obj in module.__dict__.items():
            if isinstance(obj, DanaFunction):
                dana_functions[name] = obj

        # If we have DanaFunction objects, set up their contexts properly
        if dana_functions and interpreter.function_registry:
            # Register all module functions in a temporary registry context
            # This allows recursive calls within the module
            for func_name, func_obj in dana_functions.items():
                try:
                    # Create metadata for the function
                    metadata = FunctionMetadata(source_file=module.__file__ or f"<module {module.__name__}>")
                    metadata.context_aware = True
                    metadata.is_public = True
                    metadata.doc = f"Module function from {module.__name__}.{func_name}"

                    # Register the function in the interpreter's registry
                    interpreter.function_registry.register(
                        name=func_name, func=func_obj, namespace="local", func_type=FunctionType.DANA, metadata=metadata, overwrite=True
                    )

                    # Ensure the function's execution context has access to the interpreter
                    if func_obj.context is not None:
                        if not hasattr(func_obj.context, "_interpreter") or func_obj.context._interpreter is None:
                            func_obj.context._interpreter = interpreter

                except Exception as e:
                    # Non-fatal - log and continue
                    print(f"Warning: Could not register module function {func_name}: {e}")

    def _find_module_file(self, module_name: str) -> Path | None:
        """Find a module file in the search paths.

        Args:
            module_name: Module name to find

        Returns:
            Path to module file if found, None otherwise
        """
        for search_path in self.search_paths:
            # Try .na file
            module_file = search_path / f"{module_name}.na"
            if module_file.exists():
                return module_file

            # Try package/__init__.na
            init_file = search_path / module_name / "__init__.na"
            if init_file.exists():
                return init_file

        return None
