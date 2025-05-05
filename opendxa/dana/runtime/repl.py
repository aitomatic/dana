"""DANA REPL: Read-Eval-Print Loop for executing and managing DANA programs."""

import asyncio
import logging
from typing import Any, Dict, Optional

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.exceptions import DanaError, ParseError, TranscoderError
from opendxa.dana.language.parser import ParseResult, parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter, LogLevel
from opendxa.dana.transcoder.transcoder import FaultTolerantTranscoder


class REPL:
    """Read-Eval-Print Loop for executing and managing DANA programs.

    This class provides an interactive REPL environment for executing DANA programs,
    with support for both direct DANA code execution and natural language
    input through the transcoder.
    """

    def __init__(
        self, llm_resource: Optional[LLMResource] = None, context: Optional[RuntimeContext] = None, log_level: LogLevel = LogLevel.INFO
    ):
        """Initialize the DANA REPL.

        Args:
            llm_resource: Optional LLM resource for code cleaning and generation
            context: Optional runtime context for program execution
            log_level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # Python logging level

        self.context = context or RuntimeContext()

        # Set up LLM resource if provided
        if llm_resource:
            # Register the LLM resource with the runtime context for reason() statements
            self.context.register_resource("llm", llm_resource)
            # Initialize transcoder with the same LLM resource
            self.transcoder = FaultTolerantTranscoder(llm_resource)
        else:
            self.transcoder = None

        # Initialize interpreter with the context
        self.interpreter = Interpreter(self.context)
        self.interpreter.set_log_level(log_level)  # DANA log level

    async def execute(self, program_source: str, initial_context: Optional[Dict[str, Any]] = None) -> None:
        """Execute a DANA program.

        Args:
            program_source: DANA program source code or natural language description
            initial_context: Optional initial context values

        Raises:
            DanaError: If program execution fails
        """
        try:
            # Set initial context if provided
            if initial_context:
                for key, value in initial_context.items():
                    self.context.set(key, value)

            # Try to transcode if we have an LLM resource
            parse_result: ParseResult
            if self.transcoder:
                try:
                    # transcode now returns a tuple (ParseResult, str | None)
                    parse_result, cleaned_code = await self.transcoder.transcode(program_source, self.context)
                    if cleaned_code:
                        self.logger.info("LLM generated DANA code:\n%s", cleaned_code)
                    if not parse_result.is_valid:
                        raise DanaError(f"Invalid program after transcoding: {parse_result.error}")
                except TranscoderError as e:
                    self.logger.warning(f"Transcoding failed: {e}")
                    # Fall back to direct parsing
                    try:
                        # Try parsing again
                        parse_result = parse(program_source)
                        # If parsing *succeeds* here (unlikely given the test setup, but possible),
                        # we'd continue to execution. The original TranscoderError 'e' is effectively ignored.
                    except ParseError as pe:
                        # Both transcoding and parsing failed.
                        # Raise a new DanaError specifically for this double failure.
                        err_msg = f"Failed to parse program after transcoding failed: {pe}"
                        self.logger.error(err_msg)
                        raise DanaError(err_msg)  # Don't chain the original TranscoderError
                    # If we reach here, parsing succeeded after transcoding failed.
                    # The 'parse_result' from the inner try will be used.

            else:
                # Direct parsing without transcoding
                try:
                    parse_result = parse(program_source)
                except ParseError as pe:
                    self.logger.error(f"Failed to parse program: {pe}")
                    raise DanaError(f"Failed to parse program: {pe}") from pe

            # Execute the program - wrap in try/except for better async error handling
            try:
                self.interpreter.execute_program(parse_result)
            except RuntimeError as e:
                if "Cannot run the event loop while another loop is running" in str(e):
                    # This is a special case for reason() statements in an async context
                    # We'll create and use our own event loop for this execution
                    self.logger.debug("Detected event loop issue with reasoning statements, using alternate approach")
                    # Recreate a nested event loop for the reasoning operation
                    loop = asyncio.new_event_loop()
                    try:
                        # Run _visit_reason_statement_sync on all reason statements in the program
                        from opendxa.dana.language.ast import ReasonStatement

                        for stmt in parse_result.program.statements:
                            if isinstance(stmt, ReasonStatement):
                                self.interpreter._visit_reason_statement_sync(stmt)
                    finally:
                        loop.close()
                else:
                    # For other runtime errors, just re-raise
                    raise

        except DanaError as e:
            # Handle DanaError, including the specific one for double failure.
            # We log it here, and the test will assert the correct message is raised.
            self.logger.error(f"Program execution failed with DanaError: {e}")
            raise  # Re-raise the caught DanaError
        except Exception as e:
            # Catch any other unexpected exceptions
            self.logger.error(f"Program execution failed: {e}")
            raise DanaError(f"Program execution failed: {e}") from e

    def get_context(self) -> RuntimeContext:
        """Get the current runtime context.

        Returns:
            The current runtime context
        """
        return self.interpreter.context

    def set_log_level(self, level: LogLevel) -> None:
        """Set the logging level.

        Args:
            level: Logging level
        """
        self.logger.setLevel(logging.INFO)  # Python logging level
        self.interpreter.set_log_level(level)  # DANA log level
