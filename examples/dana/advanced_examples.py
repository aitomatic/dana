"""Advanced examples demonstrating complex DANA REPL usage patterns."""

import asyncio
import logging

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.repl import REPL
from opendxa.dana.runtime.interpreter import LogLevel


async def run_conditional_example(repl: REPL) -> None:
    """Run example with conditional statements."""
    code = """
    # Set initial temperature
    private.temperature = 25

    # Check temperature and provide appropriate message
    if private.temperature > 30:
        log("Warning: High temperature detected!")
    else:
        log("Temperature is within normal range.")
    """
    await repl.execute(code)


async def run_nested_context_example(repl: REPL) -> None:
    """Run example with nested context variables."""
    initial_context = {
        "private.sensor.temperature": 28,
        "private.sensor.humidity": 65,
        "private.sensor.location": "Room A",
    }
    code = """
    log("Sensor readings from {private.sensor.location}:")
    log("Temperature: {private.sensor.temperature}°C")
    log("Humidity: {private.sensor.humidity}%")
    """
    await repl.execute(code, initial_context)


async def run_error_handling_example(repl: REPL) -> None:
    """Run example demonstrating error handling."""
    # This will cause an error (missing scope)
    error_code = """
    temperature = 25  # Missing scope
    humidity = 60    # Missing scope
    log("Current conditions")
    """
    try:
        await repl.execute(error_code)
    except Exception as e:
        print(f"Caught expected error: {e}")

    # Recovery code with proper scoping
    recovery_code = """
    private.temperature = 25
    private.humidity = 60
    log("Current conditions: {private.temperature}°C, {private.humidity}%")
    """
    await repl.execute(recovery_code)


async def run_complex_natural_language_example(repl: REPL) -> None:
    """Run example with complex natural language input."""
    natural_language = """
    Set up a weather monitoring system that:
    1. Sets the temperature to 28 degrees
    2. Sets the humidity to 75%
    3. Sets the location to 'Outdoor Sensor 1'
    4. Logs all values with appropriate units
    5. Warns if humidity is above 70%
    """
    await repl.execute(natural_language)


async def run_context_persistence_example(repl: REPL) -> None:
    """Run example demonstrating context persistence between executions."""
    # Initialize some values
    init_code = """
    private.counter = 0
    private.max_count = 3
    log("Initialized counter: {private.counter}")
    """
    await repl.execute(init_code)

    # Update and check values
    update_code = """
    private.counter = private.counter + 1
    log("Counter: {private.counter} / {private.max_count}")
    """
    await repl.execute(update_code)


async def main():
    """Run all advanced examples."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create LLM resource for transcoding
    llm = LLMResource(
        name="dana_transcoder",
        config={
            "model": "gpt-4",
            "temperature": 0.7,
        },
    )

    # Initialize DANA REPL with LLM resource
    repl = REPL(llm_resource=llm, log_level=LogLevel.DEBUG)

    # Run all examples
    await run_conditional_example(repl)
    await run_nested_context_example(repl)
    await run_error_handling_example(repl)
    await run_complex_natural_language_example(repl)
    await run_context_persistence_example(repl)


if __name__ == "__main__":
    asyncio.run(main())
