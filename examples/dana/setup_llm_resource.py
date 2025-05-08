#!/usr/bin/env python
"""Example script demonstrating how to set up an LLM resource for DANA.

This script shows how to:
1. Create and initialize an LLM resource
2. Register it with a RuntimeContext
3. Use it with a DANA program containing reason() statements

Usage:
    python setup_llm_resource.py

Note:
    - This requires at least one LLM API key set in your environment variables
    - See below for supported providers and their environment variables
"""

import asyncio
import os

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter


async def main():
    """Run the example script."""
    print("DANA LLM Resource Setup Example")
    print("===============================")

    # Check for common API keys
    api_keys = {
        "OpenAI": os.environ.get("OPENAI_API_KEY"),
        "Anthropic": os.environ.get("ANTHROPIC_API_KEY"),
        "Azure": os.environ.get("AZURE_OPENAI_API_KEY"),
        "Groq": os.environ.get("GROQ_API_KEY"),
        "Google": os.environ.get("GOOGLE_API_KEY"),
    }

    available_keys = [provider for provider, key in api_keys.items() if key]

    if not available_keys:
        print("⚠️  No LLM API keys found in environment variables.")
        print("This example requires at least one provider's API key to be set.")
        print("\nSupported providers and their environment variables:")
        print("  - OpenAI: OPENAI_API_KEY")
        print("  - Anthropic: ANTHROPIC_API_KEY")
        print("  - Azure: AZURE_OPENAI_API_KEY")
        print("  - Groq: GROQ_API_KEY")
        print("  - Google: GOOGLE_API_KEY")
        return

    print(f"✅ Found API keys for: {', '.join(available_keys)}")

    # Create and initialize LLM resource
    print("\nStep 1: Creating and initializing LLM resource...")

    # Option 1: Simple initialization - uses config and available API keys
    llm = LLMResource(name="reasoning_llm")
    await llm.initialize()
    print(f"LLM initialized with model: {llm.model}")

    # Option 2: With explicit model (uncomment to use)
    # llm = LLMResource(name="reasoning_llm", model="openai:gpt-3.5-turbo")
    # await llm.initialize()

    # Option 3: With custom parameters (uncomment to use)
    # llm = LLMResource(
    #     name="reasoning_llm",
    #     temperature=0.8,
    #     max_tokens=1000,
    # )
    # await llm.initialize()

    # Create runtime context and register LLM resource
    print("\nStep 2: Creating RuntimeContext and registering LLM...")
    context = RuntimeContext()
    context.register_resource("llm", llm)
    print(f"Resources in context: {context.list_resources()}")

    # Create and run a DANA program with reason()
    print("\nStep 3: Running DANA program with reason() statement...")

    # Simple program with reason() statement
    program = """
    log_level INFO
    log.info("Testing reason() statement with registered LLM resource...")
    answer = reason("What are three advantages of using domain-specific languages?")
    log.info(f"LLM response: {answer}")
    """

    # Parse and execute the program
    parse_result = parse(program)
    interpreter = Interpreter(context)
    interpreter.execute_program(parse_result)

    print("\nExample complete!")


if __name__ == "__main__":
    asyncio.run(main())
