"""
Prompt Enhancement Engine for Semantic Function Dispatch

This module provides intelligent prompt modification based on expected return type context.
It enables POET-enhanced functions to automatically optimize their prompts for specific outputs.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from enum import Enum

from dana.common.mixins.loggable import Loggable
from dana.core.lang.interpreter.context_detection import ContextType, TypeContext


class PromptStyle(Enum):
    """Different prompt enhancement styles."""

    CONCISE = "concise"  # Brief, direct responses
    STRUCTURED = "structured"  # Formatted, organized responses
    DETAILED = "detailed"  # Comprehensive explanations
    MINIMAL = "minimal"  # Absolute minimum response


class PromptEnhancer(Loggable):
    """Enhances prompts based on expected return type context."""

    def __init__(self, default_style: PromptStyle = PromptStyle.CONCISE):
        super().__init__()
        self.default_style = default_style
        self._enhancement_patterns = self._build_enhancement_patterns()

    def enhance_prompt(self, prompt: str, type_context: TypeContext | None = None) -> str:
        """
        Transform prompt to optimize for specific return type.

        Args:
            prompt: Original prompt text
            type_context: Context information about expected return type

        Returns:
            Enhanced prompt optimized for the expected return type
        """
        if not type_context or not type_context.expected_type:
            self.debug("No type context available, returning original prompt")
            return prompt

        expected_type = type_context.expected_type.lower()
        self.debug(f"Enhancing prompt for type: {expected_type}")

        # Apply type-specific enhancement
        if expected_type == "bool":
            return self._enhance_for_boolean(prompt, type_context)
        elif expected_type == "int":
            return self._enhance_for_integer(prompt, type_context)
        elif expected_type == "float":
            return self._enhance_for_float(prompt, type_context)
        elif expected_type == "str":
            return self._enhance_for_string(prompt, type_context)
        elif expected_type in ["list", "dict", "tuple"]:
            return self._enhance_for_structure(prompt, type_context)
        else:
            # Check if this is a Dana struct type
            return self._enhance_for_dana_struct(prompt, type_context)

    def _enhance_for_boolean(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt to return clear boolean response."""

        # Determine if this is an implicit boolean context (like conditionals)
        if context.context_type == ContextType.CONDITIONAL:
            enhancement = self._enhancement_patterns["bool"]["conditional"]
        else:
            enhancement = self._enhancement_patterns["bool"]["explicit"]

        enhanced = f"""{prompt}

{enhancement}"""

        self.debug(f"Enhanced boolean prompt: {len(enhanced)} chars")
        return enhanced

    def _enhance_for_integer(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt to return clean integer."""

        enhancement = self._enhancement_patterns["int"]["standard"]

        enhanced = f"""{prompt}

{enhancement}"""

        self.debug(f"Enhanced integer prompt: {len(enhanced)} chars")
        return enhanced

    def _enhance_for_float(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt to return clean float."""

        enhancement = self._enhancement_patterns["float"]["standard"]

        enhanced = f"""{prompt}

{enhancement}"""

        self.debug(f"Enhanced float prompt: {len(enhanced)} chars")
        return enhanced

    def _enhance_for_string(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt for string response (usually no change needed)."""

        # For explicit string contexts, we might want to encourage detailed responses
        if context.context_type == ContextType.ASSIGNMENT and context.confidence > 0.9:
            enhancement = self._enhancement_patterns["str"]["detailed"]
            enhanced = f"""{prompt}

{enhancement}"""
            self.debug("Enhanced string prompt for detailed response")
            return enhanced

        # Otherwise, return original prompt
        self.debug("String context - no enhancement needed")
        return prompt

    def _enhance_for_structure(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt for structured data types."""

        expected_type = context.expected_type.lower()
        enhancement = self._enhancement_patterns.get("structure", {}).get(expected_type, "")

        if enhancement:
            enhanced = f"""{prompt}

{enhancement}"""
            self.debug(f"Enhanced {expected_type} prompt: {len(enhanced)} chars")
            return enhanced

        return prompt

    def _enhance_for_dana_struct(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt to return structured data matching Dana struct schema.

        Args:
            prompt: Original prompt text
            context: Type context with expected struct type

        Returns:
            Enhanced prompt with struct schema information
        """
        expected_type = context.expected_type

        try:
            # Import here to avoid circular imports
            from dana.core.lang.interpreter.struct_system import StructTypeRegistry

            # Check if this is a registered Dana struct type
            if not StructTypeRegistry.exists(expected_type):
                self.debug(f"Unknown struct type: {expected_type}")
                return prompt

            # Get the struct schema
            struct_schema = StructTypeRegistry.get_schema(expected_type)
            struct_type = StructTypeRegistry.get(expected_type)

            if not struct_schema or not struct_type:
                self.debug(f"Could not get schema for struct type: {expected_type}")
                return prompt

            # Build field description
            field_descriptions = []
            for field_name in struct_type.field_order:
                field_description = struct_type.get_field_description(field_name)
                field_descriptions.append(f"- {field_description}")

            fields_text = "\n".join(field_descriptions)

            # Debug output to verify field descriptions
            self.debug(f"Field descriptions for {expected_type}:")
            for desc in field_descriptions:
                self.debug(f"  {desc}")

            # Create enhancement with struct information
            enhancement = f"""
IMPORTANT: You must respond with a valid JSON object that matches the {expected_type} struct schema.

{expected_type} struct fields:
{fields_text}

JSON Schema:
{struct_schema}

Return format: A valid JSON object with all required fields properly typed.
Do not include markdown formatting, code fences, or explanations.
Return raw JSON only that can be parsed into a {expected_type} instance.
"""

            enhanced = f"""{prompt}

{enhancement}"""

            self.debug(f"Enhanced Dana struct prompt for {expected_type}: {len(enhanced)} chars")
            return enhanced

        except Exception as e:
            self.debug(f"Error enhancing prompt for Dana struct {expected_type}: {e}")
            return prompt

    def _build_enhancement_patterns(self) -> dict[str, dict[str, str]]:
        """Build library of enhancement patterns for different types."""

        return {
            "bool": {
                "explicit": """IMPORTANT: Respond with a clear yes/no decision.
Return format: "yes" or "no" (or "true"/"false")
Do not include explanations unless specifically requested.""",
                "conditional": """IMPORTANT: Evaluate this condition and respond clearly.
Return format: "yes" or "no" based on whether the condition is met.
Focus on the specific criteria being evaluated.""",
            },
            "int": {
                "standard": """IMPORTANT: Return ONLY the final integer number.
Do not include explanations, formatting, or additional text.
Expected format: A single whole number (e.g., 42)
If calculation is needed, show only the final result."""
            },
            "float": {
                "standard": """IMPORTANT: Return ONLY the final numerical value as a decimal number.
Do not include explanations, formatting, or additional text.
Expected format: A single floating-point number (e.g., 81.796)
If calculation is needed, show only the final result."""
            },
            "str": {
                "detailed": """Please provide a comprehensive and well-structured response.
Include relevant details and context to make the response useful and informative."""
            },
            "structure": {
                "list": """IMPORTANT: Return ONLY a valid JSON array.
Expected format: ["item1", "item2", "item3"]
Do not include markdown formatting, code fences, or explanations.
Return raw JSON only.""",
                "dict": """IMPORTANT: Return ONLY a valid JSON object.
Expected format: {"key1": "value1", "key2": "value2"}
Do not include markdown formatting, code fences, or explanations.
Return raw JSON only.""",
            },
        }

    def get_enhancement_preview(self, prompt: str, expected_type: str) -> str:
        """
        Get a preview of how a prompt would be enhanced.

        Args:
            prompt: Original prompt
            expected_type: Expected return type

        Returns:
            Preview of enhanced prompt
        """
        from dana.core.lang.interpreter.context_detection import ContextType, TypeContext

        # Create mock context for preview
        mock_context = TypeContext(
            expected_type=expected_type, context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={"preview": True}
        )

        return self.enhance_prompt(prompt, mock_context)


# Global instance for convenience
_global_enhancer = PromptEnhancer()


def enhance_prompt_for_type(prompt: str, type_context: TypeContext | None = None) -> str:
    """
    Convenience function for prompt enhancement.

    Args:
        prompt: Original prompt text
        type_context: Context information about expected return type

    Returns:
        Enhanced prompt optimized for the expected return type
    """
    return _global_enhancer.enhance_prompt(prompt, type_context)


def preview_enhancement(prompt: str, expected_type: str) -> str:
    """
    Convenience function to preview prompt enhancement.

    Args:
        prompt: Original prompt
        expected_type: Expected return type

    Returns:
        Preview of how the prompt would be enhanced
    """
    return _global_enhancer.get_enhancement_preview(prompt, expected_type)
