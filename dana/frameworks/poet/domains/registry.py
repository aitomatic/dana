"""
Domain Registry for POET Plugin System

Handles discovery, loading, and management of domain templates with support for:
- Built-in domains (computation, llm_optimization, etc.)
- User-defined plugins from multiple search paths
- Domain inheritance (parent:child syntax)
- On-demand loading for performance
- Smart error handling with suggestions
"""

import difflib
import importlib.util
from pathlib import Path

from dana.common.utils.logging import DANA_LOGGER

from .base import DomainTemplate


class DomainNotFoundError(Exception):
    """Raised when a requested domain cannot be found"""

    pass


class DomainRegistry:
    """
    Central registry for domain templates with plugin discovery and inheritance support.

    Features:
    - On-demand loading of domains
    - Multiple search paths for user plugins
    - Domain inheritance with parent:child syntax
    - Smart suggestions for typos
    - Comprehensive error messages
    """

    def __init__(self):
        self._domains: dict[str, DomainTemplate] = {}
        self._builtin_loaded = False
        self._plugin_paths_searched: set[Path] = set()

        # Search paths for plugins (order matters - first found wins)
        self._search_paths = [
            Path(__file__).parent,  # Built-in domains
            Path.home() / ".dana" / "poet" / "domains",  # User home plugins
            Path.cwd() / ".poet" / "domains",  # Project-local plugins
        ]

        # Add any paths from environment variables
        poet_plugin_path = Path.cwd() / "dana" / "poet" / "domains" / "plugins"
        if poet_plugin_path.exists():
            self._search_paths.append(poet_plugin_path)

    def get_domain(self, name: str) -> DomainTemplate:
        """
        Get a domain template by name, with support for inheritance syntax.

        Args:
            name: Domain name, e.g. "computation" or "computation:scientific"

        Returns:
            DomainTemplate instance

        Raises:
            DomainNotFoundError: If domain cannot be found
        """
        # Handle inheritance syntax: "parent:child"
        if ":" in name:
            parent_name, child_name = name.split(":", 1)
            return self._get_inherited_domain(parent_name, child_name)

        # Simple domain lookup
        if name not in self._domains:
            self._load_domain(name)

        if name not in self._domains:
            self._raise_domain_not_found(name)

        return self._domains[name]

    def _get_inherited_domain(self, parent_name: str, child_name: str) -> DomainTemplate:
        """Create an inherited domain instance"""
        # Get parent domain
        parent_domain = self.get_domain(parent_name)

        # Get child domain class and instantiate with parent
        child_domain = self.get_domain(child_name)

        # Create new instance with inheritance
        child_class = type(child_domain)
        inherited_domain = child_class(parent=parent_domain)
        inherited_domain.name = f"{parent_name}:{child_name}"

        return inherited_domain

    def _load_domain(self, name: str) -> None:
        """Load a domain on first access"""
        DANA_LOGGER.debug(f"Loading domain '{name}'")

        # Load built-ins first if not already loaded
        if not self._builtin_loaded:
            self._load_builtin_domains()

        # Try plugins if not found in built-ins
        if name not in self._domains:
            self._discover_and_load_plugin(name)

    def _load_builtin_domains(self) -> None:
        """Load built-in domains"""
        if self._builtin_loaded:
            return

        DANA_LOGGER.debug("Loading built-in domains")

        try:
            # Import built-in domain modules
            from .computation import ComputationDomain
            from .llm_optimization import LLMOptimizationDomain
            from .ml_monitoring import MLMonitoringDomain
            from .prompt_optimization import PromptOptimizationDomain

            # Register built-in domains
            self._domains["computation"] = ComputationDomain()
            self._domains["llm_optimization"] = LLMOptimizationDomain()
            self._domains["ml_monitoring"] = MLMonitoringDomain()
            self._domains["prompt_optimization"] = PromptOptimizationDomain()

            DANA_LOGGER.debug(f"Loaded {len(self._domains)} built-in domains")

        except ImportError as e:
            DANA_LOGGER.warning(f"Failed to load some built-in domains: {e}")

        self._builtin_loaded = True

    def _discover_and_load_plugin(self, name: str) -> None:
        """Discover and load a plugin domain from search paths"""
        for search_path in self._search_paths:
            if search_path in self._plugin_paths_searched:
                continue

            if not search_path.exists():
                continue

            # Try loading as single file: domain_name.py
            plugin_file = search_path / f"{name}.py"
            if plugin_file.exists():
                self._load_plugin_file(plugin_file, name)
                break

            # Try loading as package: domain_name/__init__.py
            plugin_dir = search_path / name
            if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                self._load_plugin_module(plugin_dir, name)
                break

        # Mark this path as searched
        for path in self._search_paths:
            if path.exists():
                self._plugin_paths_searched.add(path)

    def _load_plugin_file(self, plugin_file: Path, name: str) -> None:
        """Load a domain from a single Python file"""
        try:
            DANA_LOGGER.debug(f"Loading plugin from file: {plugin_file}")

            spec = importlib.util.spec_from_file_location(f"poet_domain_{name}", plugin_file)
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for domain class
            domain_class = self._find_domain_class_in_module(module, name)
            if domain_class:
                self._domains[name] = domain_class()
                DANA_LOGGER.info(f"Loaded plugin domain '{name}' from {plugin_file}")

        except Exception as e:
            DANA_LOGGER.warning(f"Failed to load plugin {plugin_file}: {e}")

    def _load_plugin_module(self, plugin_dir: Path, name: str) -> None:
        """Load a domain from a Python package directory"""
        try:
            DANA_LOGGER.debug(f"Loading plugin from package: {plugin_dir}")

            spec = importlib.util.spec_from_file_location(f"poet_domain_{name}", plugin_dir / "__init__.py")
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for domain class
            domain_class = self._find_domain_class_in_module(module, name)
            if domain_class:
                self._domains[name] = domain_class()
                DANA_LOGGER.info(f"Loaded plugin domain '{name}' from {plugin_dir}")

        except Exception as e:
            DANA_LOGGER.warning(f"Failed to load plugin package {plugin_dir}: {e}")

    def _find_domain_class_in_module(self, module, name: str) -> type[DomainTemplate] | None:
        """Find the domain class in a loaded module"""
        # Look for class ending with "Domain"
        domain_class_name = f"{name.title().replace('_', '')}Domain"

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, DomainTemplate) and attr != DomainTemplate and attr_name == domain_class_name:
                return attr

        # Fallback: look for any DomainTemplate subclass
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, DomainTemplate) and attr != DomainTemplate:
                return attr

        return None

    def _raise_domain_not_found(self, name: str) -> None:
        """Raise a helpful error with suggestions"""
        available_domains = self.list_domains()

        # Try fuzzy matching for suggestions
        suggestions = difflib.get_close_matches(name, available_domains, n=3, cutoff=0.6)

        error_msg = f"Unknown domain '{name}'."

        if suggestions:
            error_msg += f" Did you mean: {', '.join(suggestions)}?"

        error_msg += f"\n\nAvailable domains: {', '.join(available_domains)}"

        # Add inheritance help
        if ":" not in name:
            error_msg += "\n\nFor inheritance, use 'parent:child' syntax (e.g., 'computation:scientific')"

        # Add plugin development help
        error_msg += "\n\nTo create a custom domain, see: docs/poet/custom-domains.md"
        error_msg += f"\nPlugin search paths: {[str(p) for p in self._search_paths]}"

        raise DomainNotFoundError(error_msg)

    def list_domains(self) -> list[str]:
        """List all available domain names"""
        # Ensure built-ins are loaded
        if not self._builtin_loaded:
            self._load_builtin_domains()

        return sorted(self._domains.keys())

    def list_all_domains(self) -> dict[str, list[dict[str, str]]]:
        """List all domains organized by category"""
        domains = {"Built-in": [], "User Plugins": []}

        builtin_names = {"computation", "llm_optimization", "ml_monitoring", "prompt_optimization"}

        for name in self.list_domains():
            domain_info = {"name": name, "parent": None}

            if name in builtin_names:
                domains["Built-in"].append(domain_info)
            else:
                domains["User Plugins"].append(domain_info)

        return domains

    def register_domain(self, name: str, domain: DomainTemplate) -> None:
        """Register a domain programmatically"""
        self._domains[name] = domain
        DANA_LOGGER.info(f"Registered domain '{name}': {type(domain).__name__}")

    def has_domain(self, name: str) -> bool:
        """Check if a domain exists without loading it"""
        if name in self._domains:
            return True

        # Quick check for built-ins
        builtin_names = {"computation", "llm_optimization", "ml_monitoring", "prompt_optimization"}
        if name in builtin_names:
            return True

        # Check if plugin files exist
        for search_path in self._search_paths:
            if not search_path.exists():
                continue

            plugin_file = search_path / f"{name}.py"
            plugin_dir = search_path / name / "__init__.py"

            if plugin_file.exists() or plugin_dir.exists():
                return True

        return False

    def suggest_domains(self, name: str) -> list[str]:
        """Get domain suggestions for a given name"""
        available = self.list_domains()
        suggestions = difflib.get_close_matches(name, available, n=5, cutoff=0.4)

        # Add inheritance suggestions if applicable
        if ":" in name:
            parent, child = name.split(":", 1)
            if parent in available:
                child_suggestions = difflib.get_close_matches(child, available, n=3, cutoff=0.4)
                for child_suggestion in child_suggestions:
                    suggestions.append(f"{parent}:{child_suggestion}")

        return suggestions


# Global convenience function for decorator registration
def register_domain(name: str, domain_template: DomainTemplate | None = None):
    """
    Register a domain globally, either as decorator or function call.

    Usage:
        # As decorator
        @register_domain("my_domain")
        class MyDomain(DomainTemplate):
            pass

        # As function call
        register_domain("my_domain", MyDomain())
    """

    def decorator(cls):
        from . import get_registry

        registry = get_registry()
        registry.register_domain(name, cls())
        return cls

    if domain_template is not None:
        # Function call usage
        from . import get_registry

        registry = get_registry()
        registry.register_domain(name, domain_template)
        return domain_template
    else:
        # Decorator usage
        return decorator
