"""
Enhanced reason function for Dana standard library.

This module provides the context_aware_reason function for enhanced LLM reasoning.
"""

__all__ = ["py_context_aware_reason"]

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.interpreter.context_detection import ContextDetector
from dana.core.lang.interpreter.enhanced_coercion import SemanticCoercer
from dana.core.lang.interpreter.prompt_enhancement import enhance_prompt_for_type
from dana.core.lang.sandbox_context import SandboxContext


class POETEnhancedReasonFunction(Loggable):
    """POET-enhanced reason function with context-aware prompt optimization."""

    def __init__(self):
        super().__init__()
        self.context_detector = ContextDetector()
        self.semantic_coercer = SemanticCoercer()
        self._original_reason_func = None

    def set_original_function(self, original_func):
        """Set the original reason function to wrap."""
        self._original_reason_func = original_func

    def __call__(
        self,
        prompt: str,
        context: SandboxContext,
        options: dict[str, Any] | None = None,
        use_mock: bool | None = None,
    ) -> Any:
        """
        POET-enhanced reason function with automatic prompt optimization.

        Args:
            prompt: Original user prompt
            context: Sandbox execution context
            options: Optional parameters for the LLM
            use_mock: Whether to use mock responses

        Returns:
            Result optimized and coerced for the expected return type
        """
        self.debug(f"POET-enhanced reason called with prompt: '{prompt[:50]}...'")

        try:
            # Phase 1: Detect expected return type context
            type_context = self.context_detector.detect_current_context(context)

            if type_context:
                self.debug(f"Detected type context: {type_context}")

                # Phase 2: Enhance prompt based on expected type
                enhanced_prompt = enhance_prompt_for_type(prompt, type_context)

                if enhanced_prompt != prompt:
                    self.debug(f"Enhanced prompt from {len(prompt)} to {len(enhanced_prompt)} chars")
                    self.debug(f"Enhancement for type: {type_context.expected_type}")
                else:
                    self.debug("No prompt enhancement applied")
            else:
                self.debug("No type context detected, using original prompt")
                enhanced_prompt = prompt

            # Phase 3: Execute with enhanced prompt
            if self._original_reason_func:
                result = self._original_reason_func(context, enhanced_prompt, options, use_mock)
            else:
                # Fallback: import and use the original function
                result = self._execute_fallback_reason(context, enhanced_prompt, options, use_mock)

            # Phase 4: Apply semantic coercion if type context is available
            if type_context and type_context.expected_type and result is not None:
                try:
                    coerced_result = self.semantic_coercer.coerce_value(
                        result, type_context.expected_type, context=f"reason_function_{type_context.expected_type}"
                    )

                    if coerced_result != result:
                        self.debug(f"Applied semantic coercion: {type(result)} → {type(coerced_result)}")

                    return coerced_result

                except Exception as coercion_error:
                    self.debug(f"Semantic coercion failed: {coercion_error}, returning original result")
                    # Fall back to original result if coercion fails
                    return result

            return result

        except Exception as e:
            self.debug(f"POET enhancement failed: {e}, falling back to original function")
            # Fallback to original function on any error
            if self._original_reason_func:
                return self._original_reason_func(context, prompt, options, use_mock)
            else:
                return self._execute_fallback_reason(context, prompt, options, use_mock)

    def _execute_fallback_reason(self, context: SandboxContext, prompt: str, options: dict[str, Any] | None, use_mock: bool | None) -> Any:
        """Execute fallback reason function when original is not available."""
        try:
            # Import the original reason function
            from .py_reason import py_reason

            self.debug("Using fallback reason function")
            return py_reason(context, prompt, options, use_mock)

        except ImportError as e:
            self.debug(f"Could not import original reason function: {e}")
            raise RuntimeError("POET-enhanced reason function cannot access original reason implementation")


# Global instance for function registration
_poet_enhanced_reason = POETEnhancedReasonFunction()


def py_context_aware_reason(
    context: SandboxContext,
    prompt: str,
    options: dict[str, Any] | None = None,
    use_mock: bool | None = None,
) -> Any:
    """Execute the context-aware reason function with enhanced prompt optimization.

    This function provides context-aware reasoning with automatic prompt enhancement
    based on the current execution context.

    Args:
        context: The sandbox context
        prompt: The prompt string to send to the LLM
        options: Optional parameters for the LLM call
        use_mock: Force use of mock responses

    Returns:
        The LLM's response optimized for the current context

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    return _poet_enhanced_reason(prompt, context, options, use_mock)


def register_original_reason_function(original_func):
    """
    Register the original reason function for wrapping.

    Args:
        original_func: The original reason function to enhance
    """
    _poet_enhanced_reason.set_original_function(original_func)


def get_enhancement_stats() -> dict[str, Any]:
    """
    Get statistics about POET enhancements.

    Returns:
        Dictionary with enhancement statistics
    """
    return {
        "context_detector_cache_size": _poet_enhanced_reason.context_detector.get_cache_size(),
        "semantic_coercer_strategy": _poet_enhanced_reason.semantic_coercer.strategy.value,
        "has_original_function": _poet_enhanced_reason._original_reason_func is not None,
    }
