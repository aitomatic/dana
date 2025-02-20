"""Example of using LLMResource with multiple providers."""

import asyncio
import os
from dxa.agent.resource.llm_resource import LLMResource

async def main():
    """Example of using LLMResource with multiple providers."""

    # Configure LLM resource with multiple providers
    config = {
        "model": "openai:gpt-4",  # Default model
        "providers": {
            "openai": {
                "api_key": os.environ.get("OPENAI_API_KEY")
            },
            "anthropic": {
                "api_key": os.environ.get("ANTHROPIC_API_KEY")
            }
        },
        "temperature": 0.7,
        "max_retries": 3
    }

    # Initialize LLM resource
    llm = LLMResource(name="multi_provider_llm", config=config)
    await llm.initialize()

    # Test prompt
    test_prompt = "Explain quantum computing in one sentence."

    # Test with OpenAI
    try:
        print("\nTesting OpenAI GPT-4:")
        response = await llm.query({
            "prompt": test_prompt,
            "system_prompt": "You are a helpful assistant."
        })
        print(f"Response: {response['content']}")
        print(f"Model: {response['model']}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"OpenAI Error: {str(e)}")

    # Switch to Anthropic model
    llm.model = "anthropic:claude-3-sonnet-20240229"

    # Test with Anthropic
    try:
        print("\nTesting Anthropic Claude:")
        response = await llm.query({
            "prompt": test_prompt,
            "system_prompt": "You are a helpful assistant."
        })
        print(f"Response: {response['content']}")
        print(f"Model: {response['model']}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Anthropic Error: {str(e)}")

    # Cleanup
    await llm.cleanup()

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
