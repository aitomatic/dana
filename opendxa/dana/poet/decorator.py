"""
POET (Perceive-Operate-Enforce-Train) decorator for Dana language.

This module provides the POET decorator as a native Dana language feature.
POET works entirely within Dana's execution model with no Python dependencies.
"""

from typing import Any

from dana.frameworks.poet.types import POETConfig


def poet(domain: str | None = None, **kwargs) -> Any:
    """
    POET decorator for Dana functions - pure Dana language feature.

    This function is registered in Dana's function registry and works
    as a native Dana decorator that enhances functions during execution.

    In Dana code:
        @poet(domain="healthcare")
        def diagnose(symptoms: list) -> dict:
            # function implementation

    Args:
        domain: Domain context for enhancement
        **kwargs: Additional POET configuration (retries, timeout, etc.)

    Returns:
        A function that wraps the original Dana function with POET phases
    """

    def dana_decorator(original_func: Any) -> Any:
        """
        The actual decorator that receives the Dana function.
        This works within Dana's function execution context.
        """

        def poet_enhanced_function(*args, **kwargs):
            """
            POET-enhanced function with P->O->E->T phases.
            This executes entirely within Dana runtime.
            """

            # Get function name for logging/tracking
            func_name = getattr(original_func, "__name__", "unknown")

            # PERCEIVE PHASE: Input validation and context preparation
            # In a real implementation, this would use Dana's native data structures
            context = {"function_name": func_name, "domain": domain, "args": args, "kwargs": kwargs, "phase": "perceive"}

            # Log perception phase (using Dana's native log function if available)
            if "log" in kwargs.get("_dana_context", {}):
                kwargs["_dana_context"]["log"](f"POET({func_name}): Perceive phase")

            # OPERATE PHASE: Execute original function with error handling
            operation_result = None
            retry_count = 0
            max_retries = kwargs.get("retries", 1)

            while retry_count < max_retries:
                try:
                    context["phase"] = "operate"
                    context["retry"] = retry_count

                    # Execute original Dana function
                    operation_result = original_func(*args, **kwargs)
                    break  # Success, exit retry loop

                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        # Re-raise after max retries
                        context["phase"] = "error"
                        context["error"] = str(e)
                        raise e

                    # Log retry attempt
                    if "log" in kwargs.get("_dana_context", {}):
                        kwargs["_dana_context"]["log"](f"POET({func_name}): Retry {retry_count}/{max_retries}")

            # ENFORCE PHASE: Output validation and result processing
            context["phase"] = "enforce"

            # In a real implementation, this would apply domain-specific validations
            # For now, pass through the result
            enforced_result = operation_result

            # TRAIN PHASE: Learning and improvement (if enabled)
            if kwargs.get("enable_training", True):
                context["phase"] = "train"
                # In a real implementation, this would update domain knowledge
                # For now, just log the training phase
                if "log" in kwargs.get("_dana_context", {}):
                    kwargs["_dana_context"]["log"](f"POET({func_name}): Train phase completed")

            return enforced_result

        # Preserve Dana function metadata
        poet_enhanced_function.__name__ = getattr(original_func, "__name__", "poet_enhanced")
        poet_enhanced_function.__doc__ = getattr(original_func, "__doc__", None)

        # Store POET metadata in a way that's accessible to Dana
        poet_enhanced_function._poet_config = {
            "domain": domain,
            "retries": kwargs.get("retries", 1),
            "timeout": kwargs.get("timeout", None),
            "enable_training": kwargs.get("enable_training", True),
        }

        return poet_enhanced_function

    return dana_decorator


class POETMetadata:
    """Metadata for POET-enhanced functions - used by Dana runtime."""

    def __init__(self, function_name: str, config: POETConfig):
        self.function_name = function_name
        self.config = config
        self.version = 1

    def __getitem__(self, key):
        """Dict-like access for compatibility."""
        if key == "domains":
            return [self.config.domain] if self.config.domain else []
        elif key == "retries":
            return self.config.retries
        elif key == "timeout":
            return self.config.timeout
        elif key == "version":
            return self.version
        elif key == "namespace":
            return "local"
        else:
            raise KeyError(key)
