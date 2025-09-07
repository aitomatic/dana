"""
Common utility functions for RAG Resource tests.
"""

import os

def has_embedding_api_keys():
    """Check if any embedding API keys are available by reading dana_config.json dynamically."""
    try:
        from dana.common.config.config_loader import ConfigLoader
        
        # Load configuration using Dana's ConfigLoader
        config = ConfigLoader().get_default_config()
        
        # Get embedding provider configs
        embedding_config = config.get("embedding", {})
        provider_configs = embedding_config.get("provider_configs", {})
        
        # Check each provider for required API keys
        for provider_name, provider_config in provider_configs.items():
            # Skip providers that don't require API keys (like huggingface)
            if provider_name == "huggingface":
                continue
                
            # Check if provider has api_key field
            api_key_field = provider_config.get("api_key")
            if api_key_field:
                # Handle env:VARIABLE format
                if isinstance(api_key_field, str) and api_key_field.startswith("env:"):
                    env_var = api_key_field[4:]  # Remove "env:" prefix
                    if os.getenv(env_var):
                        return True
                # Handle direct API key value
                elif api_key_field:
                    return True
            
            # Check for other API key fields that might be named differently
            for key, value in provider_config.items():
                if "key" in key.lower() and isinstance(value, str) and value.startswith("env:"):
                    env_var = value[4:]  # Remove "env:" prefix
                    if os.getenv(env_var):
                        return True
        
        return False
        
    except Exception as e:
        # Fallback to hardcoded check if anything goes wrong
        print(f"Warning: Could not load Dana configuration: {e}")
        fallback_keys = ["OPENAI_API_KEY", "COHERE_API_KEY", "AZURE_OPENAI_API_KEY"]
        return any(os.getenv(key) for key in fallback_keys)
