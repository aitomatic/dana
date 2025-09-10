#!/usr/bin/env python3
"""
Demo script showing TUI integration with AGENT_REGISTRY events.

This demonstrates how the TUI app automatically responds to agent
registration and unregistration events from the global registry.
"""

from dana.core.builtins.struct_system import StructInstance, StructType
from dana.registry import AGENT_REGISTRY


def main():
    """Main demo function."""
    print("🚀 TUI Registry Integration Demo")
    print("=" * 40)

    # Clear any existing handlers
    AGENT_REGISTRY.clear_event_handlers()

    print("\n📝 Creating TUI app (this registers event handlers)...")
    from dana.apps.tui.tui_app import DanaTUI

    # Create TUI app - this will register event handlers
    _ = DanaTUI()  # tui_app unused

    print(f"✅ TUI app created with {AGENT_REGISTRY.get_event_handler_count()} event handlers")

    print("\n🎬 Simulating agent registry events...")

    # Create test agent instances
    agent_type = StructType("DemoAgent", {"name": "str"}, ["name"], {"name": "Demo Agent"})

    # Simulate agent registration events
    print("\n📥 Registering agents in global registry...")
    for i in range(3):
        agent_instance = StructInstance(agent_type, {"name": f"Agent{i + 1}"})
        instance_id = AGENT_REGISTRY.track_instance(agent_instance, f"demo_agent_{i + 1}")
        print(f"  - Registered: {instance_id}")

    # Simulate agent unregistration events
    print("\n📤 Unregistering agents from global registry...")
    instances = AGENT_REGISTRY.list_instances()
    for instance in instances:
        AGENT_REGISTRY.untrack_instance(instance.instance_id)
        print(f"  - Unregistered: {instance.instance_id}")

    print("\n🎉 Demo completed!")
    print("\n💡 In the actual TUI app, these events would:")
    print("   - Show system messages in the REPL panel")
    print("   - Update the agents list automatically")
    print("   - Provide real-time feedback on registry changes")
    print("\n🔧 You can also press Ctrl+R in the TUI to manually sync with the registry")
    print("\n📝 Note: The TUI app no longer uses registration/unregistration methods")
    print("   - Agents are managed directly through the global AGENT_REGISTRY")
    print("   - The TUI monitors registry events for real-time updates")


if __name__ == "__main__":
    main()
