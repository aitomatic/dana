"""DANA REPL: Read-Eval-Print Loop for executing and managing DANA programs."""

import logging
from typing import Any, Dict, Optional

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.utils import Misc
from opendxa.dana.common.error_utils import DanaError
from opendxa.dana.language.ast import LogLevel
from opendxa.dana.language.parser import GrammarParser
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.executor.llm_integration import LLMIntegration
from opendxa.dana.runtime.interpreter import Interpreter
from opendxa.dana.runtime.log_manager import LogManager

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {LogLevel.DEBUG: logging.DEBUG, LogLevel.INFO: logging.INFO, LogLevel.WARN: logging.WARNING, LogLevel.ERROR: logging.ERROR}


class REPL(Loggable):
    """Read-Eval-Print Loop for executing and managing DANA programs."""

    def __init__(
        self, llm_resource: Optional[LLMResource] = None, log_level: Optional[LogLevel] = None, context: Optional[RuntimeContext] = None
    ):
        """Initialize the REPL.

        Args:
            llm_resource: Optional LLM resource to use
            context: Optional runtime context to use
        """
        self.context = context or RuntimeContext()
        self.context.set(LLMIntegration.LLM_RESOURCE_VARIABLE, llm_resource)
        self.interpreter = Interpreter(self.context)
        self.parser = GrammarParser()
        self.last_result = None
        if log_level:
            self.set_log_level(log_level)

    def _handle_log_level_change(self, context: Dict[str, Any]) -> None:
        """Handle log level change hook."""
        level = context.get("level")
        if level:
            self.set_log_level(level)

    def set_log_level(self, level: LogLevel) -> None:
        """Set the log level for the REPL.

        This is the only place in opendxa.dana where log levels should be set.

        Args:
            level: The log level to set
        """
        LogManager.set_dana_log_level(level, self.context)
        self.debug(f"Set log level to {level.value}")

    def get_nlp_mode(self) -> bool:
        """Get the current NLP mode state."""
        try:
            return self.context._state["system"].get("__repl", {}).get("nlp", False)
        except Exception:
            return False

    def set_nlp_mode(self, enabled: bool) -> None:
        """Enable or disable NLP mode."""
        try:
            if "system" not in self.context._state:
                self.context._state["system"] = {}
            if "__repl" not in self.context._state["system"]:
                self.context._state["system"]["__repl"] = {}
            self.context._state["system"]["__repl"]["nlp"] = enabled
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

            # Keep only the source line and caret line
            if line.startswith(">") or "^" in line:
                formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def execute(self, program_source: str, initial_context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a DANA program and return the result value.

        Args:
            program_source: The DANA program source code to execute
            initial_context: Optional initial context to set before execution

        Returns:
            The result of executing the program

        Raises:
            DanaError: If the program execution fails
        """
        # Set initial context if provided
        if initial_context:
            for key, value in initial_context.items():
                self.context.set(key, value)

        # Handle NLP mode if enabled
        if self.get_nlp_mode() and self.transcoder:
            self.debug("NLP mode enabled, translating input")
            parse_result, translated_code = Misc.safe_asyncio_run(self.transcoder.to_dana, program_source)
            if parse_result.errors:
                raise DanaError(str(parse_result.errors[0]))
            program_source = translated_code
            print(f"Translated to: {program_source}")

        # Parse and execute the program
        try:
            # Parse the program (synchronous operation)
            parse_result = self.parser.parse(program_source)
            if parse_result.errors:
                raise DanaError(str(parse_result.errors[0]))

            # Execute the program (synchronous operation)
            result = self.interpreter.execute_program(parse_result)
            return result
        except Exception as e:
            raise DanaError(str(e))

    def get_context(self) -> RuntimeContext:
        """Get the current runtime context."""
        return self.context
