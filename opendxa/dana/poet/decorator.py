"""
POET (Perceive-Operate-Enforce-Train) decorator implementation.

This module provides the POET decorator for enhancing functions with domain-specific capabilities.
Functions are enhanced by generating Dana code that implements the P→O→E→T phases and storing
it locally in .dana/poet/ directories.
"""

import inspect
import os
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from opendxa.dana.poet.types import POETResult
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class POETConfig:
    """Configuration object for POET decorator"""

    def __init__(
        self,
        domain: str = "computation",
        retries: int = 1,
        timeout: int | None = None,
        optimize_for: str | None = None,
        enable_monitoring: bool = True,
        cache_strategy: str = "auto",
        fallback_strategy: str = "raise",
        **kwargs,
    ):
        self.domain = domain
        self.retries = retries
        self.timeout = timeout
        self.optimize_for = optimize_for
        self.enable_monitoring = enable_monitoring
        self.cache_strategy = cache_strategy
        self.fallback_strategy = fallback_strategy
        for key, value in kwargs.items():
            setattr(self, key, value)


class POETMetadata:
    """Metadata container for POET enhanced functions"""

    def __init__(self, func: Callable, config: POETConfig):
        self.function_name = func.__name__
        self.version = 1
        self.config = config
        # Mock enhanced_path for compatibility
        from pathlib import Path

        self.enhanced_path = Path("tmp") / "enhanced.na"


class POETDecorator:
    """
    Enhanced POET decorator that generates and executes Dana-based enhancements.
    
    The decorator works by:
    1. Checking for enhanced Dana code in .dana/poet/{function_name}.na
    2. Generating the enhanced code if it doesn't exist
    3. Executing the enhanced code in the Dana sandbox
    """

    def __init__(
        self,
        func: Callable,
        domain: str = "computation",
        retries: int = 1,
        timeout: int | None = None,
        optimize_for: str | None = None,
        enable_monitoring: bool = True,
        cache_strategy: str = "auto",
        fallback_strategy: str = "raise",
        **kwargs,
    ):
        """Initialize the enhanced POET decorator."""
        self.func = func
        self.config = POETConfig(
            domain=domain,
            retries=retries,
            timeout=timeout,
            optimize_for=optimize_for,
            enable_monitoring=enable_monitoring,
            cache_strategy=cache_strategy,
            fallback_strategy=fallback_strategy,
            **kwargs,
        )
        
        # Store function metadata
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__module__ = getattr(func, "__module__", None)
        self.__qualname__ = getattr(func, "__qualname__", func.__name__)
        
        # Determine enhanced file path
        self.enhanced_path = self._get_enhanced_path()
        
        # Create wrapper
        self._create_wrapper()

    def _get_enhanced_path(self) -> Path:
        """Get the path where the enhanced Dana code should be stored."""
        try:
            # Get the directory where the original function is defined
            func_file = inspect.getfile(self.func)
            func_dir = Path(func_file).parent
        except (TypeError, OSError):
            # Function might be defined in REPL or dynamically
            func_dir = Path.cwd()
        
        # Enhanced code goes in .dana/poet/{function_name}.na
        return func_dir / ".dana" / "poet" / f"{self.func.__name__}.na"

    def _ensure_enhanced_code_exists(self) -> None:
        """Ensure enhanced Dana code exists, generating if necessary."""
        if not self.enhanced_path.exists():
            # Import transpiler and generate code
            from opendxa.dana.poet.transpiler import POETTranspiler
            
            transpiler = POETTranspiler()
            dana_code = transpiler.transpile(self.func, self.config)
            
            # Create directory and write code
            self.enhanced_path.parent.mkdir(parents=True, exist_ok=True)
            self.enhanced_path.write_text(dana_code)

    def _create_wrapper(self) -> None:
        """Create the wrapper function that executes enhanced Dana code."""
        @wraps(self.func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute the POET-enhanced function."""
            # Ensure enhanced code exists
            self._ensure_enhanced_code_exists()
            
            # Get or create sandbox context
            context = kwargs.pop("context", None)
            if context is None:
                # Import sandbox only when needed
                from opendxa.dana.sandbox import DanaSandbox
                sandbox = DanaSandbox()
                context = sandbox.context
            else:
                sandbox = context.sandbox if hasattr(context, "sandbox") else None
            
            if sandbox is None:
                # Fallback to original function if no sandbox available
                if self.config.fallback_strategy == "original":
                    return self.func(*args, **kwargs)
                else:
                    raise RuntimeError("Dana sandbox not available for POET execution")
            
            try:
                # Load the enhanced module
                sandbox.load_file(str(self.enhanced_path))
                
                # Prepare arguments as Dana expressions
                arg_strs = [repr(arg) for arg in args]
                kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
                all_args = ", ".join(filter(None, [*arg_strs, kwargs_str]))
                
                # Call the enhanced function
                result = sandbox.eval(f"enhanced_{self.func.__name__}({all_args})")
                
                # Wrap in POETResult for metadata access
                if not isinstance(result, POETResult):
                    return POETResult(result, self.func.__name__)
                return result
                
            except Exception as e:
                if self.config.fallback_strategy == "original":
                    # Fallback to original function
                    return self.func(*args, **kwargs)
                else:
                    raise RuntimeError(f"POET execution failed: {e}") from e
        
        self.wrapper = wrapper

    def __call__(self, *args, **kwargs) -> Any:
        """Make the decorator callable like a function."""
        return self.wrapper(*args, **kwargs)

    def __repr__(self) -> str:
        return f"POETDecorator(func={self.func.__name__}, domain={self.config.domain})"


def poet(
    domain: str | None = None,
    retries: int = 1,
    timeout: int | None = None,
    optimize_for: str | None = None,
    enable_monitoring: bool = True,
    cache_strategy: str = "auto",
    fallback_strategy: str = "raise",
    **kwargs,
) -> Any:
    """
    POET decorator that enhances functions with Perceive→Operate→Enforce→Train phases.
    
    The decorator generates Dana code implementing the four phases and stores it locally
    in .dana/poet/{function_name}.na. When the function is called, the enhanced version
    is executed in the Dana sandbox.
    
    Args:
        domain: Domain template (e.g., "mathematical_operations", "llm_optimization")
        retries: Number of retry attempts (used in Operate phase)
        timeout: Timeout in seconds (used in Operate phase)
        optimize_for: Learning target (enables Train phase)
        enable_monitoring: Enable execution monitoring
        cache_strategy: Caching behavior for enhanced code
        fallback_strategy: What to do on error ("raise" or "original")
        
    Returns:
        Enhanced function with P→O→E(→T) capabilities
        
    Example:
        @poet(domain="mathematical_operations")
        def safe_divide(a: float, b: float) -> float:
            return a / b
            
        # Enhanced function validates inputs, handles errors, and retries
        result = safe_divide(10, 0)  # Graceful error instead of crash
    """
    # Handle Dana's decorator application quirk
    if domain is not None and callable(domain):
        # Dana passed function as first parameter
        func = domain
        return POETDecorator(func)
    
    def decorator(func: Callable) -> POETDecorator:
        """Apply POET enhancement to function."""
        return POETDecorator(
            func=func,
            domain=domain or "computation",
            retries=retries,
            timeout=timeout,
            optimize_for=optimize_for,
            enable_monitoring=enable_monitoring,
            cache_strategy=cache_strategy,
            fallback_strategy=fallback_strategy,
            **kwargs,
        )
    
    return decorator


def feedback(execution_id: str, content: str | dict | Any, **kwargs) -> bool:
    """Provide feedback for a POET function execution.
    
    When a function has optimize_for set, this feedback is used by the Train phase
    to improve future executions.
    
    Args:
        execution_id: The execution ID from POETResult._poet.execution_id
        content: Feedback content (string, dict, or any format)
        **kwargs: Additional feedback parameters
        
    Returns:
        True if feedback was processed, False otherwise
    """
    try:
        # Import storage to save feedback
        from opendxa.dana.poet.storage import POETStorage
        
        storage = POETStorage()
        return storage.save_feedback(execution_id, {
            "content": content,
            "metadata": kwargs,
            "timestamp": storage._get_timestamp(),
        })
    except Exception:
        return False
