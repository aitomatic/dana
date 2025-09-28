"""
Integration layer for the unified importing system.

This module provides a bridge between the new unified importing system
and the existing Dana importing infrastructure, allowing for gradual
migration and backward compatibility.
"""

from typing import Any, Optional, List, Tuple
from pathlib import Path
import sys

from .unified_import_handler import UnifiedImportHandler
from .core.resolver import ModuleResolver
from .core.loader import ModuleLoader as UnifiedModuleLoader
from .core.registry import ModuleRegistry as UnifiedModuleRegistry
from .core.lazy_loader import LazyLoader
from .utils.circular_detection import CircularImportDetector
from .patterns.from_import import FromImportHandler

# Import existing Dana components
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.runtime.modules.loader import ModuleLoader as DanaModuleLoader
from dana.registry.module_registry import ModuleRegistry as DanaModuleRegistry


class DanaImportingIntegration:
    """Integration layer between unified importing system and existing Dana system."""

    def __init__(self, existing_loader: Optional[DanaModuleLoader] = None,
                 existing_registry: Optional[DanaModuleRegistry] = None):
        """Initialize the integration layer.

        Args:
            existing_loader: Existing Dana module loader
            existing_registry: Existing Dana module registry
        """
        self.existing_loader = existing_loader
        self.existing_registry = existing_registry

        # Initialize unified system
        self.unified_handler = UnifiedImportHandler()

        # Create integration mappings
        self._module_mappings = {}
        self._integration_enabled = True

    def integrate_import_statement(self, module_name: str, context_name: str,
                                 context: SandboxContext, current_file: Optional[Path] = None) -> Any:
        """Integrate import statement handling.

        Args:
            module_name: The module name to import
            context_name: The name to bind in context
            context: The sandbox context
            current_file: The current file context

        Returns:
            The imported module
        """
        if not self._integration_enabled:
            return self._fallback_to_existing(module_name, context_name, context, current_file)

        try:
            # Use unified system for import
            module = self.unified_handler.import_module(module_name, current_file)

            # Set in context
            context.set_in_scope(context_name, module, scope="local")

            # Handle public variable merging (Dana-specific behavior)
            self._merge_public_variables(module, context)

            # Handle submodule namespace creation
            if "." in context_name:
                self._create_parent_namespaces(context_name, module, context)

            return module

        except Exception as e:
            # Fallback to existing system if unified system fails
            print(f"Unified import failed, falling back to existing system: {e}")
            return self._fallback_to_existing(module_name, context_name, context, current_file)

    def integrate_from_import(self, module_name: str, names: List[Tuple[str, Optional[str]]],
                             context: SandboxContext, current_file: Optional[Path] = None) -> None:
        """Integrate from-import statement handling.

        Args:
            module_name: The module to import from
            names: List of (name, alias) tuples to import
            context: The sandbox context
            current_file: The current file context
        """
        if not self._integration_enabled:
            return self._fallback_from_import(module_name, names, context, current_file)

        try:
            # Use unified system for from-import
            imports = self.unified_handler.from_import(module_name, names, current_file)

            # Set imported names in context
            for name, value in imports.items():
                context.set_in_scope(name, value, scope="local")

        except Exception as e:
            # Fallback to existing system if unified system fails
            print(f"Unified from-import failed, falling back to existing system: {e}")
            return self._fallback_from_import(module_name, names, context, current_file)

    def _fallback_to_existing(self, module_name: str, context_name: str,
                            context: SandboxContext, current_file: Optional[Path] = None) -> Any:
        """Fallback to existing Dana importing system.

        Args:
            module_name: The module name to import
            context_name: The name to bind in context
            context: The sandbox context
            current_file: The current file context

        Returns:
            The imported module
        """
        if self.existing_loader:
            # Use existing loader
            try:
                # This would need to be adapted based on the existing API
                # For now, we'll create a simple fallback
                return self._create_fallback_module(module_name, context_name)
            except Exception as e:
                raise Exception(f"Fallback import failed: {e}")
        else:
            raise Exception("No fallback system available")

    def _fallback_from_import(self, module_name: str, names: List[Tuple[str, Optional[str]]],
                            context: SandboxContext, current_file: Optional[Path] = None) -> None:
        """Fallback to existing Dana from-import system.

        Args:
            module_name: The module to import from
            names: List of (name, alias) tuples to import
            context: The sandbox context
            current_file: The current file context
        """
        if self.existing_loader:
            # Use existing from-import logic
            try:
                # This would need to be adapted based on the existing API
                for name, alias in names:
                    context_name = alias if alias else name
                    # Create a placeholder for now
                    context.set_in_scope(context_name, f"fallback_{name}", scope="local")
            except Exception as e:
                raise Exception(f"Fallback from-import failed: {e}")
        else:
            raise Exception("No fallback system available")

    def _create_fallback_module(self, module_name: str, context_name: str) -> Any:
        """Create a fallback module when unified system fails.

        Args:
            module_name: The module name
            context_name: The context name

        Returns:
            A fallback module object
        """
        class FallbackModule:
            def __init__(self, name: str):
                self.__name__ = name
                self.__file__ = None
                self.__package__ = name.rsplit('.', 1)[0] if '.' in name else None
                self.__dict__ = {}

            def __getattr__(self, name: str) -> Any:
                raise AttributeError(f"Fallback module '{self.__name__}' has no attribute '{name}'")

        return FallbackModule(context_name)

    def _merge_public_variables(self, module: Any, context: SandboxContext) -> None:
        """Merge public variables from module into global public scope.

        Args:
            module: The imported module
            context: The sandbox context
        """
        if hasattr(module, "__dict__"):
            for key, value in module.__dict__.items():
                if not key.startswith("_") and not callable(value):
                    # This is a public variable from the module
                    context.set_in_scope(key, value, scope="public")

    def _create_parent_namespaces(self, context_name: str, module: Any, context: SandboxContext) -> None:
        """Create parent namespaces for submodule imports.

        Args:
            context_name: The context name (e.g., "utils.text")
            module: The imported module
            context: The sandbox context
        """
        parts = context_name.split(".")
        if len(parts) > 1:
            # Create parent namespace
            parent_name = parts[0]
            if not context.has_in_scope(parent_name):
                # Create a namespace object
                namespace = type("Namespace", (), {"__name__": parent_name})()
                context.set_in_scope(parent_name, namespace, scope="local")

            # Set the submodule in the parent namespace
            parent = context.get_from_scope(parent_name)
            setattr(parent, parts[1], module)

    def enable_integration(self) -> None:
        """Enable the unified importing system."""
        self._integration_enabled = True

    def disable_integration(self) -> None:
        """Disable the unified importing system and use existing system."""
        self._integration_enabled = False

    def get_integration_status(self) -> dict:
        """Get the current integration status.

        Returns:
            Dictionary with integration status information
        """
        return {
            "integration_enabled": self._integration_enabled,
            "unified_system_available": self.unified_handler is not None,
            "existing_loader_available": self.existing_loader is not None,
            "existing_registry_available": self.existing_registry is not None,
            "module_mappings": len(self._module_mappings),
        }

    def clear_caches(self) -> None:
        """Clear all caches in both systems."""
        if self.unified_handler:
            self.unified_handler.clear_cache()

        if self.existing_registry:
            # Clear existing registry if it has a clear method
            if hasattr(self.existing_registry, 'clear'):
                self.existing_registry.clear()

    def get_module_info(self, module_name: str) -> dict:
        """Get information about a module from both systems.

        Args:
            module_name: The module name to query

        Returns:
            Dictionary with module information from both systems
        """
        info = {
            "module_name": module_name,
            "unified_system": {},
            "existing_system": {},
        }

        # Get info from unified system
        if self.unified_handler:
            try:
                info["unified_system"] = self.unified_handler.get_module_info(module_name)
            except Exception as e:
                info["unified_system"]["error"] = str(e)

        # Get info from existing system
        if self.existing_registry:
            try:
                info["existing_system"]["is_registered"] = self.existing_registry.is_module_registered(module_name)
                info["existing_system"]["is_loading"] = self.existing_registry.is_module_loading(module_name)
            except Exception as e:
                info["existing_system"]["error"] = str(e)

        return info



