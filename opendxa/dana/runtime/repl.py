"""DANA REPL: Read-Eval-Print Loop for executing and managing DANA programs."""

import asyncio
import logging
from typing import Any, Dict, Optional, cast

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.exceptions import DanaError, ParseError, TranscoderError
from opendxa.dana.language.parser import ParseResult, parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter, LogLevel
from opendxa.dana.transcoder.transcoder import FaultTolerantTranscoder


class REPL(Loggable):
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
        # Initialize Loggable
        super().__init__(logger_name="dana.repl")
        
        # Set Python logging level based on DANA log level
        python_log_level = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARN: logging.WARNING,
            LogLevel.ERROR: logging.ERROR
        }.get(log_level, logging.INFO)
        
        self.logger.setLevel(python_log_level)

        self.context = context or RuntimeContext()

        # Set up LLM resource if provided
        if llm_resource:
            # Register the LLM resource with the runtime context for reason() statements
            self.context.register_resource("llm", llm_resource)
            # Initialize transcoder with the same LLM resource
            self.transcoder = FaultTolerantTranscoder(llm_resource)
            # Use getattr to safely access name in case it's a mock
            llm_name = getattr(llm_resource, 'name', str(llm_resource))
            self.info(f"Initialized transcoder with LLM resource: {llm_name}")
        else:
            self.transcoder = None
            self.warning("No LLM resource provided, transcoding disabled")

        # Initialize interpreter with the context
        self.interpreter = Interpreter(self.context)
        self.interpreter.set_log_level(log_level)  # DANA log level
        self.info(f"REPL initialized with log level: {log_level.value}")

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
                    self.debug(f"Attempting to transcode input: {program_source[:50]}{'...' if len(program_source) > 50 else ''}")
                    parse_result, cleaned_code = await self.transcoder.transcode(program_source, self.context)
                    if cleaned_code:
                        self.info(f"LLM generated DANA code:\n{cleaned_code}")
                    if not parse_result.is_valid:
                        self.error(f"Invalid program after transcoding: {parse_result.error}")
                        raise DanaError(f"Invalid program after transcoding: {parse_result.error}")
                except TranscoderError as e:
                    self.warning(f"Transcoding failed: {e}")
                    self.info("Falling back to direct parsing")
                    # Fall back to direct parsing
                    try:
                        # Try parsing again
                        parse_result = parse(program_source)
                        self.debug("Direct parsing successful")
                        # If parsing *succeeds* here (unlikely given the test setup, but possible),
                        # we'd continue to execution. The original TranscoderError 'e' is effectively ignored.
                    except ParseError as pe:
                        # Both transcoding and parsing failed.
                        # Raise a new DanaError specifically for this double failure.
                        err_msg = f"Failed to parse program after transcoding failed: {pe}"
                        self.error(err_msg)
                        raise DanaError(err_msg)  # Don't chain the original TranscoderError
                    # If we reach here, parsing succeeded after transcoding failed.
                    # The 'parse_result' from the inner try will be used.

            else:
                # Direct parsing without transcoding
                self.debug("No transcoder available, using direct parsing")
                try:
                    parse_result = parse(program_source)
                    self.debug("Direct parsing successful")
                except ParseError as pe:
                    self.error(f"Failed to parse program: {pe}")
                    raise DanaError(f"Failed to parse program: {pe}") from pe

            # Special handling for REPL-style statements with type errors
            # If this looks like a simple log/print statement or reason statement with undefined variable errors,
            # we can try to execute it anyway since our runtime resolution might handle it
            from opendxa.dana.exceptions import TypeError
            from opendxa.dana.language.ast import LogStatement, PrintStatement, ReasonStatement

            # Check if this is a single statement in REPL context
            is_single_statement = len(parse_result.program.statements) == 1
            is_special_statement = False

            if is_single_statement:
                stmt = parse_result.program.statements[0]
                is_special_statement = isinstance(stmt, (LogStatement, PrintStatement, ReasonStatement))

            # Check if errors are only undefined variable errors we might resolve at runtime
            has_only_undefined_var_errors = False
            if parse_result.errors:
                has_only_undefined_var_errors = all(
                    isinstance(err, TypeError) and "Undefined variable" in str(err) for err in parse_result.errors
                )

            # Special case for a reason statement - these always need special handling in REPL
            is_reason_statement = is_single_statement and isinstance(parse_result.program.statements[0], ReasonStatement)

            # For simple REPL expressions with just undefined variable errors or reason statements,
            # try executing without the errors and see if runtime resolution helps
            if is_single_statement and ((is_special_statement and has_only_undefined_var_errors) or is_reason_statement):
                # Create a clean version of the parse result without the errors
                clean_parse_result = ParseResult(program=parse_result.program, errors=[])  # No errors to let it execute

                try:
                    # For reason statements, we need to use the special sync reason method
                    if is_reason_statement:
                        # Get the reason statement from the program
                        reason_stmt = parse_result.program.statements[0]
                        self.debug("Processing reason statement synchronously")

                        # Verify that the reason statement has a valid prompt before proceeding
                        if reason_stmt.prompt is None:
                            # For direct reason() calls, we need to extract the prompt from the program text
                            self.debug("Fixing null prompt in reason statement")
                            try:
                                # Handle f-strings special case first
                                if 'reason(f"' in program_source or "reason(f'" in program_source:
                                    # For f-strings, we need to preserve the original as an f-string expression
                                    # The safest approach is to just set a default prompt and let the interpreter
                                    # correctly evaluate the f-string later
                                    self.debug("Detected f-string prompt in reason statement")
                                    # Set a default prompt that will be overridden at execution time
                                    from opendxa.dana.language.ast import FStringExpression, Literal, LiteralExpression

                                    # Extract the f-string portions
                                    if 'reason(f"' in program_source:
                                        start_idx = program_source.find('reason(f"') + 9
                                        end_idx = program_source.find('")', start_idx)
                                    else:  # reason(f'
                                        start_idx = program_source.find("reason(f'") + 9
                                        end_idx = program_source.find("')", start_idx)

                                    if start_idx >= 9 and end_idx > start_idx:
                                        # Create an f-string with the original text
                                        fs_text = program_source[start_idx:end_idx]
                                        # Create a proper FStringExpression
                                        from opendxa.dana.language.ast import FStringExpression

                                        fstring_expr = FStringExpression(parts=[fs_text])
                                        setattr(fstring_expr, "_is_fstring", True)
                                        setattr(fstring_expr, "_original_text", fs_text)
                                        reason_stmt.prompt = LiteralExpression(literal=Literal(value=fstring_expr))
                                    else:
                                        # If parsing fails, set a generic prompt
                                        reason_stmt.prompt = LiteralExpression(literal=Literal(value="f-string prompt"))

                                # Extract normal strings
                                elif 'reason("' in program_source:
                                    # Extract the text between quotes
                                    start_idx = program_source.find('reason("') + 8
                                    end_idx = program_source.find('")', start_idx)
                                    if start_idx >= 8 and end_idx > start_idx:
                                        prompt_text = program_source[start_idx:end_idx]
                                        # Create a new prompt
                                        from opendxa.dana.language.ast import Literal, LiteralExpression

                                        reason_stmt.prompt = LiteralExpression(literal=Literal(value=prompt_text))
                                elif "reason('" in program_source:
                                    # Handle single quotes
                                    start_idx = program_source.find("reason('") + 8
                                    end_idx = program_source.find("')", start_idx)
                                    if start_idx >= 8 and end_idx > start_idx:
                                        prompt_text = program_source[start_idx:end_idx]
                                        from opendxa.dana.language.ast import Literal, LiteralExpression

                                        reason_stmt.prompt = LiteralExpression(literal=Literal(value=prompt_text))
                                else:
                                    raise RuntimeError("Reason statement must have a prompt")
                            except Exception as e:
                                self.error(f"Error extracting prompt: {e}")
                                raise RuntimeError("Reason statement must have a prompt")

                        # Call the sync method directly
                        self.interpreter._visit_reason_statement_sync(cast(ReasonStatement, reason_stmt))
                        # If we got here, it worked!
                        return
                    else:
                        # For other statements, try normal execution path
                        self.interpreter.execute_program(clean_parse_result)
                        return  # If we get here, it worked! No need to continue.
                except Exception as e:
                    # If execution still fails, fall back to the original parse_result
                    self.debug(f"Attempted runtime resolution failed: {e}")

            # Normal execution path for all other cases
            try:
                self.interpreter.execute_program(parse_result)
            except RuntimeError as e:
                if "Cannot run the event loop while another loop is running" in str(e):
                    # This is a special case for reason() statements in an async context
                    # We'll create and use our own event loop for this execution
                    self.debug("Detected event loop issue with reasoning statements, using alternate approach")
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
            self.error(f"Program execution failed with DanaError: {e}")
            raise  # Re-raise the caught DanaError
        except Exception as e:
            # Catch any other unexpected exceptions
            self.error(f"Program execution failed: {e}")
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
        # Map DANA log level to Python log level
        python_log_level = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARN: logging.WARNING,
            LogLevel.ERROR: logging.ERROR
        }.get(level, logging.INFO)
        
        # Update Loggable logger level
        self.logger.setLevel(python_log_level)
        
        # Update interpreter log level
        self.interpreter.set_log_level(level)
        
        self.debug(f"Log level set to {level.value}")
