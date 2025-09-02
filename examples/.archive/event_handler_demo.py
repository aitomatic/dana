#!/usr/bin/env python3
"""
Event Handler Demo for Dana Registries

This demonstrates how to use the new event handler functionality
with AGENT_REGISTRY and RESOURCE_REGISTRY.
"""

from dana.core.builtin_types.struct_system import StructInstance, StructType
from dana.registry import AGENT_REGISTRY, RESOURCE_REGISTRY


def on_agent_registered(agent_id: str, agent):
    """Handler for agent registration events."""
    print(f"🎯 Agent registered: {agent_id} (type: {type(agent).__name__})")


def on_agent_unregistered(agent_id: str, agent):
    """Handler for agent unregistration events."""
    print(f"🗑️  Agent unregistered: {agent_id} (type: {type(agent).__name__})")


def on_resource_registered(resource_id: str, resource):
    """Handler for resource registration events."""
    print(f"📦 Resource registered: {resource_id} (type: {type(resource).__name__})")


def on_resource_unregistered(resource_id: str, resource):
    """Handler for resource unregistration events."""
    print(f"🗑️  Resource unregistered: {resource_id} (type: {type(resource).__name__})")


def on_general_event(event_type: str, item_id: str, item):
    """General event handler for any event type."""
    print(f"📢 General event '{event_type}': {item_id}")


def main():
    """Main demo function."""
    print("🚀 Dana Registry Event Handler Demo")
    print("=" * 40)

    # Register event handlers
    print("\n📝 Registering event handlers...")
    AGENT_REGISTRY.on_registered(on_agent_registered)
    AGENT_REGISTRY.on_unregistered(on_agent_unregistered)
    AGENT_REGISTRY.on_event("registered", lambda item_id, item: on_general_event("registered", item_id, item))

    RESOURCE_REGISTRY.on_registered(on_resource_registered)
    RESOURCE_REGISTRY.on_unregistered(on_resource_unregistered)
    RESOURCE_REGISTRY.on_event("unregistered", lambda item_id, item: on_general_event("unregistered", item_id, item))

    print("✅ Event handlers registered successfully!")
    print(f"📊 Agent registry has {AGENT_REGISTRY.get_event_handler_count()} total handlers")
    print(f"📊 Resource registry has {RESOURCE_REGISTRY.get_event_handler_count()} total handlers")

    # Create test instances
    print("\n🎬 Creating test instances...")

    # Create agent instance
    agent_type = StructType("TestAgent", {"name": "str"}, ["name"], {"name": "Agent name"})
    agent_instance = StructInstance(agent_type, {"name": "DemoAgent"})

    # Create resource instance
    resource_type = StructType("TestResource", {"url": "str"}, ["url"], {"url": "Resource URL"})
    resource_instance = StructInstance(resource_type, {"url": "https://example.com"})

    # Track instances (this will trigger registration events)
    print("\n📥 Tracking instances...")
    agent_id = AGENT_REGISTRY.track_instance(agent_instance, "demo_agent")
    resource_id = RESOURCE_REGISTRY.track_instance(resource_instance, "demo_resource")

    # Untrack instances (this will trigger unregistration events)
    print("\n📤 Untracking instances...")
    AGENT_REGISTRY.untrack_instance(agent_id)
    RESOURCE_REGISTRY.untrack_instance(resource_id)

    # Test event handler management
    print("\n🔧 Testing event handler management...")
    print(f"Before clear: {AGENT_REGISTRY.get_event_handler_count()} handlers")
    AGENT_REGISTRY.clear_event_handlers("registered")
    print(f"After clearing 'registered': {AGENT_REGISTRY.get_event_handler_count()} handlers")
    AGENT_REGISTRY.clear_event_handlers()
    print(f"After clearing all: {AGENT_REGISTRY.get_event_handler_count()} handlers")

    print("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    main()
