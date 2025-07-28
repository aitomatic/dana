"""Test each AISuite provider individually to isolate the proxies issue."""

import aisuite as ai


def test_individual_providers():
    """Test each provider individually to find the problematic one."""
    print("Testing individual AISuite providers...")

    providers_to_test = {
        "openai": {"api_key": "test-openai-key"},
        "anthropic": {"api_key": "test-anthropic-key"},
        "groq": {"api_key": "test-groq-key"},
        "deepseek": {"api_key": "test-deepseek-key"},
        "cohere": {"api_key": "test-cohere-key"},
        "mistral": {"api_key": "test-mistral-key"},
        "google": {"api_key": "test-google-key"},
    }

    for provider_name, config in providers_to_test.items():
        try:
            provider_configs = {provider_name: config}
            _client = ai.Client(provider_configs=provider_configs)
            print(f"✅ {provider_name} provider works")
        except Exception as e:
            print(f"❌ {provider_name} provider failed: {e}")
            if "proxies" in str(e):
                print(f"   🔍 {provider_name} has the proxies issue!")


if __name__ == "__main__":
    test_individual_providers()
