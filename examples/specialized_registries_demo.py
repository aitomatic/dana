#!/usr/bin/env python3
"""
Demo script for specialized registries (AgentRegistry and ResourceRegistry).

This script demonstrates the specialized functionality of AgentRegistry and ResourceRegistry
compared to the base StructRegistry.
"""

from dana.core.builtins.struct_system import StructInstance
from dana.registry import AGENT_REGISTRY, RESOURCE_REGISTRY


def create_mock_struct_instance(name: str) -> StructInstance:
    """Create a mock StructInstance for demonstration."""
    # This is a simplified mock - in real usage, you'd create actual struct instances
    instance = StructInstance.__new__(StructInstance)
    instance.instance_id = f"mock_{name}_{id(instance)}"
    return instance


def demo_agent_registry():
    """Demonstrate AgentRegistry specialized functionality."""
    print("=== AgentRegistry Demo ===")

    # Create mock agent instances
    researcher = create_mock_struct_instance("researcher")
    coder = create_mock_struct_instance("coder")
    planner = create_mock_struct_instance("planner")

    # Track agents with specialized metadata
    researcher_id = AGENT_REGISTRY.track_agent(
        researcher, name="Alice", role="researcher", capabilities=["research", "analysis", "writing"]
    )

    coder_id = AGENT_REGISTRY.track_agent(coder, name="Bob", role="coder", capabilities=["python", "javascript", "debugging"])

    planner_id = AGENT_REGISTRY.track_agent(planner, name="Charlie", role="planner", capabilities=["planning", "coordination", "strategy"])

    print(f"Tracked agents: {len(AGENT_REGISTRY.list_instances())} agents")

    # Demonstrate specialized queries
    researchers = AGENT_REGISTRY.get_agents_by_role("researcher")
    print(f"Researchers: {len(researchers)} agents")

    active_agents = AGENT_REGISTRY.get_active_agents()
    print(f"Active agents: {len(active_agents)} agents")

    # Demonstrate agent-specific metadata
    print(f"Alice's role: {AGENT_REGISTRY.get_agent_role(researcher_id)}")
    print(f"Bob's capabilities: {AGENT_REGISTRY.get_agent_capabilities(coder_id)}")
    print(f"Charlie's status: {AGENT_REGISTRY.get_agent_status(planner_id)}")

    # Change agent status
    AGENT_REGISTRY.set_agent_status(coder_id, "busy")
    print(f"Bob's new status: {AGENT_REGISTRY.get_agent_status(coder_id)}")

    print()


def demo_resource_registry():
    """Demonstrate ResourceRegistry specialized functionality."""
    print("=== ResourceRegistry Demo ===")

    # Create mock resource instances
    database = create_mock_struct_instance("database")
    api = create_mock_struct_instance("api")
    file_system = create_mock_struct_instance("file_system")

    # Track resources with specialized metadata
    db_id = RESOURCE_REGISTRY.track_resource(
        database, name="PostgreSQL DB", resource_type="database", provider="AWS RDS", permissions=["read", "write", "admin"]
    )

    api_id = RESOURCE_REGISTRY.track_resource(api, name="OpenAI API", resource_type="api", provider="OpenAI", permissions=["read", "write"])

    fs_id = RESOURCE_REGISTRY.track_resource(
        file_system, name="S3 Storage", resource_type="storage", provider="AWS S3", permissions=["read", "write"]
    )

    print(f"Tracked resources: {len(RESOURCE_REGISTRY.list_instances())} resources")

    # Demonstrate specialized queries
    databases = RESOURCE_REGISTRY.get_resources_by_type("database")
    print(f"Databases: {len(databases)} resources")

    aws_resources = RESOURCE_REGISTRY.get_resources_by_provider("AWS")
    print(f"AWS resources: {len(aws_resources)} resources")

    available_resources = RESOURCE_REGISTRY.get_available_resources()
    print(f"Available resources: {len(available_resources)} resources")

    # Demonstrate resource-specific metadata
    print(f"Database type: {RESOURCE_REGISTRY.get_resource_type(db_id)}")
    print(f"API provider: {RESOURCE_REGISTRY.get_resource_provider(api_id)}")
    print(f"File system permissions: {RESOURCE_REGISTRY.get_resource_permissions(fs_id)}")

    # Change resource status
    RESOURCE_REGISTRY.set_resource_status(api_id, "maintenance")
    print(f"API new status: {RESOURCE_REGISTRY.get_resource_status(api_id)}")

    # Add/remove permissions
    RESOURCE_REGISTRY.add_resource_permission(db_id, "backup")
    print(f"Database permissions after adding backup: {RESOURCE_REGISTRY.get_resource_permissions(db_id)}")

    RESOURCE_REGISTRY.remove_resource_permission(db_id, "admin")
    print(f"Database permissions after removing admin: {RESOURCE_REGISTRY.get_resource_permissions(db_id)}")

    print()


def demo_event_handling():
    """Demonstrate event handling with specialized registries."""
    print("=== Event Handling Demo ===")

    # Register event handlers
    def on_agent_registered(agent_id: str, agent: StructInstance):
        print(f"Agent registered: {agent_id}")

    def on_resource_registered(resource_id: str, resource: StructInstance):
        print(f"Resource registered: {resource_id}")

    AGENT_REGISTRY.on_registered(on_agent_registered)
    RESOURCE_REGISTRY.on_registered(on_resource_registered)

    # Create and track instances (this will trigger events)
    new_agent = create_mock_struct_instance("new_agent")
    new_resource = create_mock_struct_instance("new_resource")

    AGENT_REGISTRY.track_agent(new_agent, name="New Agent")
    RESOURCE_REGISTRY.track_resource(new_resource, name="New Resource")

    print()


def main():
    """Run the specialized registries demo."""
    print("Specialized Registries Demo")
    print("=" * 50)

    # Clear registries for clean demo
    AGENT_REGISTRY.clear()
    RESOURCE_REGISTRY.clear()

    demo_agent_registry()
    demo_resource_registry()
    demo_event_handling()

    print("Demo completed!")


if __name__ == "__main__":
    main()
