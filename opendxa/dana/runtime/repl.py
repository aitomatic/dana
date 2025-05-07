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

    This class provides an interactive REPL environment for executing DANA programs.
    It supports variable lookup for single-word inputs and has special handling for
    reason() statements that use LLM resources.
    
    When NLP mode is enabled (private.__repl.nlp = True), it will attempt to transcode
    natural language inputs that fail to parse as DANA code.
    """

    def __init__(
        self, llm_resource: Optional[LLMResource] = None, context: Optional[RuntimeContext] = None, 
        log_level: LogLevel = LogLevel.INFO, nlp_mode: bool = False
    ):
        """Initialize the DANA REPL.

        Args:
            llm_resource: Optional LLM resource for reason() statements and transcoding
            context: Optional runtime context for program execution
            log_level: Logging level (default: INFO)
            nlp_mode: Enable natural language processing mode (default: False)
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
        
        # Initialize transcoder if LLM resource is provided
        self.transcoder = None
        if llm_resource:
            # Register the LLM resource with the runtime context for reason() statements
            self.context.register_resource("llm", llm_resource)
            
            # Initialize transcoder for NLP mode
            self.transcoder = FaultTolerantTranscoder(llm_resource)
            
            # Use getattr to safely access name in case it's a mock
            llm_name = getattr(llm_resource, 'name', str(llm_resource))
            self.info(f"Initialized LLM resource for reason() statements: {llm_name}")
            
            if nlp_mode:
                self.info(f"NLP mode enabled - will attempt transcoding for non-DANA inputs")

        # Initialize interpreter with the context
        self.interpreter = Interpreter(self.context)
        self.interpreter.set_log_level(log_level)  # DANA log level
        self.info(f"REPL initialized with log level: {log_level.value}")
        
        # Set up NLP mode in private context
        try:
            # Create __repl namespace in private scope if it doesn't exist
            if "__repl" not in self.context._state["private"]:
                self.context._state["private"]["__repl"] = {}
            
            # Set NLP mode flag
            self.context._state["private"]["__repl"]["nlp"] = nlp_mode
            self.debug(f"NLP mode initialized to: {nlp_mode}")
        except Exception as e:
            self.warning(f"Could not initialize NLP mode flag: {e}")
            
    def is_nlp_mode_enabled(self) -> bool:
        """Check if NLP mode is enabled in the context.
        
        Returns:
            bool: True if NLP mode is enabled, False otherwise
        """
        try:
            return self.context._state["private"].get("__repl", {}).get("nlp", False)
        except Exception:
            return False
            
    def set_nlp_mode(self, enabled: bool) -> None:
        """Enable or disable NLP mode for the REPL.
        
        Args:
            enabled: True to enable NLP mode, False to disable
        """
        try:
            # Create __repl namespace in private scope if it doesn't exist
            if "__repl" not in self.context._state["private"]:
                self.context._state["private"]["__repl"] = {}
                
            # Set NLP mode flag
            self.context._state["private"]["__repl"]["nlp"] = enabled
            self.info(f"NLP mode set to: {enabled}")
        except Exception as e:
            self.warning(f"Could not set NLP mode: {e}")

    async def execute(self, program_source: str, initial_context: Optional[Dict[str, Any]] = None) -> None:
        """Execute a DANA program.

        Args:
            program_source: DANA program source code
            initial_context: Optional initial context values

        Raises:
            DanaError: If program execution fails
        """
        try:
            # Set initial context if provided
            if initial_context:
                for key, value in initial_context.items():
                    self.context.set(key, value)
            
            # Special handling for single word variable references
            # If this is a single word, try to evaluate it as a variable reference
            words = program_source.strip().split()
            if len(words) == 1 and words[0].isalpha():
                var_name = words[0]
                self.debug(f"Attempting to evaluate single word as variable: {var_name}")
                
                # Try all standard scopes
                for scope in ["private", "public", "system"]:
                    try:
                        value = self.context.get(f"{scope}.{var_name}")
                        print(f"{scope}.{var_name} = {value}")
                        return
                    except Exception:
                        # Variable not found in this scope, try next one
                        pass
                        
                # If we get here, the variable wasn't found in any scope
                self.debug(f"Variable '{var_name}' not found in any scope")
                print(f"Variable '{var_name}' not found")
                return
                
            # For everything else, parse as DANA code
            self.debug(f"Parsing input as DANA code: {program_source[:50]}{'...' if len(program_source) > 50 else ''}")
            try:
                parse_result = parse(program_source)
                self.debug("Parsing successful")
            except ParseError as pe:
                self.error(f"Failed to parse program: {pe}")
                
                # Check if NLP mode is enabled and we have a transcoder
                if self.is_nlp_mode_enabled() and self.transcoder:
                    self.info("NLP mode enabled, attempting to transcode input")
                    try:
                        # Attempt to transcode the input
                        transcode_result, cleaned_code = await self.transcoder.transcode(program_source, self.context)
                        
                        if transcode_result.is_valid:
                            self.info("Transcoding successful")
                            if cleaned_code:
                                self.debug(f"Transcoded code: {cleaned_code}")
                            
                            # Use the transcoded result
                            parse_result = transcode_result
                            self.info("Using transcoded DANA code")
                        else:
                            # Transcoding failed to produce valid DANA code
                            self.error(f"Transcoding failed to produce valid DANA code: {transcode_result.error}")
                            raise DanaError(f"Failed to parse program and transcoding failed: {pe}") from pe
                    except TranscoderError as te:
                        # Transcoding process failed
                        self.error(f"Transcoding error: {te}")
                        raise DanaError(f"Failed to parse program and transcoding failed: {te}") from te
                else:
                    # NLP mode disabled or no transcoder available - just raise the original error
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
