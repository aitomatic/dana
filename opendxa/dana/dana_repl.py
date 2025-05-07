# run_interactive_repl.py
import asyncio
import logging
import os

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.exceptions import DanaError, ParseError
from opendxa.dana.language.parser import ParseResult, parse
from opendxa.dana.runtime.interpreter import LogLevel
from opendxa.dana.runtime.repl import REPL

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(name)s] %(levelname)s - %(message)s")
# Set DANA REPL logger to WARNING to avoid verbose internal logs during interaction
logging.getLogger("opendxa.dana.repl").setLevel(logging.WARNING)


# Set up history file
HISTORY_FILE = os.path.expanduser("~/.dana_history")


class InputState:
    """Tracks the state of multiline input."""
    
    def __init__(self):
        self.buffer = []
        self.in_multiline = False
        
    def add_line(self, line):
        """Add a line to the buffer."""
        self.buffer.append(line)
        
    def get_buffer(self):
        """Get the current buffer as a string."""
        return "\n".join(self.buffer)
        
    def reset(self):
        """Reset the buffer."""
        self.buffer = []
        self.in_multiline = False


def is_input_complete(code):
    """Check if the input code is a complete DANA statement/block.
    
    Args:
        code: The input code to check
        
    Returns:
        bool: True if the input is complete, False otherwise
    """
    # Check for balanced brackets/braces
    brackets = {'(': ')', '[': ']', '{': '}'}
    stack = []
    
    # Track string literals
    in_string = False
    string_char = None
    
    for char in code:
        # Handle string literals
        if char in ['"', "'"] and (not in_string or char == string_char):
            in_string = not in_string
            string_char = char if in_string else None
            continue
        
        if in_string:
            continue
            
        # Handle brackets
        if char in brackets:
            stack.append(char)
        elif char in brackets.values():
            if not stack or brackets[stack.pop()] != char:
                # Unbalanced closing bracket - syntax error but complete
                return True
    
    # Check for incomplete statements
    if stack:  # Unclosed brackets
        return False
        
    # Check for trailing assignment without value
    if code.strip().endswith('='):
        return False
        
    # Check for block statements without body
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if line.strip().endswith(':'):
            # This is a block statement
            # Check if there's at least one indented line after it
            if i == len(lines) - 1:
                return False  # No lines after the block statement
            next_line = lines[i+1]
            if not next_line.startswith(' ') and not next_line.startswith('\t'):
                return False  # Next line not indented
    
    # Try parsing the code to see if the parser accepts it
    try:
        result = parse(code)
        # Check for specific errors that indicate incomplete input
        for error in result.errors:
            error_msg = str(error)
            if "Unexpected end of input" in error_msg or "Expected closing" in error_msg:
                return False
        return True
    except Exception:
        # If parsing fails completely, it might be incomplete
        return False


async def main():
    """Runs an interactive DANA REPL session."""
    print("Initializing DANA REPL...")
    print("Type DANA code or natural language. Type 'exit' or 'quit' to end.")
    print("For multiline blocks, continue typing - the prompt will change to '.... ' for continuation lines.")
    print("Special commands:")
    print("  - Type '##' on a new line to force execution of a multiline block")
    print("  - Press Ctrl+C to cancel the current input")

    # Create keywords list for autocompletion
    keywords = [
        "exit", "quit", "private", "agent", "world", "temp", "log", "reason",
        "if", "else", "while", "print", "true", "false", "null"
    ]
    
    # Initialize prompt session with history
    session = PromptSession(
        history=FileHistory(HISTORY_FILE),
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter(keywords),
    )

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
    
    # Initialize input state
    input_state = InputState()

    while True:
        try:
            # Determine prompt based on input state
            prompt = ".... " if input_state.in_multiline else "dana> "
            
            # Use prompt_toolkit for input with history support
            line = await asyncio.get_event_loop().run_in_executor(
                None, lambda: session.prompt(prompt)
            )
            
            # Check for exit commands (only when not in multiline mode)
            if not input_state.in_multiline and line.strip().lower() in ["exit", "quit"]:
                print("Exiting REPL.")
                break
                
            # Handle blank lines
            if not line.strip() and not input_state.in_multiline:
                continue
                
            # Check for special multiline commands
            if input_state.in_multiline and line.strip() == "##":
                # Force execution with double hash (##)
                try:
                    full_input = input_state.get_buffer()[:-1]  # Remove the ## line
                    await repl.execute(full_input)
                    # Reset the input state
                    input_state.reset()
                except DanaError as e:
                    print(f"Error: {e}")
                    # Reset the input state
                    input_state.reset()
                continue
                
            # Add the line to the input buffer
            input_state.add_line(line)
            
            # Get the full input so far
            full_input = input_state.get_buffer()
            
            # Check if input is complete
            if is_input_complete(full_input):
                # Input is complete, execute it
                try:
                    await repl.execute(full_input)
                    # Reset the input state
                    input_state.reset()
                except DanaError as e:
                    print(f"Error: {e}")
                    # Reset the input state
                    input_state.reset()
            else:
                # Input is not complete, continue collecting
                input_state.in_multiline = True

        except DanaError as e:
            print(f"Error: {e}")
            # Reset the input state
            input_state.reset()
        except EOFError:  # Handle Ctrl+D
            print("\nExiting REPL.")
            break
        except KeyboardInterrupt:  # Handle Ctrl+C
            print("\nInput cancelled.")
            # Reset the input state
            input_state.reset()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # Reset the input state
            input_state.reset()

    # Cleanup LLM resource if needed
    if llm and hasattr(llm, "cleanup") and asyncio.iscoroutinefunction(llm.cleanup):
        await llm.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")