"""Example demonstrating RuntimeContext usage."""

from opendxa.dana.sandbox.sandbox_context import SandboxContext


def main():
    # Create a runtime context
    ctx = SandboxContext()

    # Set some agent state
    ctx.set("agent:name", "Alice")
    ctx.set("agent:role", "assistant")
    ctx.set("agent:preferences.theme", "dark")
    ctx.set("agent:preferences.language", "en")

    # Set some world state
    ctx.set("world:temperature", 25)
    ctx.set("world:humidity", 60)
    ctx.set("world:sensor.status", "active")

    # Set some execution state
    ctx.set("execution:status", "running")
    ctx.set("execution:step", 1)
    ctx.set("execution:errors", [])

    # Print the state
    print("Agent State:")
    print(f"  Name: {ctx.get('agent:name')}")
    print(f"  Role: {ctx.get('agent:role')}")
    print(f"  Theme: {ctx.get('agent:preferences.theme')}")
    print(f"  Language: {ctx.get('agent:preferences.language')}")

    print("\nWorld State:")
    print(f"  Temperature: {ctx.get('world:temperature')}")
    print(f"  Humidity: {ctx.get('world:humidity')}")
    print(f"  Sensor Status: {ctx.get('world:sensor.status')}")

    print("\nExecution State:")
    print(f"  Status: {ctx.get('execution:status')}")
    print(f"  Step: {ctx.get('execution:step')}")
    print(f"  Errors: {ctx.get('execution:errors')}")

    # Demonstrate error handling
    try:
        ctx.get("invalid:key")
    except Exception as e:
        print(f"\nError handling example: {e}")


if __name__ == "__main__":
    main()
