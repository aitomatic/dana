#!/usr/bin/env python

"""
DANA Reasoning Example

This script demonstrates how to run a DANA program that uses the reason() statement
to integrate with LLM capabilities.
"""

import asyncio
import os
from typing import Any, Dict, Optional

from opendxa.dana.sandbox.interpreter.interpreter import Interpreter

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


async def run_dana_reasoning_example(model: Optional[str] = None, provider: Optional[str] = None) -> None:
    """Run the DANA reasoning example.

    Args:
        model: Optional LLM model name to use (defaults to system default)
        provider: Optional LLM provider to use (defaults to system default)
    """
    # Get the example file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    example_path = os.path.join(current_dir, "code", "reasoning_example.dana")

    # Read the example code
    with open(example_path) as f:
        dana_code = f.read()

    print(f"\n{'='*80}\nRunning DANA Reasoning Example\n{'='*80}\n")
    print(f"Using model: {model or 'default'}")
    print(f"Using provider: {provider or 'default'}")
    print(f"\nDANA Code:\n{'-'*80}")
    print(dana_code)
    print(f"{'-'*80}\n")

    # Parse the DANA code
    parser = DanaParser()
    parse_result = parser.parse(dana_code)

    # Create a runtime context
    context = SandboxContext()

    # Configure and register an LLM resource
    llm_config: Dict[str, Any] = {"name": "example_llm"}
    if model:
        llm_config["model"] = model
    if provider:
        llm_config["provider"] = provider

    llm = LLMResource(**llm_config)
    context.add_resource("llm", llm)

    # Create an interpreter
    interpreter = Interpreter.new(context)

    print(f"Executing DANA code...\n{'-'*80}")

    # Execute the DANA program
    interpreter.execute_program(parse_result)

    print(f"{'-'*80}\nExecution completed!\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run DANA Reasoning Example")
    parser.add_argument("--model", type=str, help="LLM model to use")
    parser.add_argument("--provider", type=str, help="LLM provider to use")

    args = parser.parse_args()

    asyncio.run(run_dana_reasoning_example(args.model, args.provider))
