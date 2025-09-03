"""LLM reasoning utilities for structured data extraction."""

import json
import os
from typing import Union

from openai import AsyncOpenAI


class LLM:
    """LLM utility for reasoning and structured data extraction."""

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize LLM with specified model."""
        self.model = model
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def reason(self, messages: list[dict[str, str]]) -> str:
        """
        Perform reasoning with text output.

        Args:
            messages: List of message dictionaries with role and content

        Returns:
            Text response from the LLM
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "text"},
        )
        return response.choices[0].message.content or ""

    async def reason_with_structured_output(self, messages: list[dict[str, str]]) -> Union[dict, list]:
        """
        Perform reasoning with structured JSON output.

        Args:
            messages: List of message dictionaries with role and content

        Returns:
            Parsed JSON response (dict or list)
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
