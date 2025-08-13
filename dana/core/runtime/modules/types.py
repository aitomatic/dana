"""
Dana Dana Module System - Core Types

This module defines the core types for Dana's module system, including module specifications,
module objects, and related data structures.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass, field
from importlib.machinery import ModuleSpec as PyModuleSpec
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dana.core.runtime.modules.loader import ModuleLoader


@dataclass
class ModuleSpec:
    """Specification for a module, used during import."""

    name: str  # Fully qualified module name
    loader: "ModuleLoader"  # Loader instance for this module
    origin: str | None  # File path or description of origin
    cache: dict[str, Any] = field(default_factory=dict)  # Cache data

    # Optional fields
    parent: str | None = None  # Parent package name
    has_location: bool = True  # Whether module has a concrete file location
    submodule_search_locations: list[str] | None = None  # For packages

    def __post_init__(self) -> None:
        """Set up package-specific attributes."""
        # Set has_location based on origin
        self.has_location = bool(self.origin)

        # Set up package attributes
        if self.origin and Path(self.origin).name == "__init__.na":
            self.submodule_search_locations = [str(Path(self.origin).parent)]
            if "." in self.name:
                self.parent = self.name.rsplit(".", 1)[0]

    @classmethod
    def from_py_spec(cls, py_spec: PyModuleSpec) -> "ModuleSpec":
        """Create a Dana ModuleSpec from a Python ModuleSpec.

        Args:
            py_spec: Python module specification

        Returns:
            Dana module specification
        """
        # Note: This method would need proper loader conversion in a real implementation
        from typing import cast

        return cls(
            name=py_spec.name,
            loader=cast("ModuleLoader", py_spec.loader),  # Type: ignore - loader conversion needed
            origin=py_spec.origin,
            has_location=py_spec.has_location,
            submodule_search_locations=py_spec.submodule_search_locations,
        )


class Module:
    """Base class for Dana modules."""

    def __init__(self, __name__: str, __file__: str | None = None):
        """Initialize a new module.

        Args:
            __name__: Module name
            __file__: Optional file path
        """
        # Initialize internal state
        object.__setattr__(self, "_dict", {})

        # Initialize module attributes
        self._dict.update(
            {
                "__name__": __name__,
                "__file__": __file__,
                "__package__": "",  # Will be set properly later
                "__spec__": None,  # Set by loader
                "__path__": None,  # Set for packages
                "__dana_version__": "",  # Dana version compatibility
                "__exports__": set(),  # Explicitly exported symbols
                "__doc__": "",  # Module documentation
            }
        )

        # Set package name
        if __file__ and Path(__file__).name == "__init__.na":
            self._dict["__package__"] = __name__
        elif "." in __name__:
            self._dict["__package__"] = __name__.rsplit(".", 1)[0]

    def __setattr__(self, name: str, value: Any) -> None:
        """Set module attribute.

        Args:
            name: Attribute name
            value: Attribute value
        """
        if name == "_dict":
            object.__setattr__(self, name, value)
        else:
            self._dict[name] = value

    def __getattr__(self, name: str) -> Any:
        """Get module attribute.

        Args:
            name: Attribute name

        Returns:
            Attribute value

        Raises:
            AttributeError: If attribute not found
        """
        try:
            return self._dict[name]
        except KeyError:
            raise AttributeError(f"Module '{self._dict['__name__']}' has no attribute '{name}'")

    @property
    def __dict__(self) -> dict[str, Any]:
        """Get module dictionary.

        Returns:
            Module dictionary
        """
        return self._dict


class ModuleType:
    """Enumeration of module types supported by Dana."""

    DANA = "dana"  # Native Dana modules (.na)
    PYTHON = "python"  # Python modules (.py)
    GENERATED = "gen"  # Generated modules (from magic)
    HYBRID = "hybrid"  # Mixed Dana/Python modules


@dataclass
class ModuleCache:
    """Cache information for a module."""

    timestamp: float = 0.0  # Last modification time
    version_tag: str = ""  # Version information
    dependencies: dict[str, float] = field(default_factory=dict)  # Dependency timestamps
