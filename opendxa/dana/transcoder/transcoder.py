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

    async def transcode(self, input_text: str, context: RuntimeContext) -> ParseResult:
        """Convert mixed natural language and DANA code into valid DANA.

        Args:
            input_text: Mixed natural language and DANA code
            context: Runtime context for validation

        Returns:
            ParseResult containing the valid DANA program

        Raises:
            TranscoderError: If transcoding fails after all attempts
        """
        # 1. Try direct parsing first
        try:
            result = parse(input_text)
            if result.is_valid:
                return result
        except ParseError:
            pass

        # 2. Try cleaning with LLM
        cleaned_code = await self._clean_with_llm(input_text)
        try:
            result = parse(cleaned_code)
            if result.is_valid:
                return result
        except ParseError as e:
            raise TranscoderError(
                f"Failed to transcode input after cleaning: {str(e)}",
                input_text,
                cleaned_code,
            ) from e

        # If we get here, something went wrong
        raise TranscoderError(
            "Failed to transcode input after all attempts",
            input_text,
            cleaned_code,
        )

    async def _clean_with_llm(self, input_text: str) -> str:
        """Use LLM to clean and format the input.

        Args:
            input_text: Mixed natural language and DANA code

        Returns:
            Cleaned and formatted DANA code
        """
        prompt = f"""
        Clean and format this mixed natural language and DANA code into valid DANA:
        {input_text}
        
        Rules:
        1. Preserve the original intent
        2. Fix syntax errors
        3. Add helpful comments
        4. Ensure proper scoping (use private. for variables)
        5. Add appropriate logging
        6. Follow DANA syntax:
           - Assignments: scope.variable = value
           - Logging: log("message")
           - Comments: # comment
           - Strings must be quoted
        """
        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": prompt}],
                "system_messages": [
                    "You are a DANA code expert. Your task is to clean and format DANA code while preserving the original intent.",
                    "Always ensure the output is valid DANA syntax.",
                    "Add helpful comments to explain the code.",
                    "Use proper scoping and add appropriate logging statements.",
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
