"""Sandboxed Python code execution resource."""

from __future__ import annotations

import ast
from typing import Iterable

from dana.common.protocols.war import tool_use
from dana.core.agent.components.python_sandbox import PythonSandbox
from dana.core.resource.base_resource import BaseResource


DEFAULT_ALLOWED_MODULES = (
    "math",
    "statistics",
    "json",
    "re",
    "collections",
    "itertools",
    "functools",
    "datetime",
    "random",
    "string",
)

BLOCKED_BUILTINS = {
    "eval",
    "exec",
    "open",
    "__import__",
    "compile",
    "input",
    "breakpoint",
}


class CodeExecutionResource(BaseResource):
    """Execute Python code safely with stateful, sandboxed execution."""

    def __init__(
        self,
        resource_id: str = "code-execution",
        allowed_modules: Iterable[str] | None = None,
        timeout_seconds: float = 5.0,
        max_output_size: int = 10 * 1024,
        **kwargs,
    ):
        """
        Initialize CodeExecutionResource.

        Args:
            resource_id: Resource identifier (default: "code-execution")
            allowed_modules: Optional modules to extend the whitelist
            timeout_seconds: Execution timeout in seconds (default: 5)
            max_output_size: Max stdout size in bytes (default: 10KB)
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="code-execution", resource_id=resource_id, **kwargs)
        self.execute_count = 0
        self.last_code: str | None = None

        merged_allowed = set(DEFAULT_ALLOWED_MODULES)
        if allowed_modules:
            merged_allowed.update(allowed_modules)

        self._sandbox = PythonSandbox(
            allowed_modules=sorted(merged_allowed),
            max_output_size=max_output_size,
            timeout_seconds=timeout_seconds,
            allow_imports=True,
        )

    @tool_use
    def execute(self, code: str) -> str:
        """
        Execute Python code in a sandboxed environment.

        Args:
            code: Python code to execute

        Returns:
            stdout output, or a clear error message on failure
        """
        validation_error = self._validate_code(code)
        if validation_error is not None:
            return validation_error

        self.execute_count += 1
        self.last_code = code
        return self._sandbox.execute(code, context="")

    @tool_use
    def reset(self) -> str:
        """
        Reset the sandbox namespace.

        Returns:
            Confirmation message
        """
        self._sandbox.reset()
        self.execute_count = 0
        self.last_code = None
        return "Code execution sandbox reset."

    def _validate_code(self, code: str) -> str | None:
        """Validate code for blocked builtins before execution."""
        if not code.strip():
            return None
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return f"Error: SyntaxError: {exc}"

        blocked_name = self._find_blocked_builtin(tree)
        if blocked_name:
            return f"Error: PermissionError: Use of '{blocked_name}' is not allowed."
        return None

    def _find_blocked_builtin(self, tree: ast.AST) -> str | None:
        """Find blocked builtin usage in parsed AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in BLOCKED_BUILTINS:
                return node.id
        return None
