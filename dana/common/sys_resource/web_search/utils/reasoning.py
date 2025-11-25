# flake8: noqa: E501
import asyncio
import json
import os
import re
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, cast

from dotenv import load_dotenv
from loguru import logger
from openai import AsyncAzureOpenAI
from openai.types.chat.chat_completion import ChatCompletion

from dana.common.config.config_loader import ConfigLoader

load_dotenv(override=True)


def async_retry(max_retries: int = 3, delay: int = 2) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in async_retry: {e}\nRetrying...")
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries reached. Raising exception.")  # noqa
                        raise
                    await asyncio.sleep(delay)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class AnLLM(ABC):
    """
    This class provides a consistent API for the different LLM services.
    """

    @abstractmethod
    async def reason(self, **kwargs: Any) -> str:
        pass

    @abstractmethod
    async def reason_structure(self, **kwargs: Any) -> dict[str, Any]:
        pass

    def extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from text, handling unescaped control characters in strings."""
        try:
            # First, try to parse the entire text as JSON
            text = text.strip()
            if not text:
                return {}
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # Extract the JSON object from the text
                json_start = text.index("{")
                json_end = text.rfind("}")
                json_str = text[json_start : json_end + 1]

                # Function to escape control characters in string values
                def escape_string(match: re.Match[str]) -> str:
                    s = match.group(0)
                    # Remove the enclosing quotes
                    s = s[1:-1]
                    # Escape backslashes and double quotes
                    s = s.replace("\\", "\\\\").replace('"', '\\"')
                    # Escape control characters
                    s = s.replace("\b", "\\b").replace("\f", "\\f")
                    s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                    # Return the escaped string with quotes
                    return f'"{s}"'

                # Regex pattern to find string values in the JSON
                string_pattern = r'(?P<quote>")(?P<string>.*?)(?P=quote)'
                # Use regex to escape control characters in all string values
                escaped_json_str = re.sub(string_pattern, escape_string, json_str, flags=re.DOTALL)

                # Now, try to parse the escaped JSON string
                return json.loads(escaped_json_str)
            except (ValueError, json.JSONDecodeError) as e:
                logger.error(f"Failed to extract JSON from text: {e}")
                logger.debug(f"Problematic text:\n{text}")
                return {}


class AzureReasoning(AnLLM):
    """
    This class represents the Azure-hosted LLMs for reasoning tasks.
    """

    def __init__(self) -> None:
        config_loader = ConfigLoader()
        config = config_loader.get_default_config()
        preferred_models = config.get("llm", {}).get("preferred_models", [])
        azure_model = next((model for model in preferred_models if model.startswith("azure:")), None)

        if not azure_model:
            raise ValueError("No Azure model specified in llm.preferred_models in dana_config.json")

        self.deployment = azure_model.split(":")[1]
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_API_URL")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self.model = self.deployment

        if not all([self.api_key, self.azure_endpoint, self.api_version]):
            raise ValueError(
                "One or more Azure OpenAI environment variables are not set. "
                "Please set AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_URL, "
                "and AZURE_OPENAI_API_VERSION."
            )

        self._aclient: AsyncAzureOpenAI = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=cast(str, self.azure_endpoint),
            api_version=self.api_version,
        )

    @async_retry()
    async def _raw_completion(self, **kwargs: Any) -> ChatCompletion:
        """Raw API call that returns the complete response object"""
        if "temperature" not in kwargs:
            kwargs["temperature"] = 0
        return await self._aclient.chat.completions.create(model=self.model, **kwargs)  # type: ignore

    async def reason(self, **kwargs: Any) -> str:
        result = await self._raw_completion(**kwargs)
        content = result.choices[0].message.content
        return content if content is not None else ""

    async def reason_structure(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["response_format"] = {"type": "json_object"}
        content = await self.reason(**kwargs)
        return self.extract_json(content)


class ValidateAzure:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Running Azure configuration validation for the first time...")
            cls._instance = super().__new__(cls)
            # Run the validation logic here, only on first creation
            try:
                asyncio.run(cls._instance._validate())
            except Exception as e:
                print(f"An error occurred during validation: {e}")
        else:
            print("Azure configuration has already been validated.")
        return cls._instance

    async def _validate(self):
        reasoning = AzureReasoning()

        print("\n--- Azure Configuration ---")
        # Mask API key for security
        masked_key = (reasoning.api_key[:5] + "..." + reasoning.api_key[-4:]) if reasoning.api_key else "Not set"
        print(f"API Key: {masked_key}")
        print(f"Endpoint: {reasoning.azure_endpoint}")
        print(f"API Version: {reasoning.api_version}")
        print(f"Deployment: {reasoning.deployment}")
        print("---------------------------\n")

        print("Running a simple reasoning test...")
        result = await reasoning.reason_structure(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": "Briefly explain the theory of relativity in simple terms. Output in JSON with a single key 'explanation'.",
                },
            ]
        )
        print("\n--- Test Output ---")
        from pprint import pprint

        pprint(result)
        print("---------------------\n")

        print("Azure configuration and test successful.")


ValidateAzure()

if __name__ == "__main__":
    print("First validation run:")
    ValidateAzure()

    print("\nAttempting second validation run:")
    ValidateAzure()
