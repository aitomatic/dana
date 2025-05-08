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
            except TranscoderError:
                raise
        else:
            # Direct parsing when NLP mode is off
            parse_result = parse(program_source)

        # Execute the parsed program
        if not parse_result.is_valid:
            raise DanaError(f"Invalid program: {parse_result.errors}")

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
        DXA_LOGGER.setLevel(LEVEL_MAP.get(level, logging.INFO), scope="opendxa.dana")
        # Update interpreter's log level
        self.interpreter.set_log_level(level)
