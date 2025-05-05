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
from opendxa.dana.runtime.interpreter import LogLevel
from opendxa.dana.runtime.repl import REPL

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(name)s] %(levelname)s - %(message)s")
# Set DANA REPL logger to WARNING to avoid verbose internal logs during interaction
logging.getLogger("opendxa.dana.repl").setLevel(logging.WARNING)


async def main():
    """Runs an interactive DANA REPL session."""
    print("Initializing DANA REPL...")
    print("Type DANA code or natural language. Type 'exit' or 'quit' to end.")

    # --- LLM Initialization (Optional) ---
    llm = None
    try:
        # Attempt to initialize LLM for transcoding and reasoning features
        print("Initializing LLM resource...")
        # LLMResource will use ConfigLoader and available API keys
        llm = LLMResource(name="reason_llm")
        await llm.initialize()
        print(f"✅ LLM resource initialized successfully using model: {llm.model}")
        print("✅ reason() statements and natural language transcoding are enabled.")
    except Exception as e:
        print(f"⚠️  Warning: LLM initialization failed despite finding API keys: {e}")
        print("Details:", str(e))
        llm = None

    if not llm:
        print("\nTo enable reason() statements and transcoding, configure LLM API access:")
        print("  1. Set one of these environment variables:")
        print("     - OPENAI_API_KEY        (for OpenAI models)")
        print("     - ANTHROPIC_API_KEY     (for Claude models)")
        print("     - AZURE_OPENAI_API_KEY  (for Azure OpenAI models)")
        print("     - GROQ_API_KEY          (for Groq models)")
        print("     - GOOGLE_API_KEY        (for Google models)")
        print("  2. Or configure in opendxa_config.json with preferred_models")
        print("\nExample: export OPENAI_API_KEY=your_key_here")
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
