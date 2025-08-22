"""
Prompt Enhancement Engine for Semantic Function Dispatch

This module provides intelligent prompt modification based on expected return type context.
It enables POET-enhanced functions to automatically optimize their prompts for specific outputs.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from collections.abc import Callable
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
        self._type_handlers = self._build_type_handlers()

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

        # Dispatch to appropriate handler
        handler = self._get_type_handler(expected_type)
        return handler(prompt, type_context)

    def _get_type_handler(self, expected_type: str) -> Callable[[str, TypeContext], str]:
        """Get the appropriate handler for the given type."""
        # Check for direct type matches
        if expected_type in self._type_handlers:
            return self._type_handlers[expected_type]

        # Check for structure types
        if expected_type in ["list", "dict", "tuple"]:
            return self._enhance_for_structure

        # Default to Dana struct handler
        return self._enhance_for_dana_struct

    def _build_type_handlers(self) -> dict[str, Callable[[str, TypeContext], str]]:
        """Build mapping of types to their enhancement handlers."""
        return {
            "bool": self._enhance_for_boolean,
            "int": self._enhance_for_integer,
            "float": self._enhance_for_float,
            "str": self._enhance_for_string,
        }

    def _apply_enhancement(self, prompt: str, enhancement: str, type_name: str) -> str:
        """Apply enhancement pattern to prompt with consistent formatting."""
        if not enhancement:
            self.debug(f"No enhancement pattern for {type_name}")
            return prompt

        enhanced = f"{prompt}\n\n{enhancement}"
        self.debug(f"Enhanced {type_name} prompt: {len(enhanced)} chars")
        return enhanced

    def _enhance_for_boolean(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt to return clear boolean response."""
        # Determine variant based on context
        variant = "conditional" if context.context_type == ContextType.CONDITIONAL else "explicit"
        enhancement = self._enhancement_patterns["bool"][variant]
        return self._apply_enhancement(prompt, enhancement, "boolean")

    def _enhance_for_integer(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt to return clean integer."""
        enhancement = self._enhancement_patterns["int"]["standard"]
        return self._apply_enhancement(prompt, enhancement, "integer")

    def _enhance_for_float(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt to return clean float."""
        enhancement = self._enhancement_patterns["float"]["standard"]
        return self._apply_enhancement(prompt, enhancement, "float")

    def _enhance_for_string(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt for string response (usually no change needed)."""
        # Only enhance for high-confidence assignment contexts
        if context.context_type == ContextType.ASSIGNMENT and context.confidence > 0.9:
            enhancement = self._enhancement_patterns["str"]["detailed"]
            return self._apply_enhancement(prompt, enhancement, "string")

        self.debug("String context - no enhancement needed")
        return prompt

    def _enhance_for_structure(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt for structured data types."""
        expected_type = context.expected_type.lower()
        enhancement = self._enhancement_patterns.get("structure", {}).get(expected_type, "")

        if enhancement:
            return self._apply_enhancement(prompt, enhancement, expected_type)

        return prompt

    def _enhance_for_dana_struct(self, prompt: str, context: TypeContext) -> str:
        """Enhance prompt to return structured data matching Dana struct schema."""
        expected_type = context.expected_type

        try:
            # Get struct information
            struct_info = self._get_struct_info(expected_type)
            if not struct_info:
                return prompt

            # Build enhancement from struct information
            enhancement = self._build_struct_enhancement(expected_type, struct_info)
            return self._apply_enhancement(prompt, enhancement, f"Dana struct {expected_type}")

        except Exception as e:
            self.debug(f"Error enhancing prompt for Dana struct {expected_type}: {e}")
            return prompt

    def _get_struct_info(self, expected_type: str) -> dict | None:
        """Get struct schema and type information."""
        try:
            # Import here to avoid circular imports
            from dana.registry import TYPE_REGISTRY

            if not TYPE_REGISTRY.exists(expected_type):
                self.debug(f"Unknown struct type: {expected_type}")
                return None

            struct_schema = TYPE_REGISTRY.get_schema(expected_type)
            struct_type = TYPE_REGISTRY.get(expected_type)

            if not struct_schema or not struct_type:
                self.debug(f"Could not get schema for struct type: {expected_type}")
                return None

            return {
                "schema": struct_schema,
                "type": struct_type,
            }

        except Exception as e:
            self.debug(f"Error getting struct info for {expected_type}: {e}")
            return None

    def _build_struct_enhancement(self, struct_name: str, struct_info: dict) -> str:
        """Build enhancement text for Dana struct."""
        struct_type = struct_info["type"]
        struct_schema = struct_info["schema"]

        # Build field descriptions
        field_descriptions = self._build_field_descriptions(struct_type)

        # Log field descriptions for debugging
        self.debug(f"Field descriptions for {struct_name}:")
        for desc in field_descriptions:
            self.debug(f"  {desc}")

        fields_text = "\n".join(field_descriptions)

        # Include docstring if available
        docstring_text = ""
        if struct_type.docstring:
            docstring_text = f"\nDescription: {struct_type.docstring}\n"

        return f"""
{struct_name} struct{docstring_text} fields:
{fields_text}

JSON Schema:
{struct_schema}

Return format: A valid JSON object with all required fields properly typed.
Do not include markdown formatting, code fences, or explanations.
Return raw JSON only that can be parsed into a {struct_name} instance.

After your response, provide your final answer in this exact format:
FINAL_ANSWER: {{"field1": "value1", "field2": "value2"}}

The final answer should be a valid JSON object with all required fields properly typed that can be parsed into a {struct_name} instance."""

    def _build_field_descriptions(self, struct_type) -> list[str]:
        """Build list of field descriptions for a struct type."""
        field_descriptions = []
        for field_name in struct_type.field_order:
            field_description = struct_type.get_field_description(field_name)
            field_descriptions.append(f"- {field_description}")
        return field_descriptions

    def _build_enhancement_patterns(self) -> dict[str, dict[str, str]]:
        """Build library of enhancement patterns for different types."""
        return {
            "bool": {
                "explicit": """IMPORTANT: Respond with a clear yes/no decision.
Return format: "yes" or "no" (or "true"/"false")
Do not include explanations unless specifically requested.

After your response, provide your final answer in this exact format:
FINAL_ANSWER: yes
or
FINAL_ANSWER: no

You can use "true"/"false" instead of "yes"/"no" if more appropriate.""",
                "conditional": """IMPORTANT: Evaluate this condition and respond clearly.
Return format: "yes" or "no" based on whether the condition is met.
Focus on the specific criteria being evaluated.""",
            },
            "int": {
                "standard": """IMPORTANT: Return ONLY the final integer number.
Do not include explanations, formatting, or additional text.
Expected format: A single whole number (e.g., 42)
If calculation is needed, show only the final result.

After your response, provide your final answer in this exact format:
FINAL_ANSWER: 42

The final answer should be a single whole number."""
            },
            "float": {
                "standard": """IMPORTANT: Return ONLY the final numerical value as a decimal number.
Do not include explanations, formatting, or additional text.
Expected format: A single floating-point number (e.g., 81.796)
If calculation is needed, show only the final result.

After your response, provide your final answer in this exact format:
FINAL_ANSWER: 81.796

The final answer should be a single decimal number."""
            },
            "str": {
                "detailed": """Please provide a comprehensive and well-structured response.
Include relevant details and context to make the response useful and informative.

If you need to provide a specific final answer, use this format:
FINAL_ANSWER: [your answer here]"""
            },
            "structure": {
                "list": """IMPORTANT: Return ONLY a valid JSON array.
Expected format: ["item1", "item2", "item3"]
Do not include markdown formatting, code fences, or explanations.
Return raw JSON only.

After your response, provide your final answer in this exact format:
FINAL_ANSWER: ["item1", "item2", "item3"]

The final answer should be a valid JSON array.""",
                "dict": """IMPORTANT: Return ONLY a valid JSON object.
Expected format: {"key1": "value1", "key2": "value2"}
Do not include markdown formatting, code fences, or explanations.
Return raw JSON only.

After your response, provide your final answer in this exact format:
FINAL_ANSWER: {"key1": "value1", "key2": "value2"}

The final answer should be a valid JSON object.""",
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
