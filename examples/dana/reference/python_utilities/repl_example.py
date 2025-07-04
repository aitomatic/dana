"""Example demonstrating the usage of the DANA REPL."""

import asyncio
import logging

from dana.common.resource.llm_resource import LLMResource
from dana.core.repl.repl.repl import REPL
from dana.core.lang.log_manager import LogLevel


async def main():
    """Run the DANA REPL example."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create LLM resource for transcoding
    # LLMResource now loads configuration via ConfigLoader (opendxa_config.json)
    # and defaults the name to "default_llm". Ensure API keys are set in your
    # environment or the config file.
    llm = LLMResource()
    await llm.initialize()

    # Initialize DANA REPL with LLM resource
    repl = REPL(llm_resource=llm, log_level=LogLevel.DEBUG)  # Enable detailed logging

    # Example 1: Direct DANA code execution
    print("\nExample 1: Direct DANA code execution")
    dana_code = """
    # Set initial values
    private:temperature = 25
    private:humidity = 60

    # Log the values
    log("Current temperature: {private:temperature}°C")
    log("Current humidity: {private:humidity}%")
    """
    await repl.execute(dana_code)

    # Example 2: Natural language to DANA conversion
    print("\nExample 2: Natural language to DANA conversion")
    natural_language = """
    I want to set up a simple weather monitoring system.
    Set the temperature to 30 degrees and humidity to 70 percent.
    Then log both values with descriptive messages.
    """
    await repl.execute(natural_language)

    # Example 3: Mixed input with some syntax errors
    print("\nExample 3: Mixed input with syntax errors")
    mixed_input = """
    # This is a comment
    temp = 35  # Missing scope
    humidity = 75  # Missing scope
    log the current weather conditions  # Not proper DANA syntax
    """
    await repl.execute(mixed_input)

    # Example 4: Using initial context
    print("\nExample 4: Using initial context")
    initial_context = {"private:location": "San Francisco", "private:units": "metric"}
    await repl.execute('log("Weather report for {private:location} ({private:units})")', initial_context)


if __name__ == "__main__":
    asyncio.run(main())
