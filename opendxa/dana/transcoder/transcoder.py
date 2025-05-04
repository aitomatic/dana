"""Fault-tolerant transcoder for DANA programs."""

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest
from opendxa.dana.exceptions import DanaError, ParseError
from opendxa.dana.language.parser import ParseResult, parse
from opendxa.dana.language.validator import ValidationResult, validate_program
from opendxa.dana.runtime.context import RuntimeContext


class TranscoderError(DanaError):
    """Error during transcoding process."""

    def __init__(self, message: str, original_input: str, cleaned_input: str):
        self.original_input = original_input
        self.cleaned_input = cleaned_input
        super().__init__(message)


class FaultTolerantTranscoder:
    """Handles mixed natural language and DANA code, with error correction."""

    def __init__(self, llm_resource: LLMResource):
        """Initialize the transcoder with an LLM resource.

        Args:
            llm_resource: LLM resource for code cleaning and generation
        """
        self.llm = llm_resource

    async def transcode(self, input_text: str, context: RuntimeContext) -> tuple[ParseResult, str | None]:
        """Convert mixed natural language and DANA code into valid DANA.

        If LLM cleaning is required, the cleaned code is also returned.

        Args:
            input_text: Mixed natural language and DANA code
            context: Runtime context for validation

        Returns:
            A tuple containing:
                - ParseResult: Contains the valid DANA program.
                - str | None: The cleaned DANA code string if LLM cleaning was performed,
                  otherwise None.

        Raises:
            TranscoderError: If transcoding fails after all attempts
        """
        # 1. Try direct parsing first
        cleaned_code = None
        try:
            result = parse(input_text)
            if result.is_valid:
                # Return the successful parse result and None for cleaned code
                return result, None
        except ParseError:
            pass  # Proceed to cleaning

        # 2. Try cleaning with LLM
        cleaned_code = await self._clean_with_llm(input_text)
        try:
            result = parse(cleaned_code)
            if result.is_valid:
                # Return the successful parse result and the cleaned code
                return result, cleaned_code
        except ParseError as e:
            # Raise error, including original and cleaned input
            raise TranscoderError(
                f"Failed to transcode input after cleaning: {str(e)}",
                input_text,
                cleaned_code,
            ) from e

        # If we get here, parsing the cleaned code must have failed
        # (but the parse function didn't raise ParseError for some reason,
        # or the is_valid check failed silently). Raise an error.
        # Note: cleaned_code will contain the LLM output here.
        raise TranscoderError(
            "Transcoding failed: Could not parse the cleaned code.",
            input_text,
            cleaned_code or "LLM cleaning did not produce output",
        )

    async def _clean_with_llm(self, input_text: str) -> str:
        """Use LLM to clean and format the input.

        Args:
            input_text: Mixed natural language and DANA code

        Returns:
            Cleaned and formatted DANA code
        """
        prompt = f"""
        You are an expert DANA programmer. Your task is to translate the following input,
        which might be mixed natural language and DANA-like code, into a valid DANA program.

        Input:
        ```
        {input_text}
        ```

        Follow these rules strictly:
        1. The output MUST be valid DANA code that can be parsed and executed. This is non-negotiable.
        2. Preserve the original intent of the input while making it valid DANA code.
        3. Output ONLY valid DANA code. No explanations, apologies, or markdown formatting.
        4. Fix any syntax errors, missing scopes, or invalid expressions.
        5. Add helpful comments (# comment) to clarify complex logic or important decisions.
        6. Ensure proper scoping for variables using standard DANA prefixes:
           - temp: for temporary variables
           - agent: for agent-specific state
           - world: for world/environment state
           - execution: for execution context
           Example: temp:my_var = 10, agent:status = "active"
        7. Handle common user mistakes and natural language:
           - Add missing scopes to variables
           - Convert natural language commands to proper DANA expressions
             Example: "log some string" -> temp:log = "some string"
           - Fix incorrect operator usage (e.g., = vs ==)
           - Add proper indentation for blocks
           - Convert informal variable names to valid DANA identifiers
           - Handle imperative statements by converting to appropriate DANA operations
           - Convert natural language conditions to proper boolean expressions
        8. Validation Checklist (MUST pass all):
           - Every variable has a proper scope prefix
           - All expressions use valid DANA operators
           - All conditionals follow DANA syntax
           - All assignments use proper DANA syntax
           - No unsupported features (loops, functions)
           - Proper indentation for all blocks
           - Valid identifiers following DANA rules
        9. Adhere to DANA syntax rules:

        DANA Syntax Reference:
        - Structure: Code is a sequence of instructions. Indentation defines blocks (like Python).
        - Comments: Start with #.
        - Assignments: scope:variable = value
          Example: temp:result = "done", world:data.value = 5
        - Conditionals: if condition: followed by indented block. else: is optional.
        - LLM Calls: reason(prompt: str, context: dict)
          Example: temp:analysis = reason("Is this okay?", context=world:sensor)
        - KB/Subprogram Calls: use(id: str)
          Example: use("kb.common.error_handling.v1")
        - State Setting: set(key: str, value)
          Example: set("execution:status", "running")
        - Types: Strings ("quoted"), Numbers (123, 4.5), Booleans (true, false)
        - Expressions: Use comparison operators (==, !=, <, >, <=, >=), boolean logic (and, or),
          and containment (in)
        - Identifiers: [a-zA-Z_][a-zA-Z0-9_.]* (dots for scoping within identifiers)
        - Not Supported: Loops (for, while), function definitions (def)

        Common Natural Language Patterns:
        - "log X" -> temp:log = "X"
        - "set X to Y" -> temp:X = Y
        - "if X then Y" -> if X: Y
        - "check if X" -> if X:
        - "when X happens" -> if X:
        - "store X as Y" -> temp:Y = X
        - "get X from Y" -> temp:X = Y:X
        - "update X with Y" -> X = Y

        Final Validation:
        Before outputting, verify that:
        1. The code follows ALL DANA syntax rules
        2. All variables are properly scoped
        3. All expressions are valid DANA expressions
        4. The code can be parsed and executed without errors
        5. Natural language has been properly converted to valid DANA syntax

        Translate the input above into clean, valid DANA code.
        """
        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": prompt}],
                "system_messages": [
                    "You are a DANA code generation expert. Your sole task is to translate potentially mixed input",
                    "into valid DANA syntax according to the provided rules and syntax reference.",
                    "Output *only* valid DANA code. Do not add any conversational text, markdown formatting",
                    "for the code block, or explanations.",
                    "Ensure the output strictly follows the DANA syntax rules provided in the user prompt.",
                    "Pay close attention to scoping rules and valid instruction formats.",
                ],
            }
        )
        response = await self.llm.query(request)
        if not response.success:
            raise TranscoderError(f"Failed to clean code with LLM: {response}", input_text, "LLM cleaning failed")
        if not response.content:
            raise TranscoderError("LLM response content is empty", input_text, "LLM cleaning failed")
        choices = response.content.get("choices", [])
        if not choices:
            raise TranscoderError("No choices in LLM response", input_text, "LLM cleaning failed")
        message = getattr(choices[0], "message", None)
        if not message:
            raise TranscoderError("No message in LLM response", input_text, "LLM cleaning failed")
        content = getattr(message, "content", None)
        if not content:
            raise TranscoderError("No content in LLM response", input_text, "LLM cleaning failed")
        return content

    def validate(self, program: ParseResult, context: RuntimeContext) -> ValidationResult:
        """Validate a DANA program.

        Args:
            program: ParseResult containing the program to validate
            context: Runtime context for validation

        Returns:
            ValidationResult indicating if the program is valid
        """
        return validate_program(program.program)
