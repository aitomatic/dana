"""
Live tests for OpenAI model parameter compatibility.

These tests help discover which parameters are supported by different OpenAI model series.
Run with: cd dana_agent && uv run pytest tests/live/llm/test_openai_model_compatibility.py --live -v
"""

import asyncio
from datetime import datetime
import json
from pathlib import Path

import pytest

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage


# Models to test for compatibility
MODELS_TO_TEST = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "gpt-5-mini",  # New series with different restrictions
]

# Simple test prompt
TEST_PROMPT = "Say 'ok' and nothing else."


class TestOpenAIModelCompatibility:
    """Live tests to discover model-specific parameter restrictions."""

    @pytest.mark.live
    @pytest.mark.provider("openai")
    def test_temperature_support(self):
        """Test temperature parameter support across models."""
        temperature_values = [0, 0.5, 1]
        results = {}

        for model in MODELS_TO_TEST:
            results[model] = {}
            for temp in temperature_values:
                try:
                    llm = LLM(provider="openai", model=model)
                    messages = [LLMMessage(role="user", content=TEST_PROMPT)]
                    _ = asyncio.run(llm.provider.chat(messages, temperature=temp))
                    results[model][f"temperature={temp}"] = "✅ supported"
                    print(f"✅ {model} temperature={temp}: supported")
                except Exception as e:
                    error_msg = str(e)
                    if "API key" in error_msg:
                        pytest.skip(f"OpenAI API key not available: {error_msg}")
                    elif "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                        results[model][f"temperature={temp}"] = "⏭️ model not available"
                        print(f"⏭️ {model} temperature={temp}: model not available")
                        break  # Skip remaining tests for this model
                    else:
                        results[model][f"temperature={temp}"] = f"❌ {error_msg[:100]}"
                        print(f"❌ {model} temperature={temp}: {error_msg[:100]}")

        # Print summary
        print("\n" + "=" * 60)
        print("Temperature Support Matrix:")
        print("=" * 60)
        for model, model_results in results.items():
            print(f"\n{model}:")
            for param, result in model_results.items():
                print(f"  {param}: {result}")

    @pytest.mark.live
    @pytest.mark.provider("openai")
    def test_max_tokens_support(self):
        """Test max_tokens parameter support across models."""
        # Test explicit value, no value, and explicit None (though None is filtered)
        test_cases = [
            ("max_tokens=100", {"max_tokens": 100}),
            ("no max_tokens", {}),
        ]
        results = {}

        for model in MODELS_TO_TEST:
            results[model] = {}
            for case_name, kwargs in test_cases:
                try:
                    llm = LLM(provider="openai", model=model)
                    messages = [LLMMessage(role="user", content=TEST_PROMPT)]
                    _ = asyncio.run(llm.provider.chat(messages, **kwargs))
                    results[model][case_name] = "✅ supported"
                    print(f"✅ {model} {case_name}: supported")
                except Exception as e:
                    error_msg = str(e)
                    if "API key" in error_msg:
                        pytest.skip(f"OpenAI API key not available: {error_msg}")
                    elif "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                        results[model][case_name] = "⏭️ model not available"
                        print(f"⏭️ {model} {case_name}: model not available")
                        break
                    else:
                        results[model][case_name] = f"❌ {error_msg[:100]}"
                        print(f"❌ {model} {case_name}: {error_msg[:100]}")

        # Print summary
        print("\n" + "=" * 60)
        print("Max Tokens Support Matrix:")
        print("=" * 60)
        for model, model_results in results.items():
            print(f"\n{model}:")
            for param, result in model_results.items():
                print(f"  {param}: {result}")

    @pytest.mark.live
    @pytest.mark.provider("openai")
    def test_json_mode_support(self):
        """Test JSON mode (response_format) support across models."""
        results = {}

        for model in MODELS_TO_TEST:
            try:
                llm = LLM(provider="openai", model=model)
                messages = [
                    LLMMessage(
                        role="system",
                        content="You are a helpful assistant that responds in JSON format.",
                    ),
                    LLMMessage(role="user", content='Respond with {"status": "ok"}'),
                ]
                response = asyncio.run(llm.provider.chat(messages, json_mode=True))
                results[model] = "✅ supported"
                print(f"✅ {model} json_mode: supported - {response.content[:50]}")
            except Exception as e:
                error_msg = str(e)
                if "API key" in error_msg:
                    pytest.skip(f"OpenAI API key not available: {error_msg}")
                elif "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                    results[model] = "⏭️ model not available"
                    print(f"⏭️ {model} json_mode: model not available")
                else:
                    results[model] = f"❌ {error_msg[:100]}"
                    print(f"❌ {model} json_mode: {error_msg[:100]}")

        # Print summary
        print("\n" + "=" * 60)
        print("JSON Mode Support Matrix:")
        print("=" * 60)
        for model, result in results.items():
            print(f"  {model}: {result}")

    @pytest.mark.live
    @pytest.mark.provider("openai")
    def test_combined_parameters(self):
        """Test common parameter combinations across models."""
        test_cases = [
            ("default params", {}),
            ("temp=0", {"temperature": 0}),
            ("temp=0 + max_tokens=100", {"temperature": 0, "max_tokens": 100}),
            ("temp=1 + max_tokens=100", {"temperature": 1, "max_tokens": 100}),
        ]
        results = {}

        for model in MODELS_TO_TEST:
            results[model] = {}
            model_available = True

            for case_name, kwargs in test_cases:
                if not model_available:
                    results[model][case_name] = "⏭️ model not available"
                    continue

                try:
                    llm = LLM(provider="openai", model=model)
                    messages = [LLMMessage(role="user", content=TEST_PROMPT)]
                    _ = asyncio.run(llm.provider.chat(messages, **kwargs))
                    results[model][case_name] = "✅ ok"
                    print(f"✅ {model} [{case_name}]: ok")
                except Exception as e:
                    error_msg = str(e)
                    if "API key" in error_msg:
                        pytest.skip(f"OpenAI API key not available: {error_msg}")
                    elif "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                        results[model][case_name] = "⏭️ model not available"
                        model_available = False
                        print(f"⏭️ {model} [{case_name}]: model not available")
                    else:
                        results[model][case_name] = f"❌ {error_msg[:80]}"
                        print(f"❌ {model} [{case_name}]: {error_msg[:80]}")

        # Print summary
        print("\n" + "=" * 60)
        print("Combined Parameters Matrix:")
        print("=" * 60)
        for model, model_results in results.items():
            print(f"\n{model}:")
            for param, result in model_results.items():
                print(f"  {param}: {result}")

    @pytest.mark.live
    @pytest.mark.provider("openai")
    def test_full_compatibility_matrix(self):
        """
        Comprehensive test that generates a full compatibility matrix.

        This test runs all parameter combinations and saves results to JSON.
        """
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "models": {},
        }

        parameter_tests = [
            ("temperature=0", {"temperature": 0}),
            ("temperature=0.5", {"temperature": 0.5}),
            ("temperature=1", {"temperature": 1}),
            ("max_tokens=100", {"max_tokens": 100}),
            ("no extra params", {}),
        ]

        for model in MODELS_TO_TEST:
            all_results["models"][model] = {"available": True, "parameters": {}}
            model_available = True

            for test_name, kwargs in parameter_tests:
                if not model_available:
                    all_results["models"][model]["parameters"][test_name] = {
                        "supported": None,
                        "error": "model not available",
                    }
                    continue

                try:
                    llm = LLM(provider="openai", model=model)
                    messages = [LLMMessage(role="user", content=TEST_PROMPT)]
                    _ = asyncio.run(llm.provider.chat(messages, **kwargs))
                    all_results["models"][model]["parameters"][test_name] = {
                        "supported": True,
                        "error": None,
                    }
                except Exception as e:
                    error_msg = str(e)
                    if "API key" in error_msg:
                        pytest.skip(f"OpenAI API key not available: {error_msg}")
                    elif "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
                        all_results["models"][model]["available"] = False
                        all_results["models"][model]["parameters"][test_name] = {
                            "supported": None,
                            "error": "model not available",
                        }
                        model_available = False
                    else:
                        all_results["models"][model]["parameters"][test_name] = {
                            "supported": False,
                            "error": error_msg[:200],
                        }

        # Print formatted results
        print("\n" + "=" * 70)
        print("FULL COMPATIBILITY MATRIX")
        print("=" * 70)
        print(json.dumps(all_results, indent=2))

        # Save to file for reference
        output_path = Path(__file__).parent / "openai_compatibility_results.json"
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults saved to: {output_path}")
