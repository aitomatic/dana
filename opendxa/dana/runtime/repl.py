"""DANA REPL: Read-Eval-Print Loop for executing and managing DANA programs."""

from typing import Any, Dict, Optional

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.error_handling import DanaError, ErrorContext, ErrorHandler
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter
from opendxa.dana.transcoder.transcoder import Transcoder


class REPL(Loggable):
    """Read-Eval-Print Loop for executing and managing DANA programs."""

    def __init__(
        self,
        llm_resource: Optional[LLMResource] = None,
        context: Optional[RuntimeContext] = None,
    ):
        """Initialize the DANA REPL."""
        # Initialize Loggable
        super().__init__()

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

        # Special handling for REPL expressions - direct variable lookups
        program_source = program_source.strip()
        # Only handle direct variable references, not statements
        if not program_source.startswith(("if", "while", "print", "log")) and "=" not in program_source:
            # Check for dotted expression like 'private.a' or 'public.b'
            if "." in program_source and len(program_source.split(".")) == 2:
                scope, var_name = program_source.split(".")
                if scope in ["private", "public", "system"] and var_name.isalpha():
                    try:
                        # Direct lookup with no fallbacks for consistency
                        return self.context.get(program_source)
                    except Exception:
                        # Not found in the specified scope
                        raise DanaError(f"Variable '{program_source}' not found")

            # For simple variables, explicitly require a scope
            elif program_source.isalpha():
                # Provide a helpful error message
                raise DanaError(
                    f"Variable '{program_source}' must be accessed with a scope prefix: "
                    f"private.{program_source}, public.{program_source}, or system.{program_source}"
                )

        # If NLP mode is on, use transcoder
        if self.get_nlp_mode():
            if not self.transcoder:
                raise DanaError(
                    "NLP mode is enabled but no LLM resource is available. "
                    "Please set one of these environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY, AZURE_OPENAI_API_KEY, etc."
                )
            try:
                parse_result, _ = await self.transcoder.to_dana(program_source)
            except Exception as e:
                context = ErrorContext("natural language processing")
                error = ErrorHandler.handle_error(e, context)
                if "Generated invalid DANA code" in str(e):
                    raise DanaError("I couldn't understand that. Please try rephrasing your request or use DANA syntax directly.")
                else:
                    # Clean up the error message
                    error_msg = str(error)
                    if "Error during" in error_msg:
                        error_msg = error_msg.split("Error during")[1].strip()
                    raise DanaError(error_msg)
        else:
            # Direct parsing when NLP mode is off
            try:
                parse_result = parse(program_source)
            except Exception as e:
                context = ErrorContext("program parsing")
                error = ErrorHandler.handle_error(e, context)
                # Clean up the error message
                error_msg = str(error)
                if "Error during" in error_msg:
                    error_msg = error_msg.split("Error during")[1].strip()
                raise DanaError(self._format_error_message(error_msg))

        # Execute the parsed program
        if not parse_result.is_valid:
            context = ErrorContext("program validation")
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

            raise DanaError(self._format_error_message(error_msg), context=context)

        try:
            result = self.interpreter.execute_program(parse_result)
            # Try to get the last_value first, then fallback to the result from execute_program
            if "private" in self.context._state and "__last_value" in self.context._state["private"]:
                return self.context.get("private.__last_value")
            return result
        except Exception as e:
            context = ErrorContext("program execution")
            error = ErrorHandler.handle_error(e, context)
            # Clean up the error message
            error_msg = str(error)
            if "Error during" in error_msg:
                error_msg = error_msg.split("Error during")[1].strip()
            raise DanaError(self._format_error_message(error_msg))

    def get_context(self) -> RuntimeContext:
        """Get the current runtime context."""
        return self.context
