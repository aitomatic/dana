# run_interactive_repl.py
import asyncio
import logging

# Make sure aioconsole is installed: pip install aioconsole
# The linter might show an error here if aioconsole is not yet installed.
try:
    import aioconsole
except ImportError:
    print("Please install aioconsole: pip install aioconsole")
    exit(1)

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.exceptions import DanaError
from opendxa.dana.repl import REPL
from opendxa.dana.runtime.interpreter import LogLevel

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(name)s] %(levelname)s - %(message)s")
# Set DANA REPL logger to WARNING to avoid verbose internal logs during interaction
logging.getLogger("opendxa.dana.repl").setLevel(logging.WARNING)


async def main():
    """Runs an interactive DANA REPL session."""
    print("Initializing DANA REPL...")
    print("Type DANA code or natural language. Type 'exit' or 'quit' to end.")

    # --- LLM Initialization (Optional) ---
    # Set environment variables for your LLM API key (e.g., OPENAI_API_KEY)
    # You might need to adjust LLMResource initialization based on your config
    llm = None
    try:
        # Attempt to initialize LLM for transcoding features
        print("Attempting to initialize LLM resource...")
        # Make sure LLMResource uses config loading or has necessary env vars set
        llm = LLMResource()
        await llm.initialize()  # Ensure resource is initialized if needed by implementation
        print("LLM resource initialized successfully.")
    except Exception as e:
        print(f"Warning: Could not initialize LLM resource: {e}")
        print("Natural language transcoding will be disabled.")
        llm = None
    # --- End LLM Initialization ---

    # Initialize REPL
    # Pass the initialized llm resource if available
    repl = REPL(llm_resource=llm, log_level=LogLevel.INFO)  # Use INFO for execution logs

    while True:
        try:
            # Use aioconsole for async input
            line = await aioconsole.ainput("dana> ")
            line = line.strip()

            if line.lower() in ["exit", "quit"]:
                print("Exiting REPL.")
                break
            if not line:
                continue

            # Execute the input
            await repl.execute(line)
            # Successful execution might print logs via the DANA log statement

        except DanaError as e:
            print(f"Error: {e}")
        except EOFError:  # Handle Ctrl+D
            print("\nExiting REPL.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # Optionally break or continue depending on desired robustness
            # break

    # Cleanup LLM resource if needed
    if llm and hasattr(llm, "cleanup") and asyncio.iscoroutinefunction(llm.cleanup):
        await llm.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
