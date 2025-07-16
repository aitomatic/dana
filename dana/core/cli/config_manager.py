#!/usr/bin/env python3
"""
DANA Configuration Manager

This module provides interactive configuration management for DANA providers.
It guides users through selecting and configuring LLM providers, creates .env files,
and validates the configuration by testing the reason() function.

Features:
- Interactive provider selection
- Guided configuration setup for each provider
- Environment file generation
- Configuration validation with reason() function
- Retry mechanism for failed configurations
"""

import logging
import os
import sys

from dana.common.config.config_loader import ConfigLoader
from dana.common.exceptions import ConfigurationError
from dana.common.terminal_utils import ColorScheme, supports_color


class ConfigurationManager:
    """Interactive configuration manager for DANA providers."""

    def __init__(self, output_file: str = ".env", debug: bool = False):
        """Initialize the configuration manager.

        Args:
            output_file: Path to the output .env file
            debug: Enable debug logging
        """
        self.output_file = output_file
        self.debug = debug
        self.colors = ColorScheme(supports_color())

        # Load the current dana configuration to get available providers
        try:
            self.config = ConfigLoader().get_default_config()
        except ConfigurationError as e:
            print(f"{self.colors.error(f'Error loading dana configuration: {e}')}")
            sys.exit(1)

        self.providers = self.config.get("llm", {}).get("provider_configs", {})

        # Map providers to their required environment variables and descriptions
        self.provider_info = {
            "openai": {
                "name": "OpenAI",
                "description": "OpenAI GPT models (GPT-4, GPT-4o, etc.)",
                "env_vars": ["OPENAI_API_KEY"],
                "signup_url": "https://platform.openai.com/api-keys",
            },
            "anthropic": {
                "name": "Anthropic",
                "description": "Claude models (Claude 3.5 Sonnet, etc.)",
                "env_vars": ["ANTHROPIC_API_KEY"],
                "signup_url": "https://console.anthropic.com/",
            },
            "azure": {
                "name": "Azure OpenAI",
                "description": "Microsoft Azure OpenAI Service",
                "env_vars": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_URL"],
                "signup_url": "https://azure.microsoft.com/en-us/products/ai-services/openai-service",
            },
            "groq": {
                "name": "Groq",
                "description": "Fast inference with Llama and other models",
                "env_vars": ["GROQ_API_KEY"],
                "signup_url": "https://console.groq.com/keys",
            },
            "mistral": {
                "name": "Mistral AI",
                "description": "Mistral large and other models",
                "env_vars": ["MISTRAL_API_KEY"],
                "signup_url": "https://console.mistral.ai/",
            },
            "google": {
                "name": "Google AI",
                "description": "Gemini models",
                "env_vars": ["GOOGLE_API_KEY"],
                "signup_url": "https://aistudio.google.com/app/apikey",
            },
            "deepseek": {
                "name": "DeepSeek",
                "description": "DeepSeek chat models",
                "env_vars": ["DEEPSEEK_API_KEY"],
                "signup_url": "https://platform.deepseek.com/api_keys",
            },
            "cohere": {
                "name": "Cohere",
                "description": "Cohere command models",
                "env_vars": ["COHERE_API_KEY"],
                "signup_url": "https://dashboard.cohere.ai/api-keys",
            },
            "xai": {"name": "xAI", "description": "Grok models from xAI", "env_vars": ["XAI_API_KEY"], "signup_url": "https://x.ai/"},
            "ibm_watsonx": {
                "name": "IBM Watson X",
                "description": "IBM Watson X AI platform",
                "env_vars": ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_DEPLOYMENT_ID"],
                "signup_url": "https://www.ibm.com/watsonx",
            },
            "local": {
                "name": "Local LLM",
                "description": "Local LLM server (e.g., VLLM, Ollama)",
                "env_vars": ["LOCAL_API_KEY"],
                "signup_url": None,
            },
        }

    def run_configuration_wizard(self) -> bool:
        """Run the interactive configuration wizard.

        Returns:
            True if configuration was successful, False otherwise
        """
        print(f"{self.colors.header('DANA Configuration Wizard')}")
        print()
        print("This wizard will help you configure DANA providers and create a .env file.")
        print("You need at least one provider configured to use DANA's reason() function.")
        print()

        while True:
            # Show available providers
            selected_providers = self._select_providers()
            if not selected_providers:
                print(f"{self.colors.error('No providers selected. Exiting.')}")
                return False

            # Configure each selected provider
            env_vars = {}
            for provider in selected_providers:
                provider_env = self._configure_provider(provider)
                if provider_env:
                    env_vars.update(provider_env)

            if not env_vars:
                print(f"{self.colors.error('No providers were successfully configured.')}")
                continue

            # Write .env file
            self._write_env_file(env_vars)

            # Validate configuration
            print(f"\n{self.colors.accent('Validating configuration...')}")
            if self.validate_configuration():
                print(f"{self.colors.accent('Configuration successful!')}")
                print(f"Environment variables saved to: {self.colors.bold(self.output_file)}")
                return True
            else:
                print(f"{self.colors.error('Configuration validation failed.')}")
                retry = input("Would you like to try again? (y/n): ").lower().strip()
                if retry != "y":
                    return False
                print()

    def _select_providers(self) -> list[str]:
        """Let user select which providers to configure.

        Returns:
            List of selected provider names
        """
        print(f"{self.colors.bold('Available Providers:')}")
        print()

        # Display providers with numbers
        available_providers = []
        for i, (provider_key, provider_info) in enumerate(self.provider_info.items(), 1):
            if provider_key in self.providers:  # Only show providers that are in the config
                available_providers.append(provider_key)
                print(f"{self.colors.accent(f'{i:2d}.')} {provider_info['name']} - {provider_info['description']}")

        print()

        while True:
            try:
                selection = input("Select providers (comma-separated numbers, e.g., 1,3,5): ").strip()
                if not selection:
                    continue

                # Parse selection
                indices = [int(x.strip()) for x in selection.split(",")]
                selected_providers = []

                for idx in indices:
                    if 1 <= idx <= len(available_providers):
                        provider_key = available_providers[idx - 1]
                        selected_providers.append(provider_key)
                    else:
                        print(f"{self.colors.error(f'Invalid selection: {idx}')}")
                        break
                else:
                    # All selections valid
                    if selected_providers:
                        return selected_providers

            except ValueError:
                print(f"{self.colors.error('Please enter valid numbers separated by commas.')}")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return []

    def _configure_provider(self, provider_key: str) -> dict[str, str] | None:
        """Configure a specific provider by prompting for environment variables.

        Args:
            provider_key: The provider key (e.g., 'openai', 'anthropic')

        Returns:
            Dictionary of environment variables, or None if user skipped
        """
        provider_info = self.provider_info[provider_key]

        print(f"\n{self.colors.bold('Configuring ' + provider_info['name'])}")
        print(f"Description: {provider_info['description']}")

        if provider_info.get("signup_url"):
            print(f"Get API key from: {self.colors.accent(provider_info['signup_url'])}")
        print()

        env_vars = {}

        for env_var in provider_info["env_vars"]:
            while True:
                # Check if environment variable already exists
                existing_value = os.getenv(env_var)
                if existing_value:
                    prompt = f"{env_var} (current: {'*' * min(8, len(existing_value))}...): "
                else:
                    prompt = f"{env_var}: "

                try:
                    value = input(prompt).strip()

                    if not value and existing_value:
                        # User pressed enter, keep existing value
                        env_vars[env_var] = existing_value
                        break
                    elif not value:
                        print(f"{self.colors.error(env_var + ' is required for ' + provider_info['name'])}")
                        skip = input("Skip this provider? (y/n): ").lower().strip()
                        if skip == "y":
                            return None
                        continue
                    else:
                        env_vars[env_var] = value
                        break

                except KeyboardInterrupt:
                    print("\nSkipping provider configuration.")
                    return None

        return env_vars

    def _write_env_file(self, env_vars: dict[str, str]):
        """Write environment variables to .env file.

        Args:
            env_vars: Dictionary of environment variable names and values
        """
        # Read existing .env file if it exists
        existing_vars = {}
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            existing_vars[key] = value
            except Exception as e:
                print(f"{self.colors.error(f'Could not read existing .env file: {e}')}")

        # Merge with new variables (new variables take precedence)
        existing_vars.update(env_vars)

        # Write the .env file
        try:
            with open(self.output_file, "w") as f:
                f.write("# DANA Configuration\n")
                f.write("# Generated by 'dana config' command\n\n")

                for key, value in sorted(existing_vars.items()):
                    f.write(f"{key}={value}\n")

            print(f"{self.colors.accent(f'Environment variables written to {self.output_file}')}")

        except Exception as e:
            print(f"{self.colors.error(f'Failed to write .env file: {e}')}")
            raise

    def validate_configuration(self) -> bool:
        """Validate the configuration by testing the reason() function.

        Returns:
            True if validation successful, False otherwise
        """
        try:
            # Load environment variables from .env file if it exists
            if os.path.exists(self.output_file):
                print(f"{self.colors.accent(f'Loading environment variables from {self.output_file}')}")
                self._load_env_file()

            # Clear any cached DanaSandbox shared resources to ensure fresh LLM configuration
            # This prevents reusing LLMResource that was created before API keys were available
            from dana.core.lang.dana_sandbox import DanaSandbox

            DanaSandbox._shared_api_service = None
            DanaSandbox._shared_api_client = None
            DanaSandbox._shared_llm_resource = None
            DanaSandbox._resource_users = 0

            # Create a sandbox and test the reason function
            sandbox = DanaSandbox()
            sandbox.logger.setLevel(logging.CRITICAL)

            # Test with a simple prompt
            test_prompt = "Hello, can you respond with just 'Configuration test successful'?"

            if self.debug:
                print(f"Testing reason function with prompt: {test_prompt}")

            result = sandbox.eval(f'reason("{test_prompt}")', filename="<config-test>")

            if result.success and result.result:
                print(f"{self.colors.accent('✓ Configuration validation successful')}")
                if self.debug:
                    print(f"Response: {result.result}")
                return True
            else:
                print(f"{self.colors.error('✗ Configuration validation failed')}")
                if result.error:
                    print(f"Error: {result.error}")
                return False

        except Exception as e:
            print(f"{self.colors.error('✗ Configuration validation failed')}")
            print(f"Error: {str(e)}")
            if self.debug:
                import traceback

                traceback.print_exc()
            return False

    def _load_env_file(self):
        """Load environment variables from .env file into the current process."""
        try:
            with open(self.output_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key] = value
        except Exception as e:
            if self.debug:
                print(f"Warning: Could not load .env file: {e}")
