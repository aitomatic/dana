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
from urllib.parse import urlparse

import requests

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
        # Display order for providers in the wizard
        self.provider_display_order: list[str] = [
            "openai",
            "anthropic",
            "azure",
            "groq",
            "mistral",
            "google",
            "deepseek",
            "cohere",
            "xai",
            "ibm_watsonx",
            "local",
        ]

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
                "description": "Local LLM server (e.g., Ollama, vLLM)",
                # Handled by a custom flow; keep for parity
                "env_vars": ["LOCAL_API_KEY", "LOCAL_BASE_URL"],
                "signup_url": None,
            },
        }

    def run_configuration_wizard(self) -> bool:
        """Run the interactive configuration wizard.

        Returns:
            True if configuration was successful, False otherwise
        """
        print(f"{self.colors.header('Dana Configuration Wizard')}")
        print("-------------------------")
        print("Select at least ONE provider so your agents can use reason() and other LLM steps.")
        print("Your selections will be saved to .env.\n")

        # Static, model-agnostic list for clarity
        print(" 1. OpenAI       - GPT-4, GPT-4o, etc.")
        print(" 2. Anthropic    - Claude 3.5, etc.")
        print(" 3. Azure OpenAI - Azure-hosted GPT models")
        print(" 4. Groq         - Fast Llama, etc.")
        print(" 5. Mistral AI   - Mistral large, etc.")
        print(" 6. Google AI    - Gemini models")
        print(" 7. DeepSeek     - DeepSeek chat")
        print(" 8. Cohere       - Cohere command")
        print(" 9. xAI          - Grok models")
        print("10. IBM Watson X - Watson X platform")
        print("11. Local LLM    - Your own server (e.g., Ollama, vLLM)\n")

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
        # Build selection list from configured providers in preferred order
        available_providers: list[str] = []
        for key in self.provider_display_order:
            if key in self.providers:
                available_providers.append(key)

        # Show enumerated list matching the selection indices
        print()
        current_index = 1
        for provider_key in available_providers:
            info = self.provider_info[provider_key]
            print(f"{self.colors.accent(f'{current_index:2d}.')} {info['name']} - {info['description']}")
            current_index += 1
        print()

        while True:
            try:
                selection = input("Select providers (e.g., 1,3,5): ").strip()
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
        # Special flow for Local LLM
        if provider_key == "local":
            return self._configure_local_provider()

        provider_info = self.provider_info[provider_key]

        print(f"\n{self.colors.bold('Configuring ' + provider_info['name'])}")
        print(f"Description: {provider_info['description']}")

        if provider_info.get("signup_url"):
            print(f"Get API key from: {self.colors.accent(provider_info['signup_url'])}")
        print()

        env_vars: dict[str, str] = {}

        for env_var in provider_info["env_vars"]:
            while True:
                existing_value = os.getenv(env_var)
                prompt = (
                    f"{env_var} (current: {'*' * min(8, len(existing_value))}...): "
                    if existing_value
                    else f"{env_var}: "
                )

                try:
                    value = input(prompt).strip()

                    if not value and existing_value:
                        env_vars[env_var] = existing_value
                        break
                    elif not value:
                        print(self.colors.error(f"{env_var} is required for {provider_info['name']}"))
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

    # ===== Local LLM custom flow =====
    def _configure_local_provider(self) -> dict[str, str] | None:
        print("\nLocal LLM (Ollama / vLLM)")
        print("-------------------------")
        print("Use a model server running on THIS machine. No cloud API key is required.\n")
        print("If using Ollama:")
        print("  - Start the server:  ollama serve")
        print("  - Pull a model:      ollama pull <model-name>")
        print("  - Endpoint URL:      http://127.0.0.1:11434/v1\n")
        print("If using vLLM:")
        print("  - Endpoint URL (example): http://127.0.0.1:8000/v1\n")

        detected = self._detect_local_openai_endpoints()
        default_url = detected[0] if detected else "http://127.0.0.1:11434/v1"

        last_url: str | None = os.getenv("LOCAL_BASE_URL") or None
        if last_url:
            default_url = last_url

        # Offer to use detected endpoint if any
        if detected:
            choice = input(f"Found a local server at {detected[0]}. Use this? [Y/n]: ").strip().lower()
            if choice in ("", "y", "yes"):  # accept
                default_url = detected[0]

        # Ask for BASE_URL first
        print("Enter your Local LLM endpoint URL (include /v1):")
        try:
            base_url = input(f"[default: {default_url}]: ").strip() or default_url
        except KeyboardInterrupt:
            print("\nSkipping provider configuration.")
            return None

        # Preflight connectivity message
        print("\nChecking Local LLM at: {0}".format(base_url))
        print("If this hangs or fails, ensure your server is running and at least one model is available.")
        print(f"Quick check:  curl -s {base_url}/models\n")

        # Proxy warning
        if os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY"):
            print(self.colors.accent("Warning: HTTP(S)_PROXY is set and may interfere with localhost connections."))
            print(self.colors.accent("Suggestion: unset HTTP_PROXY and HTTPS_PROXY for local testing."))

        ok, info = self._probe_openai_models(base_url)
        if not ok:
            # Connectivity-centric failure message
            print(self.colors.error(f"✗ Could not reach your Local LLM at: {base_url}"))
            if info:
                print(f"Details: {info}")
            print("\nWhat to try:")
            print("  • If using Ollama:")
            print("      - Start server:  ollama serve")
            print("      - Pull a model:  ollama pull <model-name>")
            print("      - Use URL:       http://127.0.0.1:11434/v1")
            print("  • If using vLLM:")
            print("      - Ensure your server exposes an OpenAI-compatible /v1 route\n")
            print("Tips:")
            print("  • Prefer 127.0.0.1 over localhost")
            print("  • Include the /v1 path in the URL")
            print("  • Unset proxies for localhost:  unset HTTP_PROXY HTTPS_PROXY\n")

            retry = input("Would you like to try again? (y/n): ").strip().lower()
            if retry == "y":
                # Persist last answer as default
                os.environ["LOCAL_BASE_URL"] = base_url
                return self._configure_local_provider()
            # Offer fallback if endpoint is at least reachable with OpenAI semantics
            if info and info.startswith("HTTP 200"):
                use_fallback = input(
                    "We detected an OpenAI-compatible endpoint. Configure OpenAI provider pointing to this BASE_URL instead? (y/N): "
                ).strip().lower()
                if use_fallback == "y":
                    return {"OPENAI_BASE_URL": base_url, "OPENAI_API_KEY": "not-needed"}
            return None

        # Successful probe; ensure at least one model
        # info contains model count description

        # Decide API key behavior: default to not-needed for localhost/127.0.0.1
        host = urlparse(base_url).hostname or ""
        api_key_value = "not-needed"
        if host not in ("127.0.0.1", "localhost"):
            # Non-local host: offer advanced toggle
            adv = input("Advanced: enter a custom API key? (y/N): ").strip().lower()
            if adv == "y":
                try:
                    entered = input('LOCAL_API_KEY (press Enter to use "not-needed"): ').strip()
                    api_key_value = entered or "not-needed"
                except KeyboardInterrupt:
                    print("\nSkipping provider configuration.")
                    return None
        else:
            # Local host: do not prompt; keep not-needed
            pass

        print(self.colors.accent("✓ Local LLM configured"))
        print("Saved to .env:")
        print(f"  LOCAL_BASE_URL={base_url}")
        print(f"  LOCAL_API_KEY={api_key_value}")
        print("Validation succeeded. You can now run Dana agents locally.\n")

        return {"LOCAL_BASE_URL": base_url, "LOCAL_API_KEY": api_key_value}

    def _detect_local_openai_endpoints(self) -> list[str]:
        """Probe common local endpoints and return those that look OpenAI-compatible.

        Returns a list ordered by preference.
        """
        candidates = [
            "http://127.0.0.1:11434/v1",  # Ollama default
            "http://127.0.0.1:8000/v1",   # vLLM common
        ]
        detected: list[str] = []
        for base_url in candidates:
            # Require at least one model to count as a valid detection
            ok, info = self._probe_openai_models(base_url, quick=False)
            if ok:
                detected.append(base_url)
        return detected

    def _probe_openai_models(self, base_url: str, quick: bool = False) -> tuple[bool, str]:
        """Try GET {base_url}/models and verify an OpenAI-style response.

        Returns (ok, info). info contains details like HTTP status or exception.
        """
        url = base_url.rstrip("/") + "/models"
        try:
            resp = requests.get(url, timeout=3 if quick else 8)
            status = resp.status_code
            if status == 401 or status == 403:
                # Auth issue; only mention key if 401/403
                return False, f"HTTP {status} Unauthorized. If your server requires an API key, provide one."
            if status != 200:
                return False, f"HTTP {status} from {url}"
            data = resp.json()
            if not isinstance(data, dict) or "data" not in data or not isinstance(data["data"], list):
                return False, "HTTP 200 but response is not OpenAI /models format"
            # If quick probe, we don't care about model count
            if quick:
                return True, f"HTTP 200 with {len(data['data'])} models"
            if len(data["data"]) == 0:
                return False, "HTTP 200 but no models available (data: [])"
            return True, f"HTTP 200 with {len(data['data'])} models"
        except Exception as e:
            return False, str(e)

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

            # Test: Basic reason function
            print(f"{self.colors.accent('🧠 Testing reason function...')}")
            test_prompt = "Hello, can you respond with just 'Configuration test successful'?"

            if self.debug:
                print(f"Testing reason function with prompt: {test_prompt}")

            result = sandbox.execute_string(f'reason("{test_prompt}")', filename="<config-test>")

            if not (result.success and result.result):
                print(f"{self.colors.error('✗ Reason function validation failed')}")
                if result.error:
                    print(f"Error: {result.error}")
                return False

            print(f"{self.colors.accent('✓ Reason function validation successful')}")
            if self.debug:
                print(f"Response: {result.result}")

            print(f"{self.colors.accent('✓ Overall configuration validation successful')}")
            return True

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
