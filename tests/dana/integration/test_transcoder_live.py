"""Live test for the DANA transcoder using actual LLM calls."""

import os

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.transcoder.transcoder import Transcoder


# Register the live marker
def pytest_configure(config):
    config.addinivalue_line("markers", "live: mark test as a live test that requires external services")


@pytest.mark.live
@pytest.mark.asyncio
async def test_transcoder():
    """Run live tests of the transcoder with actual LLM calls."""
    # Set up LLM resource with OpenAI GPT-4
    preferred_models = [{"name": "openai:gpt-4", "required_api_keys": ["OPENAI_API_KEY"]}]

    # Create LLM resource with explicit model and API key
    llm = LLMResource(
        name="test_llm",
        model="openai:gpt-4",
        preferred_models=preferred_models,
        temperature=0.2,  # Lower temperature for more deterministic outputs
        provider_configs={"openai": {"api_key": os.getenv("OPENAI_API_KEY")}},
    )

    # Create transcoder
    transcoder = Transcoder(llm)

    # Test cases for natural language to DANA
    nl_to_dana_tests = [
        "add 5 and 10",
        "calculate the square root of 16",
        "set the user's name to Alice",
        "if temperature is greater than 30, print 'too hot'",
        "log an error message saying 'connection failed'",
    ]

    print("\n=== Testing Natural Language to DANA ===")
    for nl in nl_to_dana_tests:
        print(f"\nInput: {nl}")
        try:
            result = await transcoder.to_dana(nl)
            print(f"Generated DANA code: {result}")
        except Exception as e:
            print(f"Error: {e}")

    # Test cases for DANA to natural language
    dana_to_nl_tests = [
        "private.result = 5 + 10",
        "if private.temp > 30:\n    print('too hot')",
        "private.user_name = 'Alice'",
        "log.error('connection failed')",
        "private.sqrt_result = system.math.sqrt(16)",
    ]

    print("\n=== Testing DANA to Natural Language ===")
    for dana in dana_to_nl_tests:
        print(f"\nInput: {dana}")
        try:
            nl = await transcoder.to_natural_language(dana)
            print(f"Natural language: {nl}")
        except Exception as e:
            print(f"Error: {e}")
