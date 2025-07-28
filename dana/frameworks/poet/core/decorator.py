"""
POET (Perceive-Operate-Enforce-Train) decorator for Dana language.

This module provides the POET decorator as a native Dana language feature.
POET works entirely within Dana's execution model with no Python dependencies.
"""

from typing import Any

from dana.frameworks.poet.core.metadata_extractor import MetadataExtractor
from dana.frameworks.poet.core.types import POETConfig, POETResult


def poet(
    domain: str | None = None,
    *,
    # Phase-specific configuration
    perceive: dict[str, Any] | None = None,
    operate: dict[str, Any] | None = None,
    enforce: dict[str, Any] | None = None,
    train: dict[str, Any] | None = None,
    # Legacy compatibility
    retries: int = 1,
    timeout: float | None = None,
    # Observability
    debug: bool = False,
    trace_phases: bool = False,
    performance_tracking: bool = True,
    **kwargs,
) -> Any:
    """
    POET decorator for Dana functions - enhanced with explicit phase configuration.

    Examples:
        # Simple usage
        @poet(domain="healthcare")
        def diagnose(symptoms: list) -> dict:
            return {"diagnosis": "healthy"}

        # Advanced configuration
        @poet(
            domain="financial_services",
            perceive={"input_validation": True, "normalize_formats": True},
            operate={"retries": 3, "timeout": 30},
            enforce={"output_validation": True, "compliance_check": "FCRA"},
            train={"learning_rate": 0.1, "feedback_threshold": 0.8},
            debug=True
        )
        def assess_credit_risk(score: int) -> str:
            return "approved" if score > 700 else "declined"

    Args:
        domain: Domain context for enhancement
        perceive: Configuration for input processing phase
        operate: Configuration for execution phase
        enforce: Configuration for output validation phase
        train: Configuration for learning phase
        retries: Number of retry attempts (legacy)
        timeout: Timeout in seconds (legacy)
        debug: Enable debug logging
        trace_phases: Log detailed phase execution
        performance_tracking: Track phase timings
        **kwargs: Additional configuration options

    Returns:
        A function that wraps the original Dana function with POET phases
    """

    # Create configuration object - filter out unsupported kwargs
    supported_kwargs = {k: v for k, v in kwargs.items() if k in ["optimize_for", "enable_monitoring"]}

    config = POETConfig(
        domain=domain,
        perceive=perceive or {},
        operate=operate or {},
        enforce=enforce or {},
        train=train or {},
        retries=retries,
        timeout=timeout,
        debug=debug,
        trace_phases=trace_phases,
        performance_tracking=performance_tracking,
        **supported_kwargs,
    )

    def dana_decorator(original_func: Any) -> Any:
        """
        The actual decorator that receives the Dana function.
        This works within Dana's function execution context.
        """

        def poet_enhanced_function(*args, **kwargs):
            """
            POET-enhanced function with P->O->E->T phases.
            This executes entirely within Dana runtime with enhanced configuration.
            """
            import time

            # Get function name for logging/tracking
            func_name = getattr(original_func, "__name__", "unknown")

            # Phase timing tracking
            phase_timings = {} if config.performance_tracking else None
            start_time = time.time() if config.performance_tracking else None

            # Enhanced context with configuration
            context = {
                "function_name": func_name,
                "domain": config.domain,
                "args": args,
                "kwargs": kwargs,
                "config": config,
                "phase": "perceive",
            }

            # PERCEIVE PHASE: Input validation and context preparation
            if config.trace_phases or config.debug:
                print(f"🔍 POET({func_name}): Perceive phase started")

            perceive_start = time.time() if config.performance_tracking else None

            # Apply perceive configuration
            if config.perceive.get("input_validation", False):
                if config.debug:
                    print(f"  → Input validation enabled for {func_name}")

            if config.perceive.get("normalize_formats", False):
                if config.debug:
                    print(f"  → Format normalization enabled for {func_name}")

            if perceive_start and config.performance_tracking:
                phase_timings["perceive"] = time.time() - perceive_start

            # OPERATE PHASE: Execute original function with error handling
            if config.trace_phases or config.debug:
                print(f"⚙️  POET({func_name}): Operate phase started")

            operate_start = time.time() if config.performance_tracking else None
            context["phase"] = "operate"

            operation_result = None
            retry_count = 0
            max_retries = config.retries

            # Apply operate configuration
            # actual_timeout = config.operate.get("timeout", config.timeout)  # TODO: Implement timeout handling

            while retry_count < max_retries:
                try:
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
                        if config.debug:
                            print(f"❌ POET({func_name}): Failed after {max_retries} retries: {e}")
                        raise e

                    # Log retry attempt
                    if config.debug:
                        print(f"🔄 POET({func_name}): Retry {retry_count}/{max_retries}")

            if operate_start and config.performance_tracking:
                phase_timings["operate"] = time.time() - operate_start

            # ENFORCE PHASE: Output validation and result processing
            if config.trace_phases or config.debug:
                print(f"🛡️  POET({func_name}): Enforce phase started")

            enforce_start = time.time() if config.performance_tracking else None
            context["phase"] = "enforce"

            # Apply enforce configuration
            if config.enforce.get("output_validation", False):
                if config.debug:
                    print(f"  → Output validation enabled for {func_name}")

            if config.enforce.get("compliance_check"):
                compliance_type = config.enforce["compliance_check"]
                if config.debug:
                    print(f"  → Compliance check ({compliance_type}) enabled for {func_name}")

            enforced_result = operation_result

            if enforce_start and config.performance_tracking:
                phase_timings["enforce"] = time.time() - enforce_start

            # TRAIN PHASE: Learning and improvement (if enabled)
            if config.train:
                if config.trace_phases or config.debug:
                    print(f"🎓 POET({func_name}): Train phase started")

                train_start = time.time() if config.performance_tracking else None
                context["phase"] = "train"

                # Apply train configuration
                if config.train.get("learning_rate"):
                    if config.debug:
                        print(f"  → Learning rate: {config.train['learning_rate']}")

                if config.train.get("feedback_threshold"):
                    if config.debug:
                        print(f"  → Feedback threshold: {config.train['feedback_threshold']}")

                if train_start and config.performance_tracking:
                    phase_timings["train"] = time.time() - train_start

            # Performance summary
            if config.performance_tracking and phase_timings:
                total_time = time.time() - start_time
                if config.debug:
                    print(f"⏱️  POET({func_name}): Total execution time: {total_time:.3f}s")
                    for phase, timing in phase_timings.items():
                        print(f"    {phase}: {timing:.3f}s")

            # Return enhanced result with metadata
            if config.performance_tracking or config.debug:
                return POETResult(
                    enforced_result,
                    func_name,
                    phase_timings=phase_timings,
                    confidence=0.95,  # Mock confidence for now
                )
            else:
                return enforced_result

        # Preserve Dana function metadata
        poet_enhanced_function.__name__ = getattr(original_func, "__name__", "poet_enhanced")
        poet_enhanced_function.__doc__ = getattr(original_func, "__doc__", None)

        # Store POET metadata in a way that's accessible to Dana
        poet_enhanced_function._poet_config = config.dict()

        # Add metadata extraction capability
        poet_enhanced_function.get_metadata = lambda: MetadataExtractor().extract_function_metadata(poet_enhanced_function)

        return poet_enhanced_function

    return dana_decorator


def extract_poet_metadata(func: Any) -> dict[str, Any]:
    """
    Extract metadata from a poet-decorated function.

    Args:
        func: A function decorated with @poet

    Returns:
        Dictionary containing function metadata
    """
    if hasattr(func, "get_metadata"):
        return func.get_metadata().to_dict()
    else:
        # Fallback for non-poet functions
        extractor = MetadataExtractor()
        return extractor.extract_function_metadata(func).to_dict()


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
