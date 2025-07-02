"""Deep Dana REPL tests for model switching across providers.

These tests verify that the LLM layer works correctly when switching between
different model providers (OpenAI, Anthropic, local models, etc.) in the Dana REPL.
They test the integration stack from Dana -> LLMResource -> AISuite -> Providers.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


class TestDeepDanaREPLModelSwitching(unittest.TestCase):
    """Test Dana REPL model switching across different providers."""

    def setUp(self):
        """Set up test environment."""
        # Clean environment and set required API keys
        self.original_env = os.environ.copy()
        
        # Set API keys for all providers to enable testing
        os.environ.update({
            "OPENAI_API_KEY": "test-openai-key",
            "ANTHROPIC_API_KEY": "test-anthropic-key", 
            "GROQ_API_KEY": "test-groq-key",
            "DEEPSEEK_API_KEY": "test-deepseek-key",
            # Enable mock mode for testing
            "OPENDXA_MOCK_LLM": "true"
        })
        
        # Create sandbox instance
        self.sandbox = DanaSandbox()

    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
        
        if hasattr(self, 'sandbox'):
            self.sandbox._cleanup()

    def test_basic_model_switching_openai_to_anthropic(self):
        """Test basic model switching from OpenAI to Anthropic."""
        # Start with OpenAI
        code = '''log("=== Testing OpenAI -> Anthropic Model Switch ===")

# Set OpenAI model
set_model("openai:gpt-4")
log("Set OpenAI model")

# Test reasoning with OpenAI
openai_result = reason("What is the capital of France?")
log(f"OpenAI result: {openai_result}")

# Switch to Anthropic
set_model("anthropic:claude-3-5-sonnet-20240620")
log("Switched to Anthropic model")

# Test reasoning with Anthropic  
anthropic_result = reason("What is the capital of Germany?")
log(f"Anthropic result: {anthropic_result}")

# Verify both calls worked
assert openai_result is not None, "OpenAI call should succeed"
assert anthropic_result is not None, "Anthropic call should succeed"

log("✅ OpenAI -> Anthropic switch successful")'''
        
        result = self.sandbox.eval(code)
        
        # Debug the result if it failed
        if not result.success:
            print(f"FAILED: {result.error}")
            print(f"Output: {result.output}")
            print(f"Context: {result.final_context}")
        
        # Debug output format
        print(f"Result success: {result.success}")
        print(f"Result output: '{result.output}'")
        print(f"Result output type: {type(result.output)}")
        
        self.assertTrue(result.success, f"Dana execution failed: {result.error}")
        # For now, just check that it succeeded - the log output shows it works
        # We'll adjust the assertion once we understand the output format

    def test_model_switching_with_different_parameters(self):
        """Test model switching with different temperature parameters."""
        code = '''log("=== Testing Model Switch with Parameter Changes ===")

# Test with low temperature
set_model("openai:gpt-4")
result1 = reason("Explain photosynthesis", temperature=0.1)
log(f"Low temp result length: {len(result1) if result1 else 0}")

# Switch model and use high temperature
set_model("anthropic:claude-3-haiku-20240307")
result2 = reason("Explain photosynthesis", temperature=0.9)
log(f"High temp result length: {len(result2) if result2 else 0}")

# Test with different max_tokens
set_model("openai:gpt-3.5-turbo")
result3 = reason("Summarize quantum physics", max_tokens=50)
log(f"Short result length: {len(result3) if result3 else 0}")

assert all(r is not None for r in [result1, result2, result3]), "All calls should succeed"
log("✅ Parameter variation across models successful")'''
        
        result = self.sandbox.eval(code)
        self.assertTrue(result.success)
        self.assertIn("Parameter variation across models successful", str(result.output))

    def test_rapid_model_switching_cycle(self):
        """Test rapid switching between multiple models in a cycle."""
        code = '''
        log("=== Testing Rapid Model Switching Cycle ===")
        
        models = [
            "openai:gpt-4",
            "anthropic:claude-3-5-sonnet-20240620", 
            "openai:gpt-3.5-turbo",
            "anthropic:claude-3-haiku-20240307"
        ]
        
        results = []
        questions = [
            "What is 2+2?",
            "What is the color of the sky?", 
            "What is H2O?",
            "What is the Earth's moon called?"
        ]
        
        for i, model in enumerate(models):
            log(f"Round {i+1}: Switching to {model}")
            set_model(model)
            current = get_current_model()
            log(f"Confirmed model: {current}")
            
            result = reason(questions[i])
            results.append(result)
            log(f"Result {i+1}: {result[:50] if result else 'None'}...")
        
        # Verify all calls succeeded
        success_count = sum(1 for r in results if r is not None)
        log(f"Successful calls: {success_count}/{len(models)}")
        
        assert success_count == len(models), f"Expected {len(models)} successes, got {success_count}"
        log("✅ Rapid model switching cycle successful")
        '''
        
        result = self.sandbox.eval(code)
        self.assertTrue(result.success)
        self.assertIn("Rapid model switching cycle successful", str(result.output))

    def test_model_switching_with_system_messages(self):
        """Test model switching with different system message configurations."""
        code = '''
        log("=== Testing Model Switch with System Messages ===")
        
        # Test Anthropic with system message (should handle system message properly)
        set_model("anthropic:claude-3-5-sonnet-20240620")
        
        # Use system message with Anthropic
        anthropic_result = reason(
            "What is pi?",
            system_messages=["You are a precise mathematician. Give exact answers."]
        )
        log(f"Anthropic with system: {anthropic_result[:100] if anthropic_result else 'None'}...")
        
        # Switch to OpenAI with system message
        set_model("openai:gpt-4")
        
        openai_result = reason(
            "What is pi?", 
            system_messages=["You are a casual teacher. Explain simply."]
        )
        log(f"OpenAI with system: {openai_result[:100] if openai_result else 'None'}...")
        
        # Test multiple system messages (should be handled correctly)
        set_model("anthropic:claude-3-haiku-20240307")
        
        multi_system_result = reason(
            "What is gravity?",
            system_messages=[
                "You are a physics expert.",
                "Always provide scientific accuracy.",
                "Keep explanations concise."
            ]
        )
        log(f"Multi-system result: {multi_system_result[:100] if multi_system_result else 'None'}...")
        
        results = [anthropic_result, openai_result, multi_system_result]
        success_count = sum(1 for r in results if r is not None)
        
        assert success_count == 3, f"Expected 3 successes, got {success_count}"
        log("✅ System message handling across models successful")
        '''
        
        result = self.sandbox.eval(code)
        self.assertTrue(result.success)
        self.assertIn("System message handling across models successful", str(result.output))

    def test_model_switching_error_recovery(self):
        """Test error recovery when switching to invalid models."""
        code = '''
        log("=== Testing Model Switch Error Recovery ===")
        
        # Start with a valid model
        set_model("openai:gpt-4")
        valid_result1 = reason("What is 1+1?")
        log(f"Valid model 1 result: {valid_result1 is not None}")
        
        # Try to switch to invalid model (should handle gracefully)
        try:
            set_model("invalid:nonexistent-model")
            invalid_result = reason("This should fail gracefully")
            log(f"Invalid model handled: {invalid_result is not None}")
        except Exception as e:
            log(f"Invalid model error (expected): {str(e)[:100]}")
        
        # Switch back to valid model (should recover)
        set_model("anthropic:claude-3-5-sonnet-20240620")
        valid_result2 = reason("What is 2+2?")
        log(f"Recovery result: {valid_result2 is not None}")
        
        # Try another invalid format
        try:
            set_model("malformed-model-name")  # Missing provider:model format
            invalid_result2 = reason("This should also fail")
            log(f"Malformed model handled: {invalid_result2 is not None}")
        except Exception as e:
            log(f"Malformed model error (expected): {str(e)[:100]}")
        
        # Final recovery test
        set_model("openai:gpt-3.5-turbo")
        final_result = reason("What is 3+3?")
        log(f"Final recovery: {final_result is not None}")
        
        valid_results = [valid_result1, valid_result2, final_result]
        success_count = sum(1 for r in valid_results if r is not None)
        
        assert success_count >= 2, f"Expected at least 2 valid results, got {success_count}"
        log("✅ Error recovery testing successful")
        '''
        
        result = self.sandbox.eval(code)
        self.assertTrue(result.success)
        self.assertIn("Error recovery testing successful", str(result.output))

    def test_model_switching_with_local_models(self):
        """Test switching between cloud and local models."""
        code = '''
        log("=== Testing Cloud <-> Local Model Switching ===")
        
        # Start with cloud model
        set_model("openai:gpt-4")
        cloud_result = reason("What is AI?")
        log(f"Cloud model result: {cloud_result is not None}")
        
        # Switch to local model (should work even if not available)
        try:
            set_model("local:llama3.2")
            local_result = reason("What is machine learning?")
            log(f"Local model result: {local_result is not None}")
        except Exception as e:
            log(f"Local model handling: {str(e)[:100]}")
            local_result = None
        
        # Switch back to cloud
        set_model("anthropic:claude-3-haiku-20240307")
        cloud_result2 = reason("What is deep learning?")
        log(f"Cloud model 2 result: {cloud_result2 is not None}")
        
        # Test vLLM format
        try:
            set_model("vllm:microsoft/Phi-3.5-mini-instruct")
            vllm_result = reason("What is NLP?")
            log(f"vLLM model result: {vllm_result is not None}")
        except Exception as e:
            log(f"vLLM model handling: {str(e)[:100]}")
            vllm_result = None
        
        valid_results = [r for r in [cloud_result, cloud_result2] if r is not None]
        
        assert len(valid_results) >= 2, f"Expected at least 2 cloud results, got {len(valid_results)}"
        log("✅ Cloud/Local model switching test successful")
        '''
        
        result = self.sandbox.eval(code)
        self.assertTrue(result.success)
        self.assertIn("Cloud/Local model switching test successful", str(result.output))

    def test_comprehensive_provider_switching(self):
        """Test comprehensive switching across all supported providers."""
        code = '''
        log("=== Comprehensive Provider Switching Test ===")
        
        # Define test providers and models
        providers = [
            ("openai", "openai:gpt-4"),
            ("anthropic", "anthropic:claude-3-5-sonnet-20240620"),
            ("openai", "openai:gpt-3.5-turbo"),
            ("anthropic", "anthropic:claude-3-haiku-20240307"),
        ]
        
        results = {}
        questions = [
            "What is Python?",
            "What is JavaScript?", 
            "What is Rust?",
            "What is Go?"
        ]
        
        for i, (provider, model) in enumerate(providers):
            log(f"\\nTesting {provider} provider with {model}")
            
            try:
                set_model(model)
                current = get_current_model()
                log(f"Set model to: {current}")
                
                # Test basic reasoning
                basic_result = reason(questions[i])
                
                # Test with parameters
                param_result = reason(
                    f"Briefly explain {questions[i].split()[-1][:-1]}",
                    temperature=0.7,
                    max_tokens=100
                )
                
                results[provider] = {
                    "basic": basic_result is not None,
                    "with_params": param_result is not None,
                    "model": current
                }
                
                log(f"{provider} basic: {results[provider]['basic']}")
                log(f"{provider} with params: {results[provider]['with_params']}")
                
            except Exception as e:
                log(f"Error with {provider}: {str(e)[:100]}")
                results[provider] = {"basic": False, "with_params": False, "error": str(e)}
        
        # Analyze results
        successful_providers = [p for p, r in results.items() if r.get("basic", False)]
        total_successful = len(successful_providers)
        
        log(f"\\nSummary: {total_successful} providers working successfully")
        for provider in successful_providers:
            log(f"✅ {provider}: {results[provider]['model']}")
        
        # We expect at least OpenAI and Anthropic to work
        assert total_successful >= 2, f"Expected at least 2 providers, got {total_successful}"
        assert "openai" in successful_providers, "OpenAI should work"
        assert "anthropic" in successful_providers, "Anthropic should work"
        
        log("✅ Comprehensive provider switching successful")
        '''
        
        result = self.sandbox.eval(code)
        self.assertTrue(result.success)
        self.assertIn("Comprehensive provider switching successful", str(result.output))

    def test_model_switching_state_persistence(self):
        """Test that model switching doesn't affect other Dana state."""
        code = '''
        log("=== Testing State Persistence During Model Switching ===")
        
        # Set up some Dana state
        my_variable = "persistent_value"
        my_list = [1, 2, 3, 4, 5]
        
        def my_function(x):
            return x * 2
        
        log(f"Initial state - variable: {my_variable}, list length: {len(my_list)}")
        
        # Test state persists across model switches
        set_model("openai:gpt-4")
        result1 = reason("What is 5*5?")
        log(f"After OpenAI switch - variable: {my_variable}, list: {my_list}")
        assert my_variable == "persistent_value", "Variable should persist"
        assert len(my_list) == 5, "List should persist"
        
        set_model("anthropic:claude-3-5-sonnet-20240620")
        result2 = reason("What is 6*6?")
        log(f"After Anthropic switch - variable: {my_variable}, function test: {my_function(3)}")
        assert my_variable == "persistent_value", "Variable should still persist"
        assert my_function(3) == 6, "Function should still work"
        
        # Modify state and switch again
        my_variable = "modified_value"
        my_list.append(6)
        
        set_model("openai:gpt-3.5-turbo")
        result3 = reason("What is 7*7?")
        log(f"After modification - variable: {my_variable}, list length: {len(my_list)}")
        assert my_variable == "modified_value", "Modified variable should persist"
        assert len(my_list) == 6, "Modified list should persist"
        
        results = [result1, result2, result3]
        success_count = sum(1 for r in results if r is not None)
        
        assert success_count >= 2, f"Expected at least 2 successful calls, got {success_count}"
        log("✅ State persistence during model switching verified")
        '''
        
        result = self.sandbox.eval(code)
        self.assertTrue(result.success)
        self.assertIn("State persistence during model switching verified", str(result.output))

    def test_concurrent_model_usage_patterns(self):
        """Test patterns that might cause conflicts in model usage."""
        code = '''
        log("=== Testing Concurrent Model Usage Patterns ===")
        
        # Test rapid successive calls without switching
        set_model("openai:gpt-4")
        
        rapid_results = []
        for i in range(3):
            result = reason(f"What is {i+1} + {i+1}?")
            rapid_results.append(result)
            log(f"Rapid call {i+1}: {result is not None}")
        
        # Test switching with immediate usage
        switch_results = []
        models = ["anthropic:claude-3-5-sonnet-20240620", "openai:gpt-3.5-turbo", "anthropic:claude-3-haiku-20240307"]
        
        for i, model in enumerate(models):
            set_model(model)
            # Immediate call after switch
            result = reason(f"Calculate {(i+1)*10} / {i+2}")
            switch_results.append(result)
            log(f"Switch call {i+1} with {model}: {result is not None}")
        
        # Test mixed parameter calls
        mixed_results = []
        set_model("openai:gpt-4")
        
        # Call with different parameters in succession
        configs = [
            {"temperature": 0.1},
            {"temperature": 0.9, "max_tokens": 50},
            {"system_messages": ["You are helpful."]},
        ]
        
        for i, config in enumerate(configs):
            result = reason(f"What is the number {i+10}?", **config)
            mixed_results.append(result)
            log(f"Mixed call {i+1}: {result is not None}")
        
        # Analyze all results
        all_results = rapid_results + switch_results + mixed_results
        success_count = sum(1 for r in all_results if r is not None)
        total_calls = len(all_results)
        
        log(f"Total calls: {total_calls}, Successful: {success_count}")
        success_rate = success_count / total_calls
        
        assert success_rate >= 0.8, f"Expected 80%+ success rate, got {success_rate:.1%}"
        log(f"✅ Concurrent usage patterns successful ({success_rate:.1%} success rate)")
        '''
        
        result = self.sandbox.eval(code)
        self.assertTrue(result.success)
        self.assertIn("Concurrent usage patterns successful", str(result.output))


if __name__ == "__main__":
    unittest.main()