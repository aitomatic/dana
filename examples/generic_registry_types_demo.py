#!/usr/bin/env python3
"""
Demo script showing how generic registry types can be extended for specific types.

This demonstrates how you could create specialized registries for specific
agent and resource types with proper type annotations.
"""

# Remove unused import
from dana.core.builtins.struct_system import StructInstance
from dana.registry import AGENT_REGISTRY, RESOURCE_REGISTRY


# Example: Define specific agent and resource types
class AgentInstance(StructInstance):
    """Base class for agent instances."""

    def get_metrics(self) -> dict:
        """Get agent metrics - required by TUI."""
        return {"status": "active", "tasks_completed": 0, "memory_usage": "0MB"}


class ResourceInstance(StructInstance):
    """Base class for resource instances."""

    def get_permissions(self) -> list[str]:
        """Get resource permissions."""
        return []


# Example: Create specialized registries for specific types
class TypedAgentRegistry:
    """Example of how you could create a typed agent registry."""

    def __init__(self):
        self._registry = AGENT_REGISTRY

    def track_agent(self, agent: AgentInstance, **kwargs) -> str:
        """Track an agent with type safety."""
        return self._registry.track_agent(agent, **kwargs)

    def get_agent(self, agent_id: str) -> AgentInstance | None:
        """Get an agent with type safety."""
        instance = self._registry.get_instance(agent_id)
        if isinstance(instance, AgentInstance):
            return instance
        return None

    def list_agents(self) -> list[AgentInstance]:
        """List all agents with type safety."""
        instances = self._registry.list_instances()
        return [inst for inst in instances if isinstance(inst, AgentInstance)]


class TypedResourceRegistry:
    """Example of how you could create a typed resource registry."""

    def __init__(self):
        self._registry = RESOURCE_REGISTRY

    def track_resource(self, resource: ResourceInstance, **kwargs) -> str:
        """Track a resource with type safety."""
        return self._registry.track_resource(resource, **kwargs)

    def get_resource(self, resource_id: str) -> ResourceInstance | None:
        """Get a resource with type safety."""
        instance = self._registry.get_instance(resource_id)
        if isinstance(instance, ResourceInstance):
            return instance
        return None

    def list_resources(self) -> list[ResourceInstance]:
        """List all resources with type safety."""
        instances = self._registry.list_instances()
        return [inst for inst in instances if isinstance(inst, ResourceInstance)]


def create_mock_agent_instance(name: str) -> AgentInstance:
    """Create a mock AgentInstance for demonstration."""
    instance = AgentInstance.__new__(AgentInstance)
    instance.instance_id = f"agent_{name}_{id(instance)}"
    return instance


def create_mock_resource_instance(name: str) -> ResourceInstance:
    """Create a mock ResourceInstance for demonstration."""
    instance = ResourceInstance.__new__(ResourceInstance)
    instance.instance_id = f"resource_{name}_{id(instance)}"
    return instance


def demo_typed_registries():
    """Demonstrate typed registry usage."""
    print("=== Typed Registry Demo ===")

    # Create typed registries
    typed_agents = TypedAgentRegistry()
    typed_resources = TypedResourceRegistry()

    # Create typed instances
    agent1 = create_mock_agent_instance("researcher")
    agent2 = create_mock_agent_instance("coder")
    resource1 = create_mock_resource_instance("database")
    resource2 = create_mock_resource_instance("api")

    # Track instances with type safety
    agent1_id = typed_agents.track_agent(agent1, name="Alice", role="researcher")
    _ = typed_agents.track_agent(agent2, name="Bob", role="coder")  # agent2_id unused

    resource1_id = typed_resources.track_resource(resource1, name="PostgreSQL", resource_type="database")
    _ = typed_resources.track_resource(resource2, name="OpenAI API", resource_type="api")  # resource2_id unused

    # Retrieve instances with type safety
    retrieved_agent = typed_agents.get_agent(agent1_id)
    retrieved_resource = typed_resources.get_resource(resource1_id)

    print(f"Retrieved agent: {retrieved_agent}")
    print(f"Retrieved resource: {retrieved_resource}")

    # List instances with type safety
    agents = typed_agents.list_agents()
    resources = typed_resources.list_resources()

    print(f"Typed agents: {len(agents)} agents")
    print(f"Typed resources: {len(resources)} resources")

    # Demonstrate type-specific methods
    if retrieved_agent:
        metrics = retrieved_agent.get_metrics()
        print(f"Agent metrics: {metrics}")

    if retrieved_resource:
        permissions = retrieved_resource.get_permissions()
        print(f"Resource permissions: {permissions}")

    print()


def demo_type_safety():
    """Demonstrate type safety benefits."""
    print("=== Type Safety Demo ===")

    # This would be caught by type checkers:
    # typed_agents = TypedAgentRegistry()
    # regular_struct = StructInstance.__new__(StructInstance)  # Wrong type!
    # typed_agents.track_agent(regular_struct)  # Type error!

    print("Type safety ensures only AgentInstance objects can be tracked")
    print("in TypedAgentRegistry and only ResourceInstance objects can be")
    print("tracked in TypedResourceRegistry.")
    print()


def main():
    """Run the generic registry types demo."""
    print("Generic Registry Types Demo")
    print("=" * 50)

    # Clear registries for clean demo
    AGENT_REGISTRY.clear()
    RESOURCE_REGISTRY.clear()

    demo_typed_registries()
    demo_type_safety()

    print("Demo completed!")


if __name__ == "__main__":
    main()
