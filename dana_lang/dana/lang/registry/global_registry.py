"""
Global Registry for Dana

Unified interface for all Dana registries with specialized storage for different types.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Optional

from .agent_registry import AgentRegistry
from .function_registry import FunctionRegistry
from .instance_registry import StructRegistry
from .module_registry import ModuleRegistry
from .resource_registry import ResourceRegistry
from .struct_function_registry import StructFunctionRegistry
from .type_registry import TypeRegistry


class GlobalRegistry:
    """Unified global registry for all Dana components.

    This registry provides a single entry point for all registry operations,
    with each sub-registry maintaining its own specialized storage patterns.
    """

    _instance: Optional["GlobalRegistry"] = None

    def __new__(cls) -> "GlobalRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize all sub-registries."""
        # Type registries (simple key-value storage)
        self.types = TypeRegistry()

        # Struct function registry (composite key storage)
        self.struct_functions = StructFunctionRegistry()

        # Module registry (complex multi-storage)
        self.modules = ModuleRegistry()

        # Function registry (simple key-value storage) with delegation to struct_functions
        self.functions = FunctionRegistry(struct_function_registry=self.struct_functions)

        # Agent instance registry
        self.agents = AgentRegistry()

        # Resource instance registry
        self.resources = ResourceRegistry()

        # Workflow instance registry
        self.workflows = StructRegistry()

    def clear_all(self) -> None:
        """Clear all registries (for testing)."""
        self.types.clear_instance()
        self.struct_functions.clear()
        self.modules.clear()
        self.functions.clear()
        self.agents.clear()
        self.resources.clear()
        self.workflows.clear()

    # === Type Registration Convenience Methods ===

    def register_agent_type(self, agent_type: Any) -> None:
        """Register an agent type."""
        self.types.register_agent_type(agent_type)

    def register_resource_type(self, resource_type: Any) -> None:
        """Register a resource type."""
        self.types.register_resource_type(resource_type)

    def register_struct_type(self, struct_type: Any) -> None:
        """Register a struct type."""
        self.types.register_struct_type(struct_type)

    def register_interface_type(self, interface_type: Any) -> None:
        """Register an interface type."""
        self.types.register_interface_type(interface_type)

    def register_workflow_type(self, workflow_type: Any) -> None:
        """Register a workflow type."""
        self.types.register_workflow_type(workflow_type)

    def get_agent_type(self, name: str) -> Any:
        """Get an agent type by name."""
        return self.types.get_agent_type(name)

    def get_resource_type(self, name: str) -> Any:
        """Get a resource type by name."""
        return self.types.get_resource_type(name)

    def get_struct_type(self, name: str) -> Any:
        """Get a struct type by name."""
        return self.types.get_struct_type(name)

    def get_interface_type(self, name: str) -> Any:
        """Get an interface type by name."""
        return self.types.get_interface_type(name)

    def get_workflow_type(self, name: str) -> Any:
        """Get a workflow type by name."""
        return self.types.get_workflow_type(name)

    # === Struct Function Registration Convenience Methods ===

    def register_struct_function(self, receiver_type: str, method_name: str, func: Any) -> None:
        """Register a struct function for a receiver type."""
        self.struct_functions.register_method(receiver_type, method_name, func)

    def lookup_struct_function(self, receiver_type: str, method_name: str) -> Any:
        """Lookup a struct function for a receiver type."""
        return self.struct_functions.lookup_method(receiver_type, method_name)

    def has_struct_function(self, receiver_type: str, method_name: str) -> bool:
        """Check if a struct function exists for a receiver type."""
        return self.struct_functions.has_method(receiver_type, method_name)

    # === Instance Management Convenience Methods ===

    def track_agent_instance(self, instance: Any, name: str | None = None) -> str:
        """Track an agent instance globally."""
        return self.agents.track_instance(instance, name)

    def track_resource_instance(self, instance: Any, name: str | None = None) -> str:
        """Track a resource instance globally."""
        return self.resources.track_instance(instance, name)

    def track_workflow_instance(self, instance: Any, name: str | None = None) -> str:
        """Track a workflow instance globally."""
        return self.workflows.track_instance(instance, name)

    def list_agent_instances(self, agent_type: str | None = None) -> list[Any]:
        """List all tracked agent instances."""
        return self.agents.list_instances(agent_type)

    def list_resource_instances(self, resource_type: str | None = None) -> list[Any]:
        """List all tracked resource instances."""
        return self.resources.list_instances(resource_type)

    def list_workflow_instances(self, workflow_type: str | None = None) -> list[Any]:
        """List all tracked workflow instances."""
        return self.workflows.list_instances(workflow_type)

    # === Registry Statistics ===

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about all registries."""
        return {
            "types": {
                "agent_types": len(self.types.list_agent_types()),
                "resource_types": len(self.types.list_resource_types()),
                "struct_types": len(self.types.list_struct_types()),
                "workflow_types": len(self.types.list_workflow_types()),
            },
            "struct_functions": {
                "total_methods": len(self.struct_functions.list_all()),
            },
            "modules": {
                "total_modules": len(self.modules.list_modules()),
                "total_specs": len(self.modules.list_specs()),
            },
            "functions": {
                "total_functions": len(self.functions.list_all()),
            },
            "instances": {
                "agent_instances": len(self.agents.list_instances()),
                "resource_instances": len(self.resources.list_instances()),
                "workflow_instances": len(self.workflows.list_instances()),
            },
        }

    def __repr__(self) -> str:
        """String representation of the global registry."""
        stats = self.get_statistics()
        return (
            f"GlobalRegistry("
            f"agent_types={stats['types']['agent_types']}, "
            f"resource_types={stats['types']['resource_types']}, "
            f"struct_types={stats['types']['struct_types']}, "
            f"workflow_types={stats['types']['workflow_types']}, "
            f"struct_functions={stats['struct_functions']['total_methods']}, "
            f"modules={stats['modules']['total_modules']}, "
            f"functions={stats['functions']['total_functions']}, "
            f"agent_instances={stats['instances']['agent_instances']}, "
            f"resource_instances={stats['instances']['resource_instances']}, "
            f"workflow_instances={stats['instances']['workflow_instances']}"
            f")"
        )
