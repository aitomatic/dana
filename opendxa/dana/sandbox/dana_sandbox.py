"""
Dana Sandbox - Public API Entry Point

This module provides the main public API for executing Dana code.
Users should interact with DanaSandbox rather than the internal DanaInterpreter.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


@dataclass
class ExecutionResult:
    """Result of executing Dana code."""

    success: bool
    result: Any = None
    final_context: SandboxContext | None = None
    execution_time: float = 0.0
    error: Exception | None = None
    output: str = ""

    def __str__(self) -> str:
        """Human-readable execution summary."""
        if self.success:
            return f"Success: {self.result}"
        else:
            return f"Error: {self.error}"


class DanaSandbox:
    """
    Dana Sandbox - The official way to execute Dana code.

    This is the main public API that users should interact with.
    It provides a clean, safe interface for running Dana files and evaluating code.
    """

    def __init__(
        self,
        debug: bool = False,
        context: SandboxContext | None = None,
        default_llm: LLMResource | None = None,
        llm_resources_map: dict[str, LLMResource] | None = None,
    ):
        """
        Initialize a Dana sandbox.

        Args:
            debug: Enable debug logging
            context: Optional custom context (creates default if None).
                     If provided, it's assumed to be pre-configured.
            default_llm: Optional pre-initialized default LLMResource.
            llm_resources_map: Optional pre-initialized map of named LLMResources.
        """
        self.debug = debug
        self._provided_default_llm = default_llm
        self._provided_llm_resources_map = llm_resources_map

        self._context = context or SandboxContext()  # Create context if not provided
        self._initialize_llm_resources(self._context)  # Populate with LLMs

        self._interpreter = DanaInterpreter()
        self._parser = DanaParser()

    def _initialize_llm_resources(self, context: SandboxContext) -> None:
        """Initializes and sets LLM resources in the provided context."""
        logger = DXA_LOGGER.getLogger("opendxa.dana.sandbox")

        # Get or create the default LLM
        default_llm = self._provided_default_llm if isinstance(self._provided_default_llm, LLMResource) else LLMResource()
        logger.info(f"Using {'provided' if self._provided_default_llm else 'new'} default LLM: {default_llm.model or 'default'}")

        # Set the default LLM resource
        context.set("system:llm_resource", default_llm)

        # Initialize resources dictionary with default LLM
        resources = {"default": default_llm}
        if default_llm.model:
            resources[default_llm.model] = default_llm

        # Add any additional provided resources
        if isinstance(self._provided_llm_resources_map, dict):
            resources.update(
                {name: resource for name, resource in self._provided_llm_resources_map.items() if isinstance(resource, LLMResource)}
            )

        # Set the resources dictionary
        context.set("system:llm_resources", resources)
        logger.info(f"Initialized system:llm_resources with keys: {list(resources.keys())}")

    def run(self, file_path: str | Path) -> ExecutionResult:
        """
        Run a Dana file.

        Args:
            file_path: Path to the .na file to execute

        Returns:
            ExecutionResult with success status and results
        """
        try:
            # Read file
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if not file_path.suffix == ".na":
                raise ValueError(f"File must have .na extension: {file_path}")

            source_code = file_path.read_text()

            # Use internal _run method for actual execution
            result = self._interpreter._run(file_path, source_code, self._context)
            output = self._interpreter.get_and_clear_output()

            return ExecutionResult(success=True, result=result, final_context=self._context, output=output)

        except Exception as e:
            return ExecutionResult(success=False, error=e, final_context=self._context)

    def eval(self, source_code: str, filename: str | None = None) -> ExecutionResult:
        """
        Evaluate Dana source code.

        Args:
            source_code: Dana code to execute
            filename: Optional filename for error reporting

        Returns:
            ExecutionResult with success status and results
        """
        try:
            # Use internal _eval method for actual execution
            result = self._interpreter._eval(source_code, self._context, filename)
            output = self._interpreter.get_and_clear_output()

            return ExecutionResult(success=True, result=result, final_context=self._context, output=output)

        except Exception as e:
            return ExecutionResult(success=False, error=e, final_context=self._context)

    @classmethod
    def quick_run(cls, file_path: str | Path, debug: bool = False, context: SandboxContext | None = None) -> ExecutionResult:
        """
        Quick file execution (class method).

        Args:
            file_path: Path to the .na file to execute
            debug: Enable debug logging
            context: Optional custom context

        Returns:
            ExecutionResult with success status and results
        """
        sandbox = cls(debug=debug, context=context)
        return sandbox.run(file_path)

    @classmethod
    def quick_eval(
        cls, source_code: str, filename: str | None = None, debug: bool = False, context: SandboxContext | None = None
    ) -> ExecutionResult:
        """
        Quick code evaluation (class method).

        Args:
            source_code: Dana code to execute
            filename: Optional filename for error reporting
            debug: Enable debug logging
            context: Optional custom context

        Returns:
            ExecutionResult with success status and results
        """
        sandbox = cls(debug=debug, context=context)
        return sandbox.eval(source_code, filename)

    def run_file(self, file_path: str) -> Any:
        # This method is not provided in the original file or the code block
        # It's assumed to exist as it's called in the original file
        pass
