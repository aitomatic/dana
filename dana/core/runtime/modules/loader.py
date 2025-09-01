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
from types import ModuleType
from typing import TYPE_CHECKING, cast

from dana.common.mixins.loggable import Loggable
from dana.core.lang.parser.utils.parsing_utils import ParserCache
from dana.registry.module_registry import ModuleRegistry

from .errors import ImportError, ModuleNotFoundError, SyntaxError
from .types import Module, ModuleSpec

if TYPE_CHECKING:
    from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
    from dana.core.lang.sandbox_context import SandboxContext


class ModuleLoader(Loggable, MetaPathFinder, Loader):
    """Loader responsible for finding and loading Dana modules."""

    def __init__(self, search_paths: list[str], registry: ModuleRegistry):
        """Initialize a new module loader.

        Args:
            search_paths: List of paths to search for modules
            registry: Module registry instance
        """
        # Initialize logging mixin
        Loggable.__init__(self)

        self.search_paths = [Path(p).resolve() for p in search_paths]
        self.registry = registry

    def find_spec(self, fullname: str, path: Sequence[str | bytes] | None = None, target: ModuleType | None = None) -> PyModuleSpec | None:
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
        # For internal use: extract importing module path from path if provided
        importing_module_path = None
        if path and isinstance(path, list) and len(path) > 0 and isinstance(path[0], str):
            # Check if the first element looks like a file path (internal convention)
            first_path = path[0]
            if first_path.startswith("__dana_importing_from__:"):
                importing_module_path = first_path[23:]  # Remove prefix

        return self._find_spec_with_context(fullname, importing_module_path)

    def _wrap_dana_spec(self, dana_spec: ModuleSpec) -> PyModuleSpec:
        """Create a Python ModuleSpec from a Dana ModuleSpec, copying key attributes."""
        py_spec = PyModuleSpec(name=dana_spec.name, loader=self, origin=dana_spec.origin)
        py_spec.has_location = dana_spec.has_location
        py_spec.submodule_search_locations = dana_spec.submodule_search_locations
        return py_spec

    def _create_and_register_spec(self, fullname: str, origin: Path) -> PyModuleSpec:
        """Create, package-setup, register a Dana ModuleSpec, and wrap it for Python import system."""
        dana_spec = ModuleSpec(name=fullname, loader=self, origin=str(origin))
        self._setup_package_attributes(dana_spec)
        self.registry.register_spec(dana_spec)
        return self._wrap_dana_spec(dana_spec)

    def _find_spec_with_context(self, fullname: str, importing_module_path: str | None = None) -> PyModuleSpec | None:
        """Find a module specification with optional context of importing module.

        Args:
            fullname: Fully qualified module name
            importing_module_path: Path of the module doing the import (if any)

        Returns:
            Module specification if found, None otherwise
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
                return self._wrap_dana_spec(dana_spec)
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
                            return self._create_and_register_spec(fullname, module_file)

                        # Also check for package/__init__.na in parent's search paths (legacy)
                        init_file = Path(search_path) / module_name / "__init__.na"
                        if init_file.is_file():
                            return self._create_and_register_spec(fullname, init_file)

                        # Also check for directory packages in parent's search paths (new)
                        package_dir = Path(search_path) / module_name
                        if package_dir.is_dir() and self._is_dana_package_directory(package_dir):
                            return self._create_and_register_spec(fullname, package_dir)
            except ModuleNotFoundError:
                pass  # Continue searching

        # Search for module file in search paths
        # First, try to find in the importing module's directory if available
        if importing_module_path:
            importing_dir = Path(importing_module_path).parent
            module_file = self._find_module_in_directory(module_name, importing_dir)
            if module_file is not None:
                return self._create_and_register_spec(fullname, module_file)

        # Then search in regular search paths
        module_file = self._find_module_file(module_name)
        if module_file is not None:
            return self._create_and_register_spec(fullname, module_file)

        # Module not found after checking all paths - return None to let Python handle it
        return None

    def _setup_package_attributes(self, spec: ModuleSpec) -> None:
        """Set up package attributes for a module spec.

        This allows __init__.na files, directory packages, and regular .na files
        to serve as packages if they have subdirectories with modules.

        Args:
            spec: Module specification to set up
        """
        if not spec.origin:
            return

        origin_path = Path(spec.origin)

        # Case 1: __init__.na files are always packages (legacy support)
        if origin_path.name == "__init__.na":
            spec.submodule_search_locations = [str(origin_path.parent)]
            if "." in spec.name:
                spec.parent = spec.name.rsplit(".", 1)[0]
        # Case 2: Directory packages (new: directories are packages)
        elif origin_path.is_dir():
            spec.submodule_search_locations = [str(origin_path)]
            if "." in spec.name:
                spec.parent = spec.name.rsplit(".", 1)[0]
        else:
            # Case 3: Regular .na files can also be packages if they have a directory with the same name
            # This enables a.b.na to serve as a package for a.b.c modules
            module_dir = origin_path.parent / origin_path.stem
            if module_dir.is_dir():
                # Check if the directory contains any .na files or subdirectories with __init__.na
                has_submodules = (
                    any(f.suffix == ".na" for f in module_dir.iterdir() if f.is_file())
                    or any((subdir / "__init__.na").exists() for subdir in module_dir.iterdir() if subdir.is_dir())
                    or any(self._is_dana_package_directory(subdir) for subdir in module_dir.iterdir() if subdir.is_dir())
                )
                if has_submodules:
                    spec.submodule_search_locations = [str(module_dir)]
                    if "." in spec.name:
                        spec.parent = spec.name.rsplit(".", 1)[0]

    def create_module(self, spec: PyModuleSpec) -> ModuleType | None:
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
        origin_path = Path(spec.origin)
        if spec.origin.endswith("__init__.na"):
            # Legacy __init__.na package
            module.__path__ = [str(origin_path.parent)]
            module.__package__ = spec.name
        elif origin_path.is_dir():
            # Directory package (new)
            module.__path__ = [str(origin_path)]
            module.__package__ = spec.name
        elif "." in spec.name:
            # Submodule of a package
            module.__package__ = spec.name.rsplit(".", 1)[0]

        # Set spec
        module.__spec__ = dana_spec

        # Register module
        self.registry.register_module(module)

        return cast(ModuleType, module)

    def exec_module(self, module: ModuleType) -> None:
        """Execute a module's code.

        Args:
            module: Module to execute
        """
        # We manage our own Module class; cast for type checking
        module_obj: Module = cast(Module, module)
        if not module_obj.__file__:
            raise ImportError(f"No file path for module {module_obj.__name__}")

        # Check for circular imports before starting to load
        if self.registry.is_module_loading(module_obj.__name__):
            from .errors import CircularImportError

            raise CircularImportError([module_obj.__name__])

        # Start loading lifecycle
        self.registry.start_loading(module_obj.__name__)
        try:
            origin_path = Path(module_obj.__file__)

            # Handle both directory packages and __init__.na files
            if origin_path.is_dir():
                # Directory package without __init__.na (namespace package)
                init_file = origin_path / "__init__.na"
                if not init_file.is_file():
                    # Namespace package: populate with available submodules
                    self._populate_namespace_package(module_obj, origin_path)
                    self.registry.finish_loading(module_obj.__name__)
                    return
                # Directory with __init__.na - populate before executing
                self._populate_package_with_submodules(module_obj, origin_path)
            elif origin_path.name == "__init__.na":
                # Package __init__.na file - populate the parent directory
                package_dir = origin_path.parent
                self._populate_package_with_submodules(module_obj, package_dir)

                # 2) Read and parse from __init__.na
                source = self._read_source(origin_path)
                ast = self._parse_source(source, module_obj.__name__, str(origin_path))

                # 3) Create execution context and seed it
                interpreter, context = self._create_execution_context(module_obj, origin_path)
                self._seed_context_from_module(context, module_obj)

                # 4) Execute AST
                self._execute_ast(interpreter, ast, context)

                # 4.5) Register receiver functions from AST
                self._register_receiver_functions_from_ast(ast, module_obj, context)

                # 5) Publish results back to module/public scopes
                public_vars = self._collect_public_vars(context)
                self._publish_scopes_to_module(module_obj, context, public_vars)
                self._merge_public_into_root(context, public_vars)
                self._expose_system_vars(module_obj, context)

                # 6) Determine and apply exports
                exports = self._determine_exports(module_obj, context, public_vars)
                self._apply_exports(module_obj, exports)

                # 7) Post-process: enable intra-module function calls and log
                self._setup_module_function_context(module_obj, interpreter, context)

                return

            # 1) Read and parse
            source = self._read_source(origin_path)
            ast = self._parse_source(source, module_obj.__name__, module_obj.__file__)

            # 2) Create execution context and seed it
            interpreter, context = self._create_execution_context(module_obj, origin_path)
            self._seed_context_from_module(context, module_obj)

            # 3) Execute AST
            self._execute_ast(interpreter, ast, context)

            # 3.5) Register receiver functions from AST
            self._register_receiver_functions_from_ast(ast, module_obj, context)

            # 4) Publish results back to module/public scopes
            public_vars = self._collect_public_vars(context)
            self._publish_scopes_to_module(module_obj, context, public_vars)
            self._merge_public_into_root(context, public_vars)
            self._expose_system_vars(module_obj, context)

            # 5) Determine and apply exports
            exports = self._determine_exports(module_obj, context, public_vars)
            self._apply_exports(module_obj, exports)

            # 6) Post-process: enable intra-module function calls and log
            self._setup_module_function_context(module_obj, interpreter, context)

        finally:
            # Finish loading
            self.registry.finish_loading(module_obj.__name__)

    # ===== Helper methods for exec_module =====

    def _read_source(self, origin_path: Path) -> str:
        """Read module source from disk."""
        return origin_path.read_text()

    def _parse_source(self, source: str, module_name: str, module_file: str | None):
        """Parse Dana source code into an AST, raising Dana SyntaxError on failure."""
        from lark.exceptions import UnexpectedCharacters, UnexpectedToken

        parser = ParserCache.get_parser("dana")
        try:
            return parser.parse(source)
        except (UnexpectedToken, UnexpectedCharacters) as e:
            # Extract line number and source line from the error
            line_number = e.line
            source_line = source.splitlines()[line_number - 1] if line_number > 0 else None
            raise SyntaxError(str(e), module_name, module_file, line_number, source_line)

    def _create_execution_context(self, module: Module, origin_path: Path) -> tuple[DanaInterpreter, SandboxContext]:
        """Create a fresh interpreter + context and set module/package metadata for relative imports."""
        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
        from dana.core.lang.sandbox_context import SandboxContext

        interpreter = DanaInterpreter()
        context = SandboxContext()
        context._interpreter = interpreter  # Bind interpreter

        # Set the current file being executed (used for error reporting AND Python import resolution)
        if origin_path:
            context.error_context.set_file(str(origin_path))

        # Set current module and package for relative import resolution
        context._current_module = module.__name__
        if origin_path and (origin_path.name == "__init__.na" or origin_path.is_dir()):
            # __init__.na file or directory package - current package is the module itself
            context._current_package = module.__name__
        elif "." in module.__name__:
            # Regular module - current package is parent package
            context._current_package = module.__name__.rsplit(".", 1)[0]
        else:
            # Top-level module has no package
            context._current_package = ""

        return interpreter, context

    def _seed_context_from_module(self, context: SandboxContext, module: Module) -> None:
        """Copy any pre-existing module attributes into the local scope before execution."""
        for key, value in module.__dict__.items():
            context.set_in_scope(key, value, scope="local")

    def _execute_ast(self, interpreter: DanaInterpreter, ast, context: SandboxContext) -> None:
        """Execute parsed AST inside the given context."""
        interpreter.execute_program(ast, context)

    def _collect_public_vars(self, context: SandboxContext) -> dict[str, object]:
        """Collect public scope variables from the execution context."""
        return context.get_scope("public")

    def _publish_scopes_to_module(self, module: Module, context: SandboxContext, public_vars: dict[str, object]) -> None:
        """Publish local and public scopes to the module namespace."""
        module.__dict__.update(context.get_scope("local"))
        module.__dict__.update(public_vars)

    def _merge_public_into_root(self, context: SandboxContext, public_vars: dict[str, object]) -> None:
        """Merge module public variables into the root context's public scope."""
        root_context: SandboxContext = context
        # Walk up to the root context explicitly
        while True:
            parent = getattr(root_context, "parent_context", None)
            if parent is None:
                break
            root_context = parent
        root_context._state["public"].update(public_vars)

    def _expose_system_vars(self, module: Module, context: SandboxContext) -> None:
        """Expose system scope variables as namespaced attributes on the module."""
        system_vars = context.get_scope("system")
        for key, value in system_vars.items():
            module.__dict__[f"system:{key}"] = value

    def _determine_exports(
        self,
        module: Module,
        context: SandboxContext,
        public_vars: dict[str, object],
    ) -> set[str]:
        """Determine the module's export set from context/module/defaults, without dunder filtering."""
        exports: set[str] | None = None

        # 1) Prefer explicit exports captured on the context during execution
        if hasattr(context, "_exports"):
            try:
                ctx_exports = set(context._exports)  # type: ignore[attr-defined]
                if ctx_exports:
                    exports = ctx_exports
            except Exception:
                exports = None

        # 2) Otherwise, honor a module-defined __exports__ if present and non-empty iterable
        if exports is None and "__exports__" in module.__dict__:
            raw_exports = module.__dict__["__exports__"]
            if isinstance(raw_exports, set | list | tuple):
                try:
                    mod_exports = set(raw_exports)
                    if mod_exports:
                        exports = mod_exports
                except Exception:
                    exports = None

        # 3) Final fallback: auto-derive from locals ∪ public (skip underscore)
        if exports is None:
            local_vars = set(context.get_scope("local").keys())
            public_vars_set = set(public_vars.keys())
            all_vars = local_vars | public_vars_set
            exports = {name for name in all_vars if not name.startswith("_")}

        # Defensive fallback: if still empty, derive from module namespace (exclude colon-names)
        if not exports:
            exports = {name for name in module.__dict__.keys() if not name.startswith("_") and ":" not in name}

        return exports

    def _apply_exports(self, module: Module, exports: set[str]) -> None:
        """Apply the export set to the module, filtering out double-underscore names."""
        module.__exports__ = {name for name in exports if not name.startswith("__")}  # type: ignore[assignment]

    def _setup_module_function_context(self, module: Module, interpreter: DanaInterpreter, context: SandboxContext) -> None:
        """Set up function contexts to enable recursive calls within the module.

        Args:
            module: The executed module
            interpreter: The interpreter used for execution
            context: The execution context
        """
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction
        from dana.registry.function_registry import FunctionMetadata, FunctionType

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

                    # Ensure the function has access to the interpreter
                    if func_obj.context:
                        if not hasattr(func_obj.context, "_interpreter") or func_obj.context._interpreter is None:
                            func_obj.context._interpreter = interpreter

                except Exception as e:
                    # Non-fatal - log and continue
                    print(f"Warning: Could not register module function {func_name}: {e}")

    def _find_module_in_directory(self, module_name: str, directory: Path) -> Path | None:
        """Find a module file in a specific directory.

        Args:
            module_name: Module name to find
            directory: Directory to search in

        Returns:
            Path to module file if found, None otherwise
        """
        # Try .na file
        module_file = directory / f"{module_name}.na"
        if module_file.exists():
            return module_file

        # Try package/__init__.na (legacy support)
        init_file = directory / module_name / "__init__.na"
        if init_file.exists():
            return init_file

        # Try directory package (new: directories containing .na files are packages)
        package_dir = directory / module_name
        if package_dir.is_dir() and self._is_dana_package_directory(package_dir):
            return package_dir

        return None

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

            # Try package/__init__.na (legacy support)
            init_file = search_path / module_name / "__init__.na"
            if init_file.exists():
                return init_file

            # Try directory package (new: directories containing .na files are packages)
            package_dir = search_path / module_name
            if package_dir.is_dir() and self._is_dana_package_directory(package_dir):
                return package_dir

        return None

    def _is_dana_package_directory(self, directory: Path) -> bool:
        """Check if a directory qualifies as a Dana package.

        A directory is considered a Dana package if it contains:
        - At least one .na file, OR
        - At least one subdirectory that is also a Dana package

        Args:
            directory: Directory to check

        Returns:
            True if directory is a Dana package, False otherwise
        """
        if not directory.is_dir():
            return False

        # Check for direct .na files
        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".na":
                return True

        # Check for subdirectory packages
        for item in directory.iterdir():
            if item.is_dir():
                # Check if subdirectory has __init__.na (legacy packages)
                if (item / "__init__.na").exists():
                    return True
                # Check if subdirectory is itself a Dana package (recursive)
                if self._is_dana_package_directory(item):
                    return True

        return False

    def _populate_namespace_package(self, module_obj: Module, package_dir: Path) -> None:
        """Populate a namespace package with its available submodules.

        This method finds all immediate submodules in a namespace package directory
        and creates lazy-loading attributes for them on the namespace package module.

        Args:
            module_obj: The namespace package module to populate
            package_dir: Directory containing the namespace package
        """
        # Find all immediate submodules
        for item in package_dir.iterdir():
            if item.is_file() and item.suffix == ".na":
                # Direct .na file submodule
                submodule_name = item.stem
                full_submodule_name = f"{module_obj.__name__}.{submodule_name}"

                # Create a lazy-loading property for this submodule
                self._add_lazy_submodule(module_obj, submodule_name, full_submodule_name)

            elif item.is_dir():
                # Check if this directory is a package (has __init__.na or is namespace package)
                submodule_name = item.name
                full_submodule_name = f"{module_obj.__name__}.{submodule_name}"

                if (item / "__init__.na").exists() or self._is_dana_package_directory(item):
                    # Create a lazy-loading property for this subpackage
                    self._add_lazy_submodule(module_obj, submodule_name, full_submodule_name)

    def _add_lazy_submodule(self, module_obj: Module, submodule_name: str, full_submodule_name: str) -> None:
        """Add a lazy-loading submodule attribute to a namespace package.

        Args:
            module_obj: The namespace package module
            submodule_name: Name of the submodule (local name)
            full_submodule_name: Fully qualified name of the submodule
        """

        # Create a property that loads the submodule on first access
        def old_get_submodule():
            # Try to get from cache first
            if hasattr(module_obj, f"__{submodule_name}_cached__"):
                return getattr(module_obj, f"__{submodule_name}_cached__")

            # Load the submodule
            try:
                spec = self.find_spec(full_submodule_name)
                if spec is None:
                    raise AttributeError(f"Submodule '{submodule_name}' not found in namespace package '{module_obj.__name__}'")

                submodule = self.create_module(spec)
                if submodule is None:
                    raise AttributeError(f"Could not create submodule '{submodule_name}'")

                self.exec_module(submodule)

                # Cache the result
                setattr(module_obj, f"__{submodule_name}_cached__", submodule)
                return submodule

            except Exception as e:
                raise AttributeError(f"Error loading submodule '{submodule_name}': {e}") from e

        # Create a getter function for the submodule
        def get_submodule():
            try:
                # Use the import machinery to load the submodule
                submodule_spec = self.find_spec(full_submodule_name)
                if submodule_spec:
                    submodule = self.create_module(submodule_spec)
                    self.exec_module(submodule)
                    return submodule
                else:
                    raise ImportError(f"No module named '{full_submodule_name}'")
            except Exception as e:
                # Provide better error context for circular import issues
                if "circular import" in str(e).lower() or "partially initialized" in str(e).lower():
                    raise AttributeError(f"Circular import detected while loading '{submodule_name}': {e}") from e
                else:
                    raise AttributeError(f"Error loading submodule '{submodule_name}': {e}") from e

        # For now, always use lazy loading to avoid infinite loops
        # The import handler will handle the actual loading when needed
        def lazy_loader():
            return get_submodule()

        lazy_loader.__NAME__ = "__LAZY_MODULE_LOADER__"

        # Don't execute immediately during population to avoid circular loops
        # Just make the module available for import by setting it as an attribute
        # but defer actual execution until import time
        setattr(module_obj, submodule_name, lazy_loader)
        self.debug(f"Created lazy loader for {module_obj.__name__}.{submodule_name}")

    def _populate_package_with_submodules(self, module_obj: Module, package_dir: Path) -> None:
        """Populate a regular package (with __init__.na) with its available submodules.

        This method is similar to _populate_namespace_package but for regular packages.
        It ensures that submodules are available as attributes before the __init__.na
        file is executed, preventing import failures during package initialization.

        Args:
            module_obj: The package module to populate
            package_dir: Directory containing the package
        """
        # Reuse the same logic as namespace packages
        self._populate_namespace_package(module_obj, package_dir)

    def _register_receiver_functions_from_ast(self, ast, module_obj: Module, context) -> None:
        """Extract and register receiver functions from module AST.

        This method scans the AST for receiver functions (MethodDefinition nodes)
        and registers them in the unified FUNCTION_REGISTRY so they can be called
        as methods on struct instances.

        Args:
            ast: The parsed AST of the module
            module_obj: The module object being loaded
            context: The execution context
        """
        from dana.core.lang.ast import MethodDefinition

        try:
            # Scan through all statements in the AST
            for statement in ast.statements:
                if isinstance(statement, MethodDefinition):
                    self._register_receiver_function(statement, module_obj, context)

        except Exception as e:
            # Log warning but don't fail module loading
            self.warning(f"Failed to register receiver functions from module '{module_obj.__name__}': {e}")

    def _register_receiver_function(self, method_def, module_obj: Module, context) -> None:
        """Register a single receiver function in the struct function registry.

        Args:
            method_def: The method definition AST node
            module_obj: The module object being loaded
            context: The execution context
        """
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction
        from dana.registry import FUNCTION_REGISTRY

        try:
            # Extract receiver type from the method definition
            receiver_param = method_def.receiver
            receiver_type_str = receiver_param.type_hint.name if receiver_param.type_hint else None

            if not receiver_type_str:
                self.warning(f"Method definition in module '{module_obj.__name__}' has no receiver type")
                return

            # Parse union types (e.g., "Point | Circle | Rectangle")
            receiver_types = [t.strip() for t in receiver_type_str.split("|") if t.strip()]

            # Extract method name
            method_name = method_def.name.name

            # Create a function that can be called as a method
            def method_function(receiver, *args, **kwargs):
                # Get the function from the module context
                func = context.get(method_name)
                if func is None:
                    raise AttributeError(f"Method '{method_name}' not found in module '{module_obj.__name__}'")

                # Call the function with receiver as first argument
                if isinstance(func, DanaFunction):
                    return func.execute(context, receiver, *args, **kwargs)
                else:
                    return func(receiver, *args, **kwargs)

            # Register the method for all receiver types
            for receiver_type in receiver_types:
                FUNCTION_REGISTRY.register_struct_function(receiver_type, method_name, method_function)
                self.debug(f"Registered receiver function '{method_name}' for type '{receiver_type}' in module '{module_obj.__name__}'")

            self.debug(
                f"Successfully registered receiver function '{method_name}' for type '{receiver_type_str}' in module '{module_obj.__name__}'"
            )

        except Exception as e:
            self.warning(f"Failed to register receiver function '{method_def.name.name}' from module '{module_obj.__name__}': {e}")
