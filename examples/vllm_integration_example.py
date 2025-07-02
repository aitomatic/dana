#!/usr/bin/env python3
"""
Example: Using OpenDXA with Local vLLM Server

This script demonstrates how to configure OpenDXA to use a local vLLM server
instead of cloud-based LLM providers.

Prerequisites:
1. Start your vLLM server: ./bin/vllm/start.sh
2. Ensure the server is running on http://localhost:8000
3. Run this script: python examples/vllm_integration_example.py

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import os
from pathlib import Path

import aisuite as ai

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest, BaseResponse


class LocalvLLMDemo:
    """Demonstrates OpenDXA integration with local vLLM server."""

    def __init__(self):
        self.vllm_base_url = "http://localhost:8000/v1"
        self.vllm_model = "microsoft/Phi-4"  # or whatever model you've loaded

    async def test_direct_aisuite_connection(self):
        """Test direct aisuite connection to vLLM."""
        print("🔧 Testing direct aisuite connection to vLLM...")

        # Configure aisuite for local vLLM
        provider_configs = {"openai": {"base_url": self.vllm_base_url, "api_key": "not-needed-for-local"}}

        client = ai.Client(provider_configs=provider_configs)

        try:
            response = client.chat.completions.create(
                model=f"openai:{self.vllm_model}",
                messages=[{"role": "user", "content": "Hello! Please introduce yourself in one sentence."}],
                max_tokens=100,
                temperature=0.7,
            )

            print(f"✅ Direct aisuite response: {response.choices[0].message.content}")
            return True

        except Exception as e:
            print(f"❌ Direct aisuite connection failed: {e}")
            return False

    async def test_opendxa_llm_resource(self):
        """Test OpenDXA LLMResource with vLLM configuration."""
        print("\n🔧 Testing OpenDXA LLMResource with vLLM...")

        # Method 1: Configure via provider_configs
        llm_resource = LLMResource(
            name="vllm_local",
            model=f"openai:{self.vllm_model}",  # Use openai: prefix for compatibility
            temperature=0.7,
            max_tokens=100,
        )

        # Set up the provider configuration
        llm_resource.provider_configs["openai"] = {"base_url": self.vllm_base_url, "api_key": "not-needed-for-local"}

        try:
            # Create a test request
            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "What's the capital of France? Answer briefly."}]})

            # Query the LLM
            response = await llm_resource.query(request)

            if hasattr(response, "content") and response.content:
                print(f"✅ OpenDXA LLMResource response: {response.content}")
                return True
            else:
                print(f"❌ No content in response: {response}")
                return False

        except Exception as e:
            print(f"❌ OpenDXA LLMResource test failed: {e}")
            return False

    async def test_environment_variable_config(self):
        """Test configuration via environment variables."""
        print("\n🔧 Testing environment variable configuration...")

        # Set environment variables for vLLM
        os.environ["OPENAI_BASE_URL"] = self.vllm_base_url
        os.environ["OPENAI_API_KEY"] = "not-needed-for-local"

        try:
            # Create LLMResource with minimal config
            llm_resource = LLMResource(name="vllm_env", model=f"openai:{self.vllm_model}")

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "Tell me a fun fact about AI in one sentence."}]})

            response = await llm_resource.query(request)

            if hasattr(response, "content") and response.content:
                print(f"✅ Environment config response: {response.content}")
                return True
            else:
                print(f"❌ No content in response: {response}")
                return False

        except Exception as e:
            print(f"❌ Environment config test failed: {e}")
            return False

    def check_vllm_server(self):
        """Check if vLLM server is running."""
        import requests

        try:
            response = requests.get(f"{self.vllm_base_url.rstrip('/v1')}/health", timeout=5)
            if response.status_code == 200:
                print("✅ vLLM server is running")
                return True
        except requests.exceptions.RequestException:
            pass

        print("❌ vLLM server is not running")
        print("💡 Start it with: ./bin/vllm/start.sh")
        return False

    async def run_all_tests(self):
        """Run all configuration tests."""
        print("🚀 OpenDXA + vLLM Integration Demo")
        print("=" * 50)

        # Check if vLLM server is running
        if not self.check_vllm_server():
            return

        print(f"🎯 Testing connection to: {self.vllm_base_url}")
        print(f"📋 Using model: {self.vllm_model}")
        print()

        # Run tests
        test1 = await self.test_direct_aisuite_connection()
        test2 = await self.test_opendxa_llm_resource()
        test3 = await self.test_environment_variable_config()

        print("\n" + "=" * 50)
        print("📊 Test Results:")
        print(f"   Direct aisuite: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"   OpenDXA LLMResource: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"   Environment config: {'✅ PASS' if test3 else '❌ FAIL'}")

        if all([test1, test2, test3]):
            print("\n🎉 All tests passed! Your vLLM integration is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check your vLLM server and configuration.")


def show_configuration_examples():
    """Show different ways to configure vLLM with OpenDXA."""
    print("\n📋 Configuration Examples:")
    print("-" * 30)

    print("\n1️⃣ Environment Variables (.env file):")
    print("""
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=not-needed-for-local
""")

    print("\n2️⃣ Provider Config (in code):")
    print("""
provider_configs = {
    "openai": {
        "base_url": "http://localhost:8000/v1",
        "api_key": "not-needed-for-local"
    }
}
client = ai.Client(provider_configs=provider_configs)
""")

    print("\n3️⃣ OpenDXA Config (opendxa_config.json):")
    print("""
{
    "llm": {
        "preferred_models": [
            {"name": "vllm:local-model", "required_api_keys": []}
        ],
        "provider_configs": {
            "vllm": {
                "base_url": "http://localhost:8000/v1",
                "api_key": "not-needed"
            }
        }
    }
}
""")


async def main():
    """Main demo function."""
    demo = LocalvLLMDemo()
    await demo.run_all_tests()
    show_configuration_examples()


if __name__ == "__main__":
    asyncio.run(main())
