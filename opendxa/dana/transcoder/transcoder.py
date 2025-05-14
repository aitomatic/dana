"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Simple transcoder for DANA programs.
"""

from dana.parser.dana_parser import DanaParser, ParseResult

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest


class Transcoder:
    """Handles translation between natural language and DANA code."""

    DANA_LANGUAGE_DESCRIPTION = [
        "DANA Syntax Reference:",
        "- Structure: Code is a sequence of instructions. Indentation defines blocks",
        "- Comments: Start with #",
        "- Assignments: scope.variable = value",
        '  Example: private.result = "done", public.data = 5',
        "- Conditionals: if condition: followed by indented block",
        "  Example:",
        "    if private.x > 10:",
        '        log.info("X is greater than 10")',
        "- Logging: log.level(message)",
        '  Example: log.info("This is an info message")',
        "- Printing: print(message)",
        '  Example: print("Hello world")',
        '- Types: Strings ("quoted"), Numbers (123, 4.5), Booleans (true, false)',
        "- Expressions: Use comparison operators (==, !=, <, >, <=, >=), boolean logic (and, or, not)",
        "- Arithmetic: Addition (+), Subtraction (-), Multiplication (*), Division (/)",
        "  Example: private.result = 5 + 10 * 2",
        "- Math Functions: Use system.math.function_name()",
        "  Example: private.sqrt_result = system.math.sqrt(16)",
    ]

    def __init__(self, llm_resource: LLMResource):
        """Initialize the transcoder with an LLM resource.

        Args:
            llm_resource: LLM resource for translation
        """
        self.llm = llm_resource
        self.parser = DanaParser()

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
        system_messages = [
            "You are an expert DANA programmer. Your task is to translate natural language into valid DANA code.",
            "Follow these rules strictly:",
            "1. Output ONLY valid DANA code that can be parsed and executed",
            "2. Use proper DANA syntax:",
            "   - Variables must be scoped (private., public., system.)",
            "   - Use proper operators and expressions",
            "   - Follow DANA block structure and indentation",
            "3. Add helpful comments (# comment) to clarify complex logic",
            "4. Preserve the original intent while making it valid DANA code",
            "5. DO NOT add any markdown code blocks or formatting - just output the DANA code directly",
            "",
        ] + self.DANA_LANGUAGE_DESCRIPTION

        prompt = f"""
        Input:
        {natural_language}

        Translate the input above into clean, valid DANA code.
        """

        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": prompt}],
                "system_messages": system_messages,
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
            result = self.parser.parse(dana_code)
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
        system_messages = [
            "You are a DANA code explanation expert. Your task is to translate DANA code",
            "into clear, natural language explanations.",
            "Focus on explaining the intent and purpose of the code.",
            "",
        ] + self.DANA_LANGUAGE_DESCRIPTION

        prompt = f"""
        Input:
        {dana_code}

        Translate the DANA code above into natural language.
        """

        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": prompt}],
                "system_messages": system_messages,
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
