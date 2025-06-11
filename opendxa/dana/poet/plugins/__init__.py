"""
POET Plugin System

Provides a comprehensive plugin architecture for domain-specific intelligence
in the POET (Perceive-Operate-Enforce-Train) framework.
"""

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from opendxa.common.utils.logging import DXA_LOGGER

# Import base classes
from .base import POETPlugin


class PluginRegistry:
    """
    Central registry for POET plugins with automatic discovery and management.

    Supports multiple plugin directories and lazy loading for optimal performance.
    """

    def __init__(self):
        self._plugins: Dict[str, POETPlugin] = {}
        self._plugin_classes: Dict[str, Type[POETPlugin]] = {}
        self._plugin_paths: Dict[str, str] = {}
        self._search_paths: List[Path] = []
        self._discovered = False

    def add_search_path(self, path: str | Path) -> None:
        """Add a directory to search for plugins."""
        path_obj = Path(path)
        if path_obj.exists() and path_obj.is_dir():
            self._search_paths.append(path_obj)
            DXA_LOGGER.debug(f"Added plugin search path: {path_obj}")
        else:
            DXA_LOGGER.warning(f"Plugin search path does not exist: {path_obj}")

    def discover_plugins(self) -> int:
        """
        Discover all plugins in search paths.

        Returns:
            int: Number of plugins discovered
        """
        if not self._search_paths:
            self._initialize_default_paths()

        discovered_count = 0

        for search_path in self._search_paths:
            if not search_path.exists():
                continue

            DXA_LOGGER.debug(f"Scanning for plugins in: {search_path}")

            # Find all *_plugin.py files
            for plugin_file in search_path.glob("*_plugin.py"):
                try:
                    self._load_plugin_file(plugin_file, search_path)
                    discovered_count += 1
                except Exception as e:
                    DXA_LOGGER.warning(f"Failed to load plugin file {plugin_file}: {e}")

        self._discovered = True
        DXA_LOGGER.info(f"Discovered {discovered_count} plugins")
        return discovered_count

    def get_plugin(self, name: str) -> Optional[POETPlugin]:
        """
        Get a plugin instance by name (lazy loading).

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        if not self._discovered:
            self.discover_plugins()

        # Return cached instance if available
        if name in self._plugins:
            return self._plugins[name]

        # Create new instance if class is available
        if name in self._plugin_classes:
            try:
                plugin_instance = self._plugin_classes[name]()
                self._plugins[name] = plugin_instance
                DXA_LOGGER.debug(f"Loaded plugin: {name}")
                return plugin_instance
            except Exception as e:
                DXA_LOGGER.error(f"Failed to instantiate plugin {name}: {e}")
                return None

        return None

    def list_plugins(self) -> List[str]:
        """Get list of available plugin names."""
        if not self._discovered:
            self.discover_plugins()
        return list(self._plugin_classes.keys())

    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific plugin."""
        plugin = self.get_plugin(name)
        if plugin:
            return plugin.get_plugin_info()
        return None

    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin and cleanup its resources.

        Args:
            name: Plugin name

        Returns:
            bool: True if successfully unloaded
        """
        if name in self._plugins:
            try:
                self._plugins[name].cleanup()
                del self._plugins[name]
                DXA_LOGGER.debug(f"Unloaded plugin: {name}")
                return True
            except Exception as e:
                DXA_LOGGER.error(f"Failed to unload plugin {name}: {e}")
                return False
        return False

    def reload_plugin(self, name: str) -> bool:
        """
        Reload a plugin from disk.

        Args:
            name: Plugin name

        Returns:
            bool: True if successfully reloaded
        """
        if name in self._plugin_paths:
            # Unload existing instance
            self.unload_plugin(name)

            # Remove from class registry
            if name in self._plugin_classes:
                del self._plugin_classes[name]

            # Reload from file
            try:
                plugin_path = Path(self._plugin_paths[name])
                search_path = plugin_path.parent
                self._load_plugin_file(plugin_path, search_path)
                DXA_LOGGER.info(f"Reloaded plugin: {name}")
                return True
            except Exception as e:
                DXA_LOGGER.error(f"Failed to reload plugin {name}: {e}")
                return False
        return False

    def _initialize_default_paths(self) -> None:
        """Initialize default plugin search paths."""

        # 1. Built-in plugins (current directory)
        current_dir = Path(__file__).parent
        self.add_search_path(current_dir)

        # 2. User plugins directory
        user_plugins = Path.home() / ".opendxa" / "poet" / "plugins"
        if user_plugins.exists():
            self.add_search_path(user_plugins)

        # 3. Project-local plugins
        project_plugins = Path.cwd() / ".poet" / "plugins"
        if project_plugins.exists():
            self.add_search_path(project_plugins)

        # 4. Environment variable paths
        env_paths = os.environ.get("POET_PLUGIN_DIRS", "")
        if env_paths:
            for path in env_paths.split(os.pathsep):
                if path.strip():
                    self.add_search_path(path.strip())

    def _load_plugin_file(self, plugin_file: Path, search_path: Path) -> None:
        """Load a plugin from a Python file."""
        module_name = plugin_file.stem

        # Create module spec and load
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {plugin_file}")

        module = importlib.util.module_from_spec(spec)

        # Add to sys.modules temporarily for proper import resolution
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)

            # Find POETPlugin subclasses in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, POETPlugin) and attr != POETPlugin:
                    # Create plugin instance to get its name
                    try:
                        temp_instance = attr()
                        plugin_name = temp_instance.get_plugin_name()

                        # Store class for lazy loading
                        self._plugin_classes[plugin_name] = attr
                        self._plugin_paths[plugin_name] = str(plugin_file)

                        DXA_LOGGER.debug(f"Registered plugin class: {plugin_name} from {plugin_file}")

                        # Clean up temporary instance
                        temp_instance.cleanup()

                    except Exception as e:
                        DXA_LOGGER.warning(f"Failed to register plugin class {attr_name}: {e}")

        finally:
            # Clean up sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]


# Global plugin registry instance
PLUGIN_REGISTRY = PluginRegistry()


# Export public interface
__all__ = ["POETPlugin", "PluginRegistry", "PLUGIN_REGISTRY"]
