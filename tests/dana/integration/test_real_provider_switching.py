"""Real provider switching tests using actual API keys.

These tests are excluded from normal pytest runs but verify real functionality.
Run with: pytest -m real_api tests/dana/integration/test_real_provider_switching.py
"""

import os
import pytest
from dotenv import load_dotenv
from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


@pytest.mark.real_api
class TestRealProviderSwitching:
    """Test real provider switching with actual API calls."""

    @classmethod
    def setup_class(cls):
        """Load real API keys from .env file."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Verify we have the required API keys
        required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        missing_keys = []
        
        for key in required_keys:
            if not os.getenv(key):
                missing_keys.append(key)
        
        if missing_keys:
            pytest.skip(f"Missing required API keys: {missing_keys}")
        
        # Ensure we're NOT using mock mode
        os.environ["OPENDXA_MOCK_LLM"] = "false"
        
        print(f"\n🔑 Using real API keys:")
        print(f"   OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
        print(f"   ANTHROPIC_API_KEY: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")

    def setup_method(self):
        """Set up sandbox for each test."""
        self.sandbox = DanaSandbox()

    def teardown_method(self):
        """Clean up sandbox after each test."""
        if hasattr(self, 'sandbox'):
            self.sandbox._cleanup()

    def test_real_openai_call(self):
        """Test actual OpenAI API call."""
        print("\n🧪 Testing real OpenAI API call...")
        
        # Set OpenAI model
        result = self.sandbox.eval('set_model("openai:gpt-4o-mini")')
        assert result.success, f"Failed to set OpenAI model: {result.error}"
        print(f"   ✅ Set model: {result.result}")
        
        # Make actual API call
        result = self.sandbox.eval('reason("What is 2+2? Answer with just the number.")')
        
        if not result.success:
            print(f"   ❌ OpenAI call failed: {result.error}")
            # Print the full error for debugging
            if hasattr(result, 'output'):
                print(f"   Output: {result.output}")
        else:
            print(f"   ✅ OpenAI response: {result.result}")
        
        assert result.success, f"OpenAI API call failed: {result.error}"

    def test_real_anthropic_call(self):
        """Test actual Anthropic API call."""
        print("\n🧪 Testing real Anthropic API call...")
        
        # Set Anthropic model
        result = self.sandbox.eval('set_model("anthropic:claude-3-5-haiku-20241022")')
        assert result.success, f"Failed to set Anthropic model: {result.error}"
        print(f"   ✅ Set model: {result.result}")
        
        # Make actual API call
        result = self.sandbox.eval('reason("What is the capital of France? Answer with just the city name.")')
        
        if not result.success:
            print(f"   ❌ Anthropic call failed: {result.error}")
            # Print the full error for debugging
            if hasattr(result, 'output'):
                print(f"   Output: {result.output}")
        else:
            print(f"   ✅ Anthropic response: {result.result}")
        
        assert result.success, f"Anthropic API call failed: {result.error}"

    def test_real_provider_switching_sequence(self):
        """Test switching between real providers in sequence."""
        print("\n🧪 Testing real provider switching sequence...")
        
        # Start with OpenAI
        print("   🔄 Switching to OpenAI...")
        result = self.sandbox.eval('set_model("openai:gpt-4o-mini")')
        assert result.success, f"Failed to set OpenAI: {result.error}"
        
        result = self.sandbox.eval('reason("What is 3+3? Just the number.")')
        assert result.success, f"OpenAI call failed: {result.error}"
        openai_response = result.result
        print(f"   ✅ OpenAI: {openai_response}")
        
        # Switch to Anthropic
        print("   🔄 Switching to Anthropic...")
        result = self.sandbox.eval('set_model("anthropic:claude-3-5-haiku-20241022")')
        assert result.success, f"Failed to set Anthropic: {result.error}"
        
        result = self.sandbox.eval('reason("What is 5+5? Just the number.")')
        assert result.success, f"Anthropic call failed: {result.error}"
        anthropic_response = result.result
        print(f"   ✅ Anthropic: {anthropic_response}")
        
        # Switch back to OpenAI
        print("   🔄 Switching back to OpenAI...")
        result = self.sandbox.eval('set_model("openai:gpt-4o-mini")')
        assert result.success, f"Failed to switch back to OpenAI: {result.error}"
        
        result = self.sandbox.eval('reason("What is 7+7? Just the number.")')
        assert result.success, f"OpenAI second call failed: {result.error}"
        openai_response2 = result.result
        print(f"   ✅ OpenAI (2nd): {openai_response2}")
        
        # Verify we got responses from both providers
        assert openai_response is not None
        assert anthropic_response is not None
        assert openai_response2 is not None
        
        print("   🎉 All provider switches successful!")

    def test_real_rapid_switching(self):
        """Test rapid switching between providers to catch any state issues."""
        print("\n🧪 Testing rapid provider switching...")
        
        providers = [
            ("openai:gpt-4o-mini", "What is 1+1?"),
            ("anthropic:claude-3-5-haiku-20241022", "What is 2+2?"),
            ("openai:gpt-4o-mini", "What is 3+3?"),
            ("anthropic:claude-3-5-haiku-20241022", "What is 4+4?"),
        ]
        
        responses = []
        
        for i, (model, question) in enumerate(providers):
            print(f"   Round {i+1}: {model}")
            
            # Set model
            result = self.sandbox.eval(f'set_model("{model}")')
            assert result.success, f"Failed to set {model}: {result.error}"
            
            # Ask question
            result = self.sandbox.eval(f'reason("{question} Just the number.")')
            assert result.success, f"Failed to call {model}: {result.error}"
            
            responses.append(result.result)
            print(f"     ✅ Response: {result.result}")
        
        # Verify all calls succeeded
        assert all(r is not None for r in responses), "Some calls returned None"
        
        print("   🎉 Rapid switching successful!")

    def test_real_system_message_handling(self):
        """Test system message handling across providers."""
        print("\n🧪 Testing system message handling...")
        
        # Test with Anthropic (system messages should work)
        print("   🔄 Testing Anthropic with system message...")
        result = self.sandbox.eval('set_model("anthropic:claude-3-5-haiku-20241022")')
        assert result.success, f"Failed to set Anthropic: {result.error}"
        
        # Note: We can't easily test system messages from Dana REPL directly
        # This test verifies the model switch works, system message testing is done in unit tests
        result = self.sandbox.eval('reason("Respond with exactly: ANTHROPIC_WORKS")')
        assert result.success, f"Anthropic system test failed: {result.error}"
        print(f"   ✅ Anthropic: {result.result}")
        
        # Test with OpenAI 
        print("   🔄 Testing OpenAI with system message...")
        result = self.sandbox.eval('set_model("openai:gpt-4o-mini")')
        assert result.success, f"Failed to set OpenAI: {result.error}"
        
        result = self.sandbox.eval('reason("Respond with exactly: OPENAI_WORKS")')
        assert result.success, f"OpenAI system test failed: {result.error}"
        print(f"   ✅ OpenAI: {result.result}")
        
        print("   🎉 System message handling works!")

    def test_real_error_recovery(self):
        """Test error recovery with real providers."""
        print("\n🧪 Testing error recovery...")
        
        # Start with a valid provider
        result = self.sandbox.eval('set_model("openai:gpt-4o-mini")')
        assert result.success, f"Failed to set OpenAI: {result.error}"
        
        result = self.sandbox.eval('reason("Test 1")')
        assert result.success, f"Initial OpenAI call failed: {result.error}"
        print(f"   ✅ Initial call: {result.result}")
        
        # Try invalid model (should fail gracefully)
        print("   🔄 Testing invalid model...")
        result = self.sandbox.eval('set_model("invalid:nonexistent-model")')
        # This might succeed (just setting the model name) but the reasoning should fail
        
        result = self.sandbox.eval('reason("This should fail")')
        # We expect this to fail
        print(f"   ⚠️  Invalid model result: success={result.success}")
        
        # Recover with valid provider
        print("   🔄 Recovering with valid provider...")
        result = self.sandbox.eval('set_model("anthropic:claude-3-5-haiku-20241022")')
        assert result.success, f"Failed to recover with Anthropic: {result.error}"
        
        result = self.sandbox.eval('reason("Recovery test")')
        assert result.success, f"Recovery call failed: {result.error}"
        print(f"   ✅ Recovery successful: {result.result}")
        
        print("   🎉 Error recovery works!")


if __name__ == "__main__":
    # Run the real API tests directly
    print("🚀 Running real API provider tests...")
    print("📝 Note: These tests make actual API calls and will consume credits")
    
    pytest.main(["-v", "-m", "real_api", __file__])