"""Simple transcoder for DANA programs."""

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest
from opendxa.dana.language.parser import ParseResult, parse


class TranscoderError(Exception):
    """Exception raised when transcoding fails."""

    def __init__(self, message: str, natural_language: str):
        self.natural_language = natural_language
        # Clean up the error message
        if "Generated invalid DANA code:" in message:
            # Extract the actual error message
            error_msg = message.split("Generated invalid DANA code:")[1].strip()
            # Remove the ParseError wrapper
            if error_msg.startswith("[ParseError(") and error_msg.endswith(")]"):
                error_msg = error_msg[12:-2]  # Remove ParseError( and )
                # Remove quotes if present
                if error_msg.startswith('"') and error_msg.endswith('"'):
                    error_msg = error_msg[1:-1]
            message = error_msg
        super().__init__(message)


class Transcoder:
    """Handles translation between natural language and DANA code."""

    def __init__(self, llm_resource: LLMResource):
        """Initialize the transcoder with an LLM resource.

        Args:
            llm_resource: LLM resource for translation
        """
        self.llm = llm_resource

    async def to_dana(self, natural_language: str) -> tuple[ParseResult, str]:
        """Convert natural language to DANA code.

        Args:
            natural_language: Natural language input to convert

        Returns:
            A tuple containing:
            - The parse result with program and errors
            - The generated DANA code

        Raises:
            TranscoderError: If translation fails
        """
        prompt = f"""
        You are an expert DANA programmer. Your task is to translate the following natural language
        into valid DANA code.

        Input:
        {natural_language}

        Follow these rules strictly:
        1. Output ONLY valid DANA code that can be parsed and executed
        2. Use proper DANA syntax:
           - Variables must be scoped (private., public., system.)
           - Use proper operators and expressions
           - Follow DANA block structure and indentation
        3. Add helpful comments (# comment) to clarify complex logic
        4. Preserve the original intent while making it valid DANA code
        5. DO NOT add any markdown code blocks or formatting - just output the DANA code directly

        DANA Syntax Reference:
        - Structure: Code is a sequence of instructions. Indentation defines blocks
        - Comments: Start with #
        - Assignments: scope.variable = value
          Example: private.result = "done", public.data = 5
        - Conditionals: if condition: followed by indented block
          Example:
            if private.x > 10:
                log.info("X is greater than 10")
        - Logging: log.level(message)
          Example: log.info("This is an info message")
        - Printing: print(message)
          Example: print("Hello world")
        - Types: Strings ("quoted"), Numbers (123, 4.5), Booleans (true, false)
        - Expressions: Use comparison operators (==, !=, <, >, <=, >=), boolean logic (and, or, not)
        - Arithmetic: Addition (+), Subtraction (-), Multiplication (*), Division (/)
          Example: private.result = 5 + 10 * 2
        - Math Functions: Use system.math.function_name()
          Example: private.sqrt_result = system.math.sqrt(16)

        Translate the input above into clean, valid DANA code.
        """
        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": prompt}],
                "system_messages": [
                    "You are a DANA code generation expert. Your sole task is to translate natural language",
                    "into valid DANA syntax according to the provided rules and syntax reference.",
                    "Output *only* valid DANA code. Do not add any conversational text, explanations, or markdown formatting.",
                ],
            }
        )

        try:
            response = await self.llm.query(request)
            if not response.success:
                raise TranscoderError(f"Failed to translate to DANA: {response}", natural_language)

            # Extract the content from the response
            if hasattr(response, "content") and isinstance(response.content, dict):
                content_dict = response.content
                if "choices" in content_dict and content_dict["choices"]:
                    first_choice = content_dict["choices"][0]
                    if isinstance(first_choice, dict) and "message" in first_choice:
                        dana_code = first_choice["message"]["content"]
                    else:
                        dana_code = first_choice.message.content
                else:
                    dana_code = str(response.content)
            else:
                dana_code = str(response.content)

            # Parse the generated code to validate it
            result = parse(dana_code)
            if not result.is_valid:
                raise TranscoderError(f"Generated invalid DANA code: {result.errors}", natural_language)

            return result, dana_code

        except Exception as e:
            raise TranscoderError(f"Error during translation: {e}", natural_language)

    async def to_natural_language(self, dana_code: str) -> str:
        """Convert DANA code to natural language.

        Args:
            dana_code: DANA code to convert

        Returns:
            Natural language description of the DANA code

        Raises:
            TranscoderError: If translation fails
        """
        prompt = f"""
        You are an expert DANA programmer. Your task is to translate the following DANA code
        into natural language.

        Input:
        {dana_code}

        Follow these rules:
        1. Explain what the code does in clear, natural language
        2. Focus on the intent and purpose of the code
        3. Explain any complex logic or important decisions
        4. Keep the explanation concise but complete
        5. Use plain, non-technical language where possible

        Translate the DANA code above into natural language.
        """
        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": prompt}],
                "system_messages": [
                    "You are a DANA code explanation expert. Your task is to translate DANA code",
                    "into clear, natural language explanations.",
                    "Focus on explaining the intent and purpose of the code.",
                ],
            }
        )

        try:
            response = await self.llm.query(request)
            if not response.success:
                raise TranscoderError(f"Failed to translate to natural language: {response}", dana_code)

            # Extract the content from the response
            if hasattr(response, "content") and isinstance(response.content, dict):
                content_dict = response.content
                if "choices" in content_dict and content_dict["choices"]:
                    first_choice = content_dict["choices"][0]
                    if isinstance(first_choice, dict) and "message" in first_choice:
                        return first_choice["message"]["content"]
                    else:
                        return first_choice.message.content
                else:
                    return str(response.content)
            else:
                return str(response.content)

        except Exception as e:
            raise TranscoderError(f"Error during translation: {e}", dana_code)
