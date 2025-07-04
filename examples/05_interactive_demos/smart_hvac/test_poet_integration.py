#!/usr/bin/env python3
"""
Test script for POET integration in Smart HVAC Demo

This script verifies that the real POET framework can be imported and used
with the building management plugin and LLM integration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_poet_imports():
    """Test that POET framework components can be imported."""
    print("🧪 Testing POET framework imports...")

    try:
        from dana.frameworks.poet.poet import POETConfig, POETExecutor, poet

        print("✅ POET core framework imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import POET framework: {e}")
        return False

    try:
        from dana.frameworks.poet.plugins import PLUGIN_REGISTRY

        print("✅ POET plugin registry imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import plugin registry: {e}")
        return False

    try:
        from dana.common.resource.llm_resource import LLMResource

        print("✅ LLM resource imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import LLM resource: {e}")
        return False

    return True


async def test_plugin_discovery():
    """Test that the building management plugin can be discovered."""
    print("\n🔍 Testing plugin discovery...")

    try:
        from dana.frameworks.poet.plugins import PLUGIN_REGISTRY

        # Discover plugins
        plugin_count = PLUGIN_REGISTRY.discover_plugins()
        print(f"✅ Discovered {plugin_count} plugins")

        # List available plugins
        available_plugins = PLUGIN_REGISTRY.list_plugins()
        print(f"📋 Available plugins: {available_plugins}")

        # Check for building management plugin
        if "building_management" in available_plugins:
            print("✅ Building management plugin found")

            # Try to get the plugin
            plugin = PLUGIN_REGISTRY.get_plugin("building_management")
            if plugin:
                print("✅ Building management plugin loaded successfully")
                plugin_info = plugin.get_plugin_info()
                print(f"📄 Plugin info: {plugin_info}")
                return True
            else:
                print("❌ Failed to load building management plugin")
                return False
        else:
            print("❌ Building management plugin not found")
            return False

    except Exception as e:
        print(f"❌ Plugin discovery failed: {e}")
        return False


async def test_llm_setup():
    """Test LLM resource setup."""
    print("\n🤖 Testing LLM resource setup...")

    # Check for API keys
    api_keys = {
        "OpenAI": os.environ.get("OPENAI_API_KEY"),
        "Anthropic": os.environ.get("ANTHROPIC_API_KEY"),
        "Groq": os.environ.get("GROQ_API_KEY"),
    }

    available_keys = [provider for provider, key in api_keys.items() if key]

    if not available_keys:
        print("⚠️ No LLM API keys found - LLM features will not be available")
        print("Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY")
        return False

    print(f"✅ Found API keys for: {', '.join(available_keys)}")

    try:
        from dana.common.resource.llm_resource import LLMResource

        # Create LLM resource
        llm = LLMResource(name="test_llm")
        await llm.initialize()

        if llm.model:
            print(f"✅ LLM initialized with model: {llm.model}")
            return True
        else:
            print("❌ LLM initialized but no model selected")
            return False

    except Exception as e:
        print(f"❌ LLM setup failed: {e}")
        return False


async def test_poet_decorator():
    """Test the POET decorator functionality."""
    print("\n🎭 Testing POET decorator...")

    try:
        from hvac_systems import HVACCommand

        from dana.frameworks.poet.poet import poet

        # Create a simple test function with POET decorator
        @poet(domain="building_management", enable_training=True)
        def test_hvac_function(current_temp: float, target_temp: float, outdoor_temp: float, occupancy: bool) -> HVACCommand:
            """Test HVAC function with POET enhancement."""
            temp_error = target_temp - current_temp

            if abs(temp_error) < 0.5:
                return HVACCommand(heating_output=0, cooling_output=0, fan_speed=20, mode="idle")
            elif temp_error > 0:
                output = min(100, abs(temp_error) * 20)
                return HVACCommand(heating_output=output, cooling_output=0, fan_speed=output + 20, mode="heating")
            else:
                output = min(100, abs(temp_error) * 20)
                return HVACCommand(heating_output=0, cooling_output=output, fan_speed=output + 20, mode="cooling")

        # Test the decorated function with the standard HVAC signature
        result = test_hvac_function(70.0, 72.0, 65.0, True)

        if isinstance(result, dict) and "result" in result:
            # POET wrapper returns a dict with metadata
            actual_result = result["result"]
            print("✅ POET decorator working - function wrapped successfully")
            print(f"📊 POET metadata: execution_time={result.get('execution_time')}, success={result.get('success')}")
            print(f"🏠 HVAC result: {actual_result}")
        else:
            # Direct result (might be fallback mode)
            print("⚠️ POET decorator present but may be in fallback mode")
            print(f"🏠 HVAC result: {result}")

        # Check for executor
        if hasattr(test_hvac_function, "_poet_executor"):
            executor = test_hvac_function._poet_executor
            print("✅ POET executor attached to function")

            # Test learning status
            learning_status = executor.get_learning_status()
            print(f"📈 Learning status: {learning_status}")

            return True
        else:
            print("❌ No POET executor found")
            return False

    except Exception as e:
        print(f"❌ POET decorator test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_hvac_integration():
    """Test the actual HVAC systems integration."""
    print("\n🏠 Testing HVAC systems integration...")

    try:
        from hvac_systems import POET_AVAILABLE, basic_hvac_control, smart_hvac_control

        print(f"📋 POET availability: {POET_AVAILABLE}")

        # Test basic HVAC control
        basic_result = basic_hvac_control(70.0, 72.0, 75.0, True)
        print(f"✅ Basic HVAC: {basic_result}")

        # Test smart HVAC control
        smart_result = smart_hvac_control(70.0, 72.0, 75.0, True)

        if isinstance(smart_result, dict) and "result" in smart_result:
            print(f"✅ Smart HVAC (POET enhanced): {smart_result['result']}")
            print(f"📊 POET metadata: {smart_result}")
        else:
            print(f"✅ Smart HVAC (fallback mode): {smart_result}")

        return True

    except Exception as e:
        print(f"❌ HVAC integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 POET Integration Test Suite")
    print("=" * 50)

    # Run tests
    tests = [
        ("Import Tests", test_poet_imports),
        ("Plugin Discovery", test_plugin_discovery),
        ("LLM Setup", test_llm_setup),
        ("POET Decorator", test_poet_decorator),
        ("HVAC Integration", test_hvac_integration),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'=' * 20} Test Summary {'=' * 20}")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! POET integration is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
