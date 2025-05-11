"""DANA REPL: Interactive command-line interface for DANA."""

import asyncio
import logging
import os
from typing import List

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.error_handling import ErrorContext, ErrorHandler
from opendxa.dana.language.ast import LogLevel
from opendxa.dana.runtime.repl import REPL

# Constants
HISTORY_FILE = os.path.expanduser("~/.dana_history")
MULTILINE_PROMPT = ".... "

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {LogLevel.DEBUG: logging.DEBUG, LogLevel.INFO: logging.INFO, LogLevel.WARN: logging.WARNING, LogLevel.ERROR: logging.ERROR}


class InputState(Loggable):
    """Tracks the state of multiline input."""

    def __init__(self):
        """Initialize the input state."""
        super().__init__()
        self.buffer: List[str] = []
        self.in_multiline = False

    def add_line(self, line: str) -> None:
        """Add a line to the buffer."""
        self.buffer.append(line)

    def get_buffer(self) -> str:
        """Get the current buffer as a string."""
        return "\n".join(self.buffer)

    def reset(self) -> None:
        """Reset the buffer."""
        self.buffer = []
        self.in_multiline = False


class InputCompleteChecker(Loggable):
    """Checks if DANA input is complete."""

    def __init__(self):
        """Initialize the checker."""
        super().__init__()

    def is_complete(self, code: str) -> bool:
        """Check if the input code is a complete DANA statement/block."""
        code = code.strip()
        self.debug(f"Checking if complete: '{code}'")

        if not code:
            self.debug("Empty code, considered complete")
            return True

        # Handle simple assignments first
        if "=" in code and ":" not in code:  # Only check = if not in a block
            parts = code.split("=")
            if len(parts) == 2 and parts[1].strip():  # Has a value after =
                self.debug("Valid assignment found")
                return True
            self.debug("Incomplete assignment")
            return False

        # Handle single word variable reference
        if self._is_single_word_variable(code):
            self.debug("Single word variable reference")
            return True

        # Check brackets
        if not self._has_balanced_brackets(code):
            self.debug("Unbalanced brackets")
            return False

        # Check statements
        if not self._has_complete_statements(code):
            self.debug("Incomplete statements")
            return False

        self.debug("Code is complete")
        return True

    def _is_single_word_variable(self, code: str) -> bool:
        """Check if input is a single word variable reference."""
        words = code.strip().split()
        return len(words) == 1 and "." in words[0] and all(part.isalpha() for part in words[0].split("."))

    def _has_balanced_brackets(self, code: str) -> bool:
        """Check if brackets and braces are balanced."""
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []
        in_string = False
        string_char = None

        for char in code:
            if char in ['"', "'"] and (not in_string or char == string_char):
                in_string = not in_string
                string_char = char if in_string else None
                continue

            if in_string:
                continue

            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets[stack.pop()] != char:
                    return False

        return not stack

    def _has_complete_statements(self, code: str) -> bool:
        """Check if all statements are complete."""
        code = code.strip()
        self.debug(f"Checking completeness of:\n{code}")

        # Split into lines and track indentation state
        lines = code.split("\n")
        indent_stack = [0]  # Stack to track expected indentation levels
        self.debug("Starting with indent stack: [0]")

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:  # Skip empty lines
                self.debug(f"Line {i+1}: Skipping empty line")
                continue

            # Count leading spaces to determine indentation level
            indent = len(line) - len(line.lstrip())
            self.debug(f"Line {i+1}: '{line}' (indent={indent}, expected={indent_stack[-1]})")

            # Check block start
            if stripped.endswith(":"):
                if i == len(lines) - 1:  # Block header with no body
                    self.debug(f"Line {i+1}: Block header with no body")
                    return False
                # Next line must be indented
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line:  # If next line is not empty
                        next_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                        if next_indent <= indent:  # Must be more indented
                            self.debug(f"Line {i+1}: Next line not properly indented (next_indent={next_indent})")
                            return False
                indent_stack.append(indent + 4)  # Expect 4 spaces indentation
                self.debug(f"Line {i+1}: Added indent level {indent + 4}, stack is now {indent_stack}")
                continue

            # Check indentation against current expected level
            if indent < indent_stack[-1]:
                # Dedent must match a previous indentation level
                self.debug(f"Line {i+1}: Dedent detected, checking against stack {indent_stack}")
                while indent_stack and indent < indent_stack[-1]:
                    popped = indent_stack.pop()
                    self.debug(f"Line {i+1}: Popped {popped}, stack is now {indent_stack}")
                if not indent_stack or indent != indent_stack[-1]:
                    self.debug(f"Line {i+1}: Invalid dedent level {indent}")
                    return False
            elif indent > indent_stack[-1]:
                # Unexpected indentation
                self.debug(f"Line {i+1}: Unexpected indent level {indent}")
                return False

            # Special handling for else blocks
            if stripped.startswith("else:"):
                if indent != indent_stack[-1]:
                    self.debug(f"Line {i+1}: 'else' at wrong indentation level")
                    return False
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line:  # If next line is not empty
                        next_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                        if next_indent <= indent:  # Must be more indented
                            self.debug(f"Line {i+1}: Next line after 'else' not properly indented")
                            return False

        self.debug("All lines processed successfully")
        return True


class CommandHandler(Loggable):
    """Handles special REPL commands."""

    def __init__(self, repl: REPL):
        """Initialize the command handler."""
        super().__init__()
        self.repl = repl

    async def handle_command(self, cmd: str) -> bool:
        """Handle a special command. Returns True if command was handled."""
        cmd = cmd.strip()

        # Handle help command
        if cmd in ["help", "?", "##help"]:
            self._show_help()
            return True

        # Handle other commands
        if not cmd.startswith("##"):
            return False

        cmd = cmd[2:].strip()  # Remove ## prefix

        if cmd == "nlp on":
            self.repl.set_nlp_mode(True)
            print("✅ NLP mode enabled")
            return True

        if cmd == "nlp off":
            self.repl.set_nlp_mode(False)
            print("❌ NLP mode disabled")
            return True

        if cmd == "nlp status":
            self._show_nlp_status()
            return True

        if cmd == "nlp test":
            await self._run_nlp_test()
            return True

        return False

    def _show_help(self) -> None:
        """Show help information."""
        print("\nDANA REPL Help:")
        print("==============")
        print("Basic Commands:")
        print("  help, ?         - Show this help message")
        print("  exit, quit      - Exit the REPL")
        print("\nSpecial Commands:")
        print("  ##nlp on        - Enable natural language processing mode")
        print("  ##nlp off       - Disable natural language processing mode")
        print("  ##nlp status    - Check if NLP mode is enabled")
        print("  ##nlp test      - Test the NLP transcoder functionality")
        print("\nDANA Syntax:")
        print("  Variables:      private.x = 5, public.data = 'hello'")
        print("  Conditionals:   if private.x > 10: ...")
        print("  Loops:         while private.x < 10: ...")
        print("  Logging:       log.info('message'), log.error('error')")
        print("  Printing:      print('hello world')")
        print("\nTips:")
        print("  - Use Tab for command completion")
        print("  - Press Ctrl+C to cancel current input")
        print("  - Use ## on a new line to force execution of multiline block")
        print()

    def _show_nlp_status(self) -> None:
        """Show NLP mode status."""
        status = self.repl.get_nlp_mode()
        print(f"NLP mode: {'✅ enabled' if status else '❌ disabled'}")
        has_transcoder = self.repl.transcoder is not None
        print(f"LLM resource: {'✅ available' if has_transcoder else '❌ not available'}")

    async def _run_nlp_test(self) -> None:
        """Run NLP transcoder test."""
        if not self.repl.transcoder:
            print("❌ No LLM resource available for transcoding")
            print("Configure an LLM resource by setting one of these environment variables:")
            print("  - OPENAI_API_KEY, ANTHROPIC_API_KEY, AZURE_OPENAI_API_KEY, etc.")
            return

        print("🧪 Testing NLP transcoder with common examples...")
        test_inputs = ["calculate 10 + 20", "add 42 and 17", "print hello world", "if x is greater than 10 then log success"]

        original_mode = self.repl.get_nlp_mode()
        self.repl.set_nlp_mode(True)

        try:
            for test_input in test_inputs:
                print(f"\n➡️ Test input: '{test_input}'")
                try:
                    result = self.repl.execute(test_input)
                    print(f"✅ Execution result:\n{result}")
                except Exception as e:
                    print(f"❌ Execution failed:\n{e}")
        finally:
            self.repl.set_nlp_mode(original_mode)


class DanaREPLApp(Loggable):
    """Main DANA REPL application."""

    def __init__(self, log_level: LogLevel = LogLevel.WARN):
        """Initialize the REPL application.

        Args:
            log_level: Initial log level (default: WARN)
        """
        super().__init__()
        self.input_state = InputState()
        self.input_checker = InputCompleteChecker()
        self.repl = self._setup_repl(log_level)
        self.command_handler = CommandHandler(self.repl)
        self.prompt_session = self._setup_prompt_session()

    def _setup_repl(self, log_level: LogLevel) -> REPL:
        """Set up the REPL instance."""
        repl = REPL(llm_resource=LLMResource(), log_level=log_level)
        return repl

    def _setup_prompt_session(self) -> PromptSession:
        """Set up the prompt session with history and completion."""
        kb = KeyBindings()

        @kb.add(Keys.Tab)
        def _(event):
            """Handle tab completion."""
            b = event.app.current_buffer
            if b.complete_state:
                b.complete_next()
            else:
                b.start_completion(select_first=True)

        keywords = [
            # Commands
            "help",
            "exit",
            "quit",
            # DANA scopes
            "local",
            "private",
            "public",
            "system",
            # Common prefixes
            "local.",
            "private.",
            "public.",
            "system.",
            "log.",
            # Log levels
            "log.debug",
            "log.info",
            "log.warn",
            "log.error",
            # Keywords
            "if",
            "else",
            "while",
            "print",
            "reason",
        ]

        return PromptSession(
            history=FileHistory(HISTORY_FILE),
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter(keywords, ignore_case=True),
            key_bindings=kb,
            multiline=False,
            enable_history_search=True,
            complete_while_typing=True,
            complete_in_thread=True,
            mouse_support=False,  # Disable mouse support to prevent terminal issues
            enable_system_prompt=True,  # Enable system prompt for better terminal compatibility
            enable_suspend=True,  # Allow suspending the REPL with Ctrl+Z
        )

    def _show_welcome(self) -> None:
        """Show welcome message and help."""
        print("Initializing DANA REPL...")
        print("Type DANA code or natural language. Type 'exit' or 'quit' to end.")
        print("For multiline blocks, continue typing - the prompt will change to '.... ' for continuation lines.")
        print("Special commands:")
        print("  - Type '##' on a new line to force execution of a multiline block")
        print("  - Type '##nlp on' to enable natural language processing mode")
        print("  - Type '##nlp off' to disable natural language processing mode")
        print("  - Type '##nlp status' to check if NLP mode is enabled")
        print("  - Type '##nlp test' to test the NLP transcoder functionality")
        print("  - Press Ctrl+C to cancel the current input")

    async def run(self) -> None:
        """Run the interactive DANA REPL session."""
        self.info("Starting DANA REPL")
        self._show_welcome()

        while True:
            try:
                # Get input with appropriate prompt
                prompt = MULTILINE_PROMPT if self.input_state.in_multiline else ">>> "
                line = await self.prompt_session.prompt_async(prompt)
                self.debug(f"Got input: '{line}'")

                # Handle empty lines
                if not line.strip() and not self.input_state.in_multiline:
                    self.debug("Empty line, continuing")
                    continue

                # Handle exit commands
                if line.strip() in ["exit", "quit"]:
                    self.debug("Exit command received")
                    break

                # Handle special commands
                if await self.command_handler.handle_command(line):
                    self.debug("Handled special command")
                    continue

                # Check if input is complete
                is_complete = self.input_checker.is_complete(line)
                self.debug(f"Input complete: {is_complete}")

                # Handle multiline input
                if not is_complete:
                    self.debug("Incomplete input, entering multiline mode")
                    self.input_state.in_multiline = True
                    self.input_state.add_line(line)
                    continue

                # Execute the input
                if self.input_state.in_multiline:
                    self.debug("Executing multiline input")
                    self.input_state.add_line(line)
                    program = self.input_state.get_buffer()
                    self.input_state.reset()
                else:
                    self.debug("Executing single line input")
                    program = line

                try:
                    self.debug(f"Executing program: {program}")
                    result = self.repl.execute(program)
                    # Only print the result if it's not None
                    if result is not None:
                        print(result)
                except Exception as e:
                    context = ErrorContext("program execution")
                    error = ErrorHandler.handle_error(e, context)
                    print(f"Error:\n{error.message}")

            except KeyboardInterrupt:
                print("\nOperation cancelled")
                self.input_state.reset()
            except EOFError:
                break
            except Exception as e:
                context = ErrorContext("REPL operation")
                error = ErrorHandler.handle_error(e, context)
                print(f"Error:\n{error.message}")
                self.input_state.reset()


async def main():
    """Run the DANA REPL."""
    app = DanaREPLApp()
    await app.run()


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
