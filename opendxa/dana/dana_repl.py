# run_interactive_repl.py
import asyncio
import os

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.exceptions import DanaError, ParseError
from opendxa.dana.language.parser import ParseResult, parse
from opendxa.dana.runtime.interpreter import LogLevel
from opendxa.dana.runtime.repl import REPL


# Set up history file
HISTORY_FILE = os.path.expanduser("~/.dana_history")


class InputState(Loggable):
    """Tracks the state of multiline input."""
    
    def __init__(self):
        """Initialize the input state."""
        # Initialize Loggable
        super().__init__(logger_name="dana.repl.input_state")
        
        self.buffer = []
        self.in_multiline = False
        self.debug("Initialized input state")
        
    def add_line(self, line):
        """Add a line to the buffer."""
        self.buffer.append(line)
        self.debug(f"Added line to buffer (lines: {len(self.buffer)})")
        
    def get_buffer(self):
        """Get the current buffer as a string."""
        buffer_content = "\n".join(self.buffer)
        self.debug(f"Retrieved buffer content ({len(buffer_content)} chars)")
        return buffer_content
        
    def reset(self):
        """Reset the buffer."""
        self.debug("Resetting input state")
        self.buffer = []
        self.in_multiline = False


class InputCompleteChecker(Loggable):
    """Checks if DANA input is complete."""
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(logger_name="dana.repl.input_checker")
        
    def is_complete(self, code):
        """Check if the input code is a complete DANA statement/block.
        
        Args:
            code: The input code to check
            
        Returns:
            bool: True if the input is complete, False otherwise
        """
        self.debug(f"Checking if input is complete ({len(code)} chars)")
        
        # Handle special case for empty input
        if not code.strip():
            return True
        
        # Check if this is likely natural language input (single word or short phrase)
        words = code.strip().split()
        
        # Single word that starts with a letter is likely natural language
        if len(words) == 1 and words[0] and words[0][0].isalpha():
            self.debug("Detected single word input, treating as complete natural language")
            return True
            
        # Short phrases without DANA syntax are likely natural language
        if len(words) <= 5 and "=" not in code and all("." not in w for w in words) and "(" not in code:
            self.debug("Detected short natural language phrase, treating as complete")
            return True
        
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
                    self.warning("Found unbalanced closing bracket")
                    return True
        
        # Check for incomplete statements
        if stack:  # Unclosed brackets
            self.debug(f"Found unclosed brackets: {stack}")
            return False
            
        # Check for trailing assignment without value
        if code.strip().endswith('='):
            self.debug("Found assignment without value")
            return False
            
        # Check for block statements without body
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.strip().endswith(':'):
                # This is a block statement
                # Check if there's at least one indented line after it
                if i == len(lines) - 1:
                    self.debug("Found block statement without body")
                    return False  # No lines after the block statement
                next_line = lines[i+1]
                if not next_line.startswith(' ') and not next_line.startswith('\t'):
                    self.debug("Found block statement without indented body")
                    return False  # Next line not indented
        
        # Try parsing the code to see if the parser accepts it
        try:
            self.debug("Using parser to check completeness")
            result = parse(code)
            
            # If the parse result has no statements, it's likely incomplete
            if len(result.program.statements) == 0 and code.strip():
                self.debug("No statements found, input may be incomplete")
                return False
                
            # Check for specific errors that indicate incomplete input
            for error in result.errors:
                error_msg = str(error)
                if "Unexpected end of input" in error_msg or "Expected closing" in error_msg:
                    self.debug(f"Parser detected incomplete input: {error_msg}")
                    return False
                    
            self.debug("Input is complete according to parser")
            return True
        except Exception as e:
            # If parsing fails completely but we've passed all other checks,
            # the input is probably complete but invalid (which will be caught during execution)
            self.debug(f"Parser exception during completeness check: {e}")
            return True


class DanaREPLApp(Loggable):
    """Main application class for the DANA REPL."""
    
    def __init__(self):
        """Initialize the DANA REPL application."""
        # Initialize Loggable
        super().__init__(logger_name="dana.repl.app")
        
        # Initialize input checker
        self.input_checker = InputCompleteChecker()
        
    async def run(self):
        """Run the interactive DANA REPL session."""
        self.info("Starting DANA REPL")
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
        self.debug(f"Initialized keywords for autocompletion ({len(keywords)} keywords)")
        
        # Initialize prompt session with history
        session = PromptSession(
            history=FileHistory(HISTORY_FILE),
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter(keywords),
        )
        self.debug("Initialized prompt session with history")

        # --- LLM Initialization (Optional) ---
        llm = None
        try:
            # Attempt to initialize LLM for transcoding and reasoning features
            self.info("Initializing LLM resource")
            print("Initializing LLM resource...")
            # LLMResource will use ConfigLoader and available API keys
            llm = LLMResource(name="reason_llm")
            await llm.initialize()
            self.info(f"LLM resource initialized successfully using model: {llm.model}")
            print(f"✅ LLM resource initialized successfully using model: {llm.model}")
            print("✅ reason() statements and natural language transcoding are enabled.")
        except Exception as e:
            self.warning(f"LLM initialization failed: {e}")
            print(f"⚠️  Warning: LLM initialization failed despite finding API keys: {e}")
            print("Details:", str(e))
            llm = None

        if not llm:
            self.warning("No LLM resource available, transcoding and reasoning disabled")
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
        self.info("Initializing REPL with LLM resource")
        repl = REPL(llm_resource=llm, log_level=LogLevel.INFO)  # Use INFO for execution logs
        
        # Initialize input state
        input_state = InputState()
        self.info("Entering main REPL loop")

        while True:
            try:
                # Determine prompt based on input state
                prompt = ".... " if input_state.in_multiline else "dana> "
                
                # Use prompt_toolkit for input with history support
                self.debug(f"Waiting for input with prompt: {prompt}")
                line = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: session.prompt(prompt)
                )
            
                # Check for exit commands (only when not in multiline mode)
                if not input_state.in_multiline and line.strip().lower() in ["exit", "quit"]:
                    self.info("Exiting REPL")
                    print("Exiting REPL.")
                    break
                    
                # Handle blank lines
                if not line.strip() and not input_state.in_multiline:
                    self.debug("Skipping blank line")
                    continue
                
                # Check for special multiline commands
                if input_state.in_multiline and line.strip() == "##":
                    self.debug("Detected force execution command (##)")
                    # Force execution with double hash (##)
                    try:
                        full_input = input_state.get_buffer()[:-1]  # Remove the ## line
                        self.info("Forcing execution of multiline input")
                        await repl.execute(full_input)
                        # Reset the input state
                        input_state.reset()
                    except DanaError as e:
                        self.error(f"Execution error: {e}")
                        print(f"Error: {e}")
                        # Reset the input state
                        input_state.reset()
                    continue
                
                # Add the line to the input buffer
                input_state.add_line(line)
                
                # Get the full input so far
                full_input = input_state.get_buffer()
                
                # Check if input is complete
                if self.input_checker.is_complete(full_input):
                    # Input is complete, execute it
                    self.debug("Input is complete, executing")
                    try:
                        await repl.execute(full_input)
                        # Reset the input state
                        input_state.reset()
                    except DanaError as e:
                        self.error(f"Execution error: {e}")
                        print(f"Error: {e}")
                        # Reset the input state
                        input_state.reset()
                else:
                    # Input is not complete, continue collecting
                    self.debug("Input is incomplete, continuing to collect")
                    input_state.in_multiline = True

            except DanaError as e:
                self.error(f"DANA error: {e}")
                print(f"Error: {e}")
                # Reset the input state
                input_state.reset()
            except EOFError:  # Handle Ctrl+D
                self.info("Received EOF (Ctrl+D), exiting")
                print("\nExiting REPL.")
                break
            except KeyboardInterrupt:  # Handle Ctrl+C
                self.info("Received keyboard interrupt (Ctrl+C), cancelling input")
                print("\nInput cancelled.")
                # Reset the input state
                input_state.reset()
            except Exception as e:
                self.error(f"Unexpected error: {e}")
                print(f"An unexpected error occurred: {e}")
                # Reset the input state
                input_state.reset()

        # Cleanup LLM resource if needed
        if llm and hasattr(llm, "cleanup") and asyncio.iscoroutinefunction(llm.cleanup):
            self.info("Cleaning up LLM resource")
            await llm.cleanup()
            
        self.info("REPL session ended")


async def main():
    """Entry point for the DANA REPL."""
    app = DanaREPLApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")