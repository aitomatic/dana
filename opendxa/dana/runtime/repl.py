"""DANA REPL: Read-Eval-Print Loop for executing and managing DANA programs."""

import logging
from typing import Any, Dict, Optional

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER
from opendxa.dana.exceptions import DanaError, TranscoderError
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter, LogLevel
from opendxa.dana.transcoder.transcoder import Transcoder

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {LogLevel.DEBUG: logging.DEBUG, LogLevel.INFO: logging.INFO, LogLevel.WARN: logging.WARNING, LogLevel.ERROR: logging.ERROR}


class REPL(Loggable):
    """Read-Eval-Print Loop for executing and managing DANA programs."""

    def __init__(
        self,
        llm_resource: Optional[LLMResource] = None,
        context: Optional[RuntimeContext] = None,
        log_level: LogLevel = LogLevel.INFO,
    ):
        """Initialize the DANA REPL."""
        # Initialize Loggable
        super().__init__()

        # Set up logging
        DXA_LOGGER.setLevel(LEVEL_MAP.get(log_level, logging.INFO), scope="opendxa.dana")

        # Set up context
        self.context = context or RuntimeContext()
        if "private" not in self.context._state:
            self.context._state["private"] = {}
        if "__repl" not in self.context._state["private"]:
            self.context._state["private"]["__repl"] = {}
        self.context._state["private"]["__repl"]["nlp"] = False  # Default to disabled

        # Set up transcoder if LLM resource is available
        self.transcoder = None
        if llm_resource:
            self.context.register_resource("llm", llm_resource)
            try:
                self.transcoder = Transcoder(llm_resource)
                self.info(f"Initialized LLM resource: {llm_resource.model}")
            except Exception as e:
                self.error(f"Failed to initialize transcoder: {e}")

        # Set up interpreter
        self.interpreter = Interpreter(self.context)
        self.interpreter.set_log_level(log_level)

    def get_nlp_mode(self) -> bool:
        """Get the current NLP mode state."""
        try:
            return self.context._state["private"].get("__repl", {}).get("nlp", False)
        except Exception:
            return False

    def set_nlp_mode(self, enabled: bool) -> None:
        """Enable or disable NLP mode."""
        try:
            if "private" not in self.context._state:
                self.context._state["private"] = {}
            if "__repl" not in self.context._state["private"]:
                self.context._state["private"]["__repl"] = {}
            self.context._state["private"]["__repl"]["nlp"] = enabled
            self.info(f"NLP mode set to: {enabled}")
        except Exception as e:
            self.error(f"Could not set NLP mode: {e}")
            raise DanaError(f"Failed to set NLP mode: {e}")

    def _format_error_message(self, error_msg: str) -> str:
        """Format an error message to be more user-friendly.

        Args:
            error_msg: The raw error message

        Returns:
            A formatted, user-friendly error message
        """
        # Remove DANA Error prefix if present
        if "DANA Error" in error_msg:
            error_msg = error_msg.split("DANA Error")[1].strip()
            if error_msg.startswith("("):
                error_msg = error_msg[error_msg.find(")") + 1 :].strip()

        # Clean up the error message
        lines = error_msg.split("\n")
        formatted_lines = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Clean up the line
            line = line.strip()

            # Skip lines with just carets or arrows
            if line.strip() in ["^", ">", "A"]:
                continue

            # Clean up expected tokens
            if "Expected:" in line:
                tokens = line.split("Expected:")[1].strip()
                tokens = tokens.replace("LPAR", "(").replace("RPAR", ")").replace("EQUAL", "=")
                line = f"Expected: {tokens}"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    async def execute(self, program_source: str, initial_context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a DANA program and return the result value."""
        # Set initial context if provided
        if initial_context:
            for key, value in initial_context.items():
                self.context.set(key, value)

        # Try single word variable lookup first
        words = program_source.strip().split()
        if len(words) == 1 and words[0].isalpha():
            for scope in ["private", "public", "system"]:
                try:
                    return self.context.get(f"{scope}.{words[0]}")
                except Exception:
                    continue

        # If NLP mode is on, use transcoder
        if self.get_nlp_mode():
            if not self.transcoder:
                raise DanaError("NLP mode is enabled but no LLM resource is available")
            try:
                parse_result, _ = await self.transcoder.to_dana(program_source)
            except TranscoderError as e:
                # Provide a more user-friendly error message for natural language input
                if "Generated invalid DANA code" in str(e):
                    raise DanaError("I couldn't understand that. Please try rephrasing your request or use DANA syntax directly.")
                else:
                    raise DanaError(f"Error processing your request: {str(e)}")
        else:
            # Direct parsing when NLP mode is off
            parse_result = parse(program_source)

        # Execute the parsed program
        if not parse_result.is_valid:
            # Clean up error messages for better readability
            error_msg = str(parse_result.errors)
            if "ParseError" in error_msg:
                # Extract just the error message without the ParseError wrapper
                error_parts = error_msg.split("ParseError(")
                if len(error_parts) > 1:
                    # Get everything between the first ( and the last )
                    error_content = error_parts[1]
                    # Find the last closing parenthesis
                    last_paren = error_content.rfind(")")
                    if last_paren != -1:
                        error_msg = error_content[:last_paren]
                        # Remove quotes if present
                        if error_msg.startswith('"') and error_msg.endswith('"'):
                            error_msg = error_msg[1:-1]

            # Format the error message to be more user-friendly
            error_msg = self._format_error_message(error_msg)
            raise DanaError(error_msg)

        try:
            self.interpreter.execute_program(parse_result)
            # Return the last value in the context if available
            return self.context.get("private.__last_value") if "private.__last_value" in self.context._state["private"] else None
        except Exception as e:
            raise DanaError(f"Execution failed: {e}")

    def get_context(self) -> RuntimeContext:
        """Get the current runtime context."""
        return self.context

    def set_log_level(self, level: LogLevel) -> None:
        """Set the logging level."""
        # Set level for all loggers under opendxa.dana
        DXA_LOGGER.setLevel(LEVEL_MAP.get(level, logging.WARN), scope="opendxa.dana")
        # Update interpreter's log level
        self.interpreter.set_log_level(level)
