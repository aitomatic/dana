"""Example demonstrating RuntimeContext usage."""

from dana.core.lang.sandbox_context import SandboxContext


def main():
    # Create a runtime context
    ctx = SandboxContext()

    # Set some local state
    ctx.set("local:name", "Alice")
    ctx.set("local:role", "assistant")
    ctx.set("local:preferences.theme", "dark")
    ctx.set("local:preferences.language", "en")

    # Set some public state
    ctx.set("public:temperature", 25)
    ctx.set("public:humidity", 60)
    ctx.set("public:sensor.status", "active")

    # Set some system state
    ctx.set("system:status", "running")
    ctx.set("system:step", 1)
    ctx.set("system:errors", [])

    # Print the state
    print("Local State:")
    print(f"  Name: {ctx.get('local:name')}")
    print(f"  Role: {ctx.get('local:role')}")
    print(f"  Theme: {ctx.get('local:preferences.theme')}")
    print(f"  Language: {ctx.get('local:preferences.language')}")

    print("\nPublic State:")
    print(f"  Temperature: {ctx.get('public:temperature')}")
    print(f"  Humidity: {ctx.get('public:humidity')}")
    print(f"  Sensor Status: {ctx.get('public:sensor.status')}")

    print("\nSystem State:")
    print(f"  Status: {ctx.get('system:status')}")
    print(f"  Step: {ctx.get('system:step')}")
    print(f"  Errors: {ctx.get('system:errors')}")

    # Demonstrate error handling
    try:
        ctx.get("invalid:key")
    except Exception as e:
        print(f"\nError handling example: {e}")


if __name__ == "__main__":
    main()
