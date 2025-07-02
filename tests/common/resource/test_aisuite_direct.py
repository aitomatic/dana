"""Direct AISuite test to isolate the proxies issue."""

import os
import aisuite as ai


def test_direct_aisuite_initialization():
    """Test AISuite Client initialization directly."""
    print("Testing direct AISuite initialization...")

    # Test 1: Empty provider_configs
    try:
        client = ai.Client(provider_configs={})
        print("✅ Empty provider_configs works")
    except Exception as e:
        print(f"❌ Empty provider_configs failed: {e}")

    # Test 2: Simple provider_configs
    try:
        provider_configs = {"anthropic": {"api_key": "test-key"}}
        client = ai.Client(provider_configs=provider_configs)
        print("✅ Simple provider_configs works")
    except Exception as e:
        print(f"❌ Simple provider_configs failed: {e}")

    # Test 3: Full provider_configs from our config
    try:
        provider_configs = {
            "openai": {"api_key": "test-openai-key"},
            "anthropic": {"api_key": "test-anthropic-key"},
            "groq": {"api_key": "test-groq-key"},
            "deepseek": {"api_key": "test-deepseek-key"},
        }
        client = ai.Client(provider_configs=provider_configs)
        print("✅ Full provider_configs works")
    except Exception as e:
        print(f"❌ Full provider_configs failed: {e}")

    # Test 4: Try with no arguments
    try:
        client = ai.Client()
        print("✅ No arguments works")
    except Exception as e:
        print(f"❌ No arguments failed: {e}")


if __name__ == "__main__":
    test_direct_aisuite_initialization()
