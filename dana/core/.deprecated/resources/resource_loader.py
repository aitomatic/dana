"""
Resource Loader

This module provides dynamic resource discovery and loading from multiple sources:
- Built-in Python resource blueprints
- Dana stdlib resources (*.na files)
- User-defined resources from imported modules
"""

import importlib
import importlib.util
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# BaseResource removed - using ResourceInstance-only architecture
from .resource_registry import ResourceError, ResourceRegistry


@dataclass
class ResourcePlugin:
    """Represents a loaded resource plugin."""

    name: str
    kind: str
    source: str  # "builtin", "stdlib", "user"
    path: str | None = None
    blueprint_class: type | None = None
    factory_func: Callable | None = None
    metadata: dict[str, Any] = None


class ResourceLoader:
    """
    Loads and manages resource plugins from multiple sources.

    Provides a pluggable architecture for extending the resource system
    with new resource types from various locations.
    """

    def __init__(self, registry: ResourceRegistry):
        self.registry = registry
        self.plugins: dict[str, ResourcePlugin] = {}
        self.search_paths: list[Path] = []

        # Add default search paths
        self._add_default_search_paths()

    def _add_default_search_paths(self):
        """Add default search paths for resource discovery."""
        # Stdlib resources path
        stdlib_path = Path(__file__).parent.parent.parent / "libs" / "stdlib" / "resources"
        if stdlib_path.exists():
            self.search_paths.append(stdlib_path)

        # Check DANAPATH environment variable
        danapath = os.environ.get("DANAPATH", "")
        if danapath:
            for path_str in danapath.split(os.pathsep):
                path = Path(path_str) / "resources"
                if path.exists() and path not in self.search_paths:
                    self.search_paths.append(path)

    def add_search_path(self, path: Path):
        """Add a search path for resource discovery."""
        if path.exists() and path not in self.search_paths:
            self.search_paths.append(path)

    def load_core_plugins(self):
        """Load core ResourceInstance-based resources."""
        try:
            # Load clean ResourceInstance-based resources only
            from .plugins.llm_resource_clean import register_clean_llm_resource
            from .plugins.rag_resource_clean import register_clean_rag_resource

            # Register clean resources with factory
            register_clean_llm_resource()
            register_clean_rag_resource()
            print("Loaded clean resource: llm (ResourceInstance)")
            print("Loaded clean resource: rag (ResourceInstance)")

        except ImportError as e:
            print(f"Warning: Could not load clean resources: {e}")

    def load_stdlib_resources(self):
        """Load Dana stdlib resources from .na files."""
        # Note: Dana resources are now loaded by the Dana interpreter
        # when the startup file (dana/__init__.na) is executed.
        # This method is kept for Python resources only.

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            # Look for Python modules only (Dana resources are handled by the interpreter)
            for py_file in search_path.glob("*.py"):
                if py_file.name != "__init__.py":
                    self._load_python_resource(py_file)

    def _load_python_resource(self, py_file: Path):
        """Load a Python resource module."""
        module_name = py_file.stem

        # Check if it's already loaded
        if module_name in self.plugins:
            return

        try:
            # Load the Python module
            spec = importlib.util.spec_from_file_location(f"dana.resources.{module_name}", py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"dana.resources.{module_name}"] = module
                spec.loader.exec_module(module)

                # BaseResource-based discovery removed - ResourceInstance only
                pass

        except Exception as e:
            print(f"Warning: Failed to load Python resource from {py_file}: {e}")

    def register_plugin(self, plugin: ResourcePlugin):
        """Register a resource plugin."""
        self.plugins[plugin.name] = plugin

        # Register with the registry if it's a Python blueprint
        if plugin.blueprint_class:
            self.registry.register_blueprint(plugin.kind, plugin.blueprint_class)

    def register_user_resource(
        self,
        name: str,
        kind: str,
        blueprint_class: type | None = None,
        factory_func: Callable | None = None,
        metadata: dict[str, Any] = None,
    ):
        """
        Register a user-defined resource at runtime.

        This allows Dana code to register new resource types dynamically.
        """
        if not blueprint_class and not factory_func:
            raise ResourceError("Must provide either blueprint_class or factory_func")

        plugin = ResourcePlugin(
            name=name, kind=kind, source="user", blueprint_class=blueprint_class, factory_func=factory_func, metadata=metadata or {}
        )

        self.register_plugin(plugin)

    def create_resource_instance(self, kind: str, name: str, **kwargs):
        """
        Create a resource instance from a registered plugin.

        This handles both Python blueprint classes and Dana factory functions.
        """
        # Find the plugin
        plugin = None
        for p in self.plugins.values():
            if p.kind == kind:
                plugin = p
                break

        if not plugin:
            raise ResourceError(f"No plugin found for resource kind: {kind}")

        if plugin.blueprint_class:
            # Create from Python blueprint class
            return plugin.blueprint_class(name=name, kind=kind, **kwargs)
        elif plugin.factory_func:
            # Create from factory function
            return plugin.factory_func(name=name, kind=kind, **kwargs)
        else:
            raise ResourceError(f"Plugin {plugin.name} has no blueprint or factory")

    def list_plugins(self) -> list[ResourcePlugin]:
        """List all registered resource plugins."""
        return list(self.plugins.values())

    def get_plugin(self, name: str) -> ResourcePlugin | None:
        """Get a specific plugin by name."""
        return self.plugins.get(name)

    def get_plugin_metadata(self, name: str) -> dict[str, Any]:
        """Get metadata for a plugin."""
        plugin = self.get_plugin(name)
        if plugin:
            return {"name": plugin.name, "kind": plugin.kind, "source": plugin.source, "path": plugin.path, "metadata": plugin.metadata}
        return {}

    def load_all(self):
        """Load all resources from all sources."""
        self.load_core_plugins()
        self.load_stdlib_resources()
