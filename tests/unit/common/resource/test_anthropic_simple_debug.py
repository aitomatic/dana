"""Simple test to debug the provider_configs loading."""

import os

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource


def test_simple_provider_configs_debug():
    """Simple test to see the provider_configs being loaded."""
    # Set up a test API key
    os.environ["ANTHROPIC_API_KEY"] = "test-key"

    try:
        # Create LLMResource to see what provider_configs it loads
        llm = LegacyLLMResource(name="debug_test")
        print(f"provider_configs loaded: {llm.provider_configs}")

        # Test initialization
        try:
            llm.startup()
            print("✅ LLM startup succeeded")
        except Exception as e:
            print(f"❌ LLM startup failed: {e}")

    finally:
        # Clean up
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
