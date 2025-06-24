"""
POET (Perceive-Operate-Enforce-Train) decorator implementation.

This module provides the POET decorator for Dana code enhancement.
"""

from pathlib import Path
from typing import Any

from opendxa.dana.poet.types import POETConfig
from opendxa.dana.sandbox.parser.ast import ImportStatement
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class POETMetadata:
    """Metadata container for POET enhanced Dana code"""

    def __init__(self, dana_code: str, config: POETConfig):
        self.dana_code = dana_code
        self.version = 1
        self.config = config
        from pathlib import Path

        self.enhanced_path = Path("tmp") / "enhanced.na"

    def __getitem__(self, key):
        if key in ("domains", "domain"):
            return [self.config.domain] if self.config.domain else []
        if key == "retries":
            return getattr(self.config, "retries", None)
        if key == "timeout":
            return getattr(self.config, "timeout", None)
        if key == "version":
            return self.version
        if key == "enhanced_path":
            return self.enhanced_path
        if key == "namespace":
            return "local"
        raise KeyError(key)


class POETDecorator:
    """
    Enhanced POET decorator that generates and executes Dana-based enhancements.

    The decorator works by:
    1. Checking for enhanced Dana code in ./dana/{function_name}.na
    2. Enhancing the Dana code using POETEnhancer
    3. Executing the enhanced code in the Dana sandbox
    """

    def __init__(self, dana_code: str, domain: str | None = None, **kwargs):
        """Initialize the POET decorator.

        Args:
            dana_code: The Dana code to enhance
            domain: Domain context for enhancement
            **kwargs: Additional configuration options
        """
        self.dana_code = dana_code
        self.config = POETConfig(domain=domain, **kwargs)
        self._poet_metadata = POETMetadata(dana_code, self.config)
        # Always write enhanced code to ./dana/{domain}_enhanced.na
        dana_dir = Path("dana")
        dana_dir.mkdir(exist_ok=True)
        self.enhanced_path = dana_dir / f"{domain or 'default'}_enhanced.na"
        self._create_wrapper()

    def _ensure_enhanced_code_exists(self) -> None:
        if not self.enhanced_path.exists():
            from opendxa.dana.poet.enhancer import POETEnhancer

            enhancer = POETEnhancer()
            dana_code = enhancer.enhance(self.dana_code, self.config)
            self.enhanced_path.write_text(dana_code)

    def _load_enhanced_module(self, sandbox_context: SandboxContext) -> Any:
        # Use Dana's native import system
        module_name = self.enhanced_path.stem
        if hasattr(sandbox_context, "_interpreter") and sandbox_context._interpreter:
            import_stmt = ImportStatement(module=module_name, alias=None)
            sandbox_context._interpreter.execute_statement(import_stmt, sandbox_context)
            return sandbox_context.get_from_scope(module_name, scope="local")
        else:
            raise RuntimeError("No interpreter available in sandbox context")

    def _create_wrapper(self) -> None:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self._ensure_enhanced_code_exists()
            context = kwargs.pop("context", None)
            if context is None:
                from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
                from opendxa.dana.sandbox.sandbox_context import SandboxContext

                context = SandboxContext()
                context._interpreter = DanaInterpreter()
            enhanced_module = self._load_enhanced_module(context)
            enhanced_func_name = f"enhanced_{self.dana_code}"
            if not hasattr(enhanced_module, enhanced_func_name):
                raise RuntimeError(f"Enhanced function {enhanced_func_name} not found in module {enhanced_module}")
            enhanced_func = getattr(enhanced_module, enhanced_func_name)
            # Call the enhanced function using Dana's context and interpreter
            if hasattr(enhanced_func, "execute"):
                return enhanced_func.execute(context, *args, **kwargs)
            return enhanced_func(*args, **kwargs)

        self.wrapper = wrapper

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.wrapper(*args, **kwargs)

    def __repr__(self) -> str:
        return f"POETDecorator(dana_code={self.dana_code}, domain={self.config.domain}, enable_training={self.config.enable_training})"

    @property
    def metadata(self) -> POETMetadata:
        """Get the POET metadata for this decorated function."""
        return self._poet_metadata


def poet(dana_code: str, *, domain: str | None = None, **kwargs) -> Any:
    """Factory for POETDecorator. Accepts Dana code as a string and returns a POETDecorator instance."""
    return POETDecorator(dana_code, domain=domain, **kwargs)


def feedback(execution_id: str, content: str | dict | Any, **kwargs) -> bool:
    """Provide feedback for a POET function execution.

    When a function has optimize_for set, this feedback is used by the Train phase
    to improve future executions. The LLM learns from this feedback to generate
    better enhancements.

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
        return storage.save_feedback(
            execution_id,
            {
                "content": content,
                "metadata": kwargs,
                "timestamp": storage._get_timestamp(),
            },
        )
    except Exception as e:
        print(f"POET: Failed to save feedback: {e}")
        return False
