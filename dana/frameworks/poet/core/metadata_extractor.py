"""
POET Metadata Extractor - Automatic Workflow Metadata Construction

This module provides utilities to automatically construct workflow metadata
from function docstrings and poet() decorator parameters, eliminating the
need for manual metadata definition.

Key Features:
- Extract function names automatically
- Parse docstrings for descriptions
- Extract poet() decorator parameters (retry_count, timeout, etc.)
- Generate comprehensive workflow metadata
- Support for both Python and Dana functions
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FunctionMetadata:
    """Metadata extracted from a function and its poet() decorator."""

    name: str
    description: str
    retry_count: int = 3
    timeout: float | None = None
    domain: str | None = None
    model: str | None = None
    confidence_threshold: float | None = None
    format: str | None = None
    additional_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for workflow metadata."""
        result: dict[str, Any] = {"name": self.name, "description": self.description}

        # Add poet parameters if they exist
        # Always include retry_count if it's explicitly set (even if it's the default)
        result["retry_count"] = self.retry_count
        if self.timeout is not None:
            result["timeout"] = self.timeout
        if self.domain is not None:
            result["domain"] = self.domain
        if self.model is not None:
            result["model"] = self.model
        if self.confidence_threshold is not None:
            result["confidence_threshold"] = self.confidence_threshold
        if self.format is not None:
            result["format"] = self.format

        # Add any additional parameters
        result.update(self.additional_params)

        return result


class MetadataExtractor:
    """Extract metadata from functions and their poet() decorators."""

    def __init__(self):
        """Initialize the metadata extractor."""
        pass

    def extract_function_metadata(self, func: Callable) -> FunctionMetadata:
        """
        Extract metadata from a function and its poet() decorator.

        Args:
            func: The function to extract metadata from

        Returns:
            FunctionMetadata with extracted information
        """
        # Get function name
        name = getattr(func, "__name__", str(func))

        # Extract docstring description
        description = self._extract_description_from_docstring(func)

        # Extract poet configuration
        poet_config = self._extract_poet_config(func)

        # Create metadata object
        metadata = FunctionMetadata(
            name=name,
            description=description,
            retry_count=poet_config.get("retries", poet_config.get("retry_count", 3)),
            timeout=poet_config.get("timeout"),
            domain=poet_config.get("domain"),
            additional_params=self._extract_additional_params(poet_config),
        )

        return metadata

    def _extract_description_from_docstring(self, func: Callable) -> str:
        """
        Extract description from function docstring.

        Args:
            func: The function to extract docstring from

        Returns:
            Description string, or function name if no docstring
        """
        doc = getattr(func, "__doc__", None)
        if not doc:
            return f"Execute {getattr(func, '__name__', 'function')}"

        # Clean up docstring - take first line and remove quotes
        lines = doc.strip().split("\n")
        first_line = lines[0].strip()

        # Remove quotes if present
        if first_line.startswith('"') and first_line.endswith('"'):
            first_line = first_line[1:-1]
        elif first_line.startswith("'") and first_line.endswith("'"):
            first_line = first_line[1:-1]

        return first_line

    def _extract_poet_config(self, func: Callable) -> dict[str, Any]:
        """
        Extract poet() configuration from function.

        Args:
            func: The function to extract poet config from

        Returns:
            Dictionary of poet configuration parameters
        """
        config = {}

        # Check for _poet_config attribute (from poet decorator)
        if hasattr(func, "_poet_config"):
            poet_config = func._poet_config
            if isinstance(poet_config, dict):
                config.update(poet_config)

        # Check for metadata attribute (legacy format)
        if hasattr(func, "metadata") and isinstance(func.metadata, dict):
            config.update(func.metadata)

        # Check for step_name attribute
        if hasattr(func, "step_name"):
            config["step_name"] = func.step_name

        return config

    def _extract_additional_params(self, poet_config: dict[str, Any]) -> dict[str, Any]:
        """
        Extract additional parameters from poet config.

        Args:
            poet_config: The poet configuration dictionary

        Returns:
            Dictionary of additional parameters
        """
        additional = {}

        # Extract common parameters that might be in poet config
        for key in ["model", "confidence_threshold", "format", "profile", "interrupts"]:
            if key in poet_config:
                additional[key] = poet_config[key]

        # Extract operate phase parameters
        if "operate" in poet_config and isinstance(poet_config["operate"], dict):
            operate_config = poet_config["operate"]
            for key in ["timeout", "retries", "model"]:
                if key in operate_config:
                    additional[key] = operate_config[key]

        # Extract enforce phase parameters
        if "enforce" in poet_config and isinstance(poet_config["enforce"], dict):
            enforce_config = poet_config["enforce"]
            for key in ["confidence_threshold", "compliance_check"]:
                if key in enforce_config:
                    additional[key] = enforce_config[key]

        return additional


def extract_workflow_metadata(
    functions: list[Callable], workflow_id: str | None = None, description: str | None = None, version: str = "1.0.0"
) -> dict[str, Any]:
    """
    Automatically construct workflow metadata from a list of functions.

    Args:
        functions: List of functions in the workflow
        workflow_id: Optional workflow identifier
        description: Optional workflow description
        version: Workflow version

    Returns:
        Complete workflow metadata dictionary
    """
    extractor = MetadataExtractor()

    # Extract metadata from each function
    steps = []
    for func in functions:
        metadata = extractor.extract_function_metadata(func)
        steps.append(metadata.to_dict())

    # Construct workflow metadata
    workflow_metadata = {
        "workflow_id": workflow_id or f"workflow_{id(functions)}",
        "description": description or f"Workflow with {len(functions)} steps",
        "version": version,
        "steps": steps,
    }

    return workflow_metadata


def extract_pipeline_metadata(pipeline_func: Callable) -> dict[str, Any]:
    """
    Extract metadata from a composed pipeline function.

    Args:
        pipeline_func: A composed function (e.g., from pipe operator)

    Returns:
        Workflow metadata dictionary
    """
    # Try to extract functions from the pipeline
    functions = _extract_functions_from_pipeline(pipeline_func)

    if functions:
        return extract_workflow_metadata(functions)
    else:
        # Fallback to basic metadata
        return {
            "workflow_id": f"pipeline_{id(pipeline_func)}",
            "description": f"Pipeline: {getattr(pipeline_func, '__name__', 'unknown')}",
            "version": "1.0.0",
            "steps": [],
        }


def _extract_functions_from_pipeline(pipeline_func: Callable) -> list[Callable]:
    """
    Attempt to extract individual functions from a pipeline.

    Args:
        pipeline_func: A composed function

    Returns:
        List of functions in the pipeline, or empty list if not extractable
    """
    functions = []

    # Check if it's a ComposedFunction (from Dana's pipe operator)
    if hasattr(pipeline_func, "_functions"):
        functions = pipeline_func._functions
    elif hasattr(pipeline_func, "functions"):
        functions = pipeline_func.functions

    # If we found functions, flatten any nested compositions
    if functions:
        flattened = []
        for func in functions:
            if hasattr(func, "_functions") and hasattr(func._functions, "__iter__"):
                try:
                    flattened.extend(func._functions)
                except (TypeError, AttributeError):
                    # Handle case where _functions is not iterable (e.g., Mock objects)
                    flattened.append(func)
            else:
                flattened.append(func)
        return flattened

    return []


# Convenience functions for common use cases
def with_metadata(func: Callable, **metadata) -> Callable:
    """
    Add metadata to a function for workflow tracking.

    Args:
        func: The function to add metadata to
        **metadata: Metadata key-value pairs

    Returns:
        Function with metadata attached
    """
    func.metadata = metadata
    return func


def workflow_step(
    name: str | None = None, description: str | None = None, retry_count: int = 3, timeout: float | None = None, **kwargs
) -> Callable:
    """
    Decorator to mark a function as a workflow step with metadata.

    Args:
        name: Step name (defaults to function name)
        description: Step description (defaults to docstring)
        retry_count: Number of retry attempts
        timeout: Timeout in seconds
        **kwargs: Additional metadata

    Returns:
        Decorated function with metadata
    """

    def decorator(func: Callable) -> Callable:
        # Extract metadata
        step_name = name or getattr(func, "__name__", "unknown")
        step_description = description or _extract_first_line_docstring(func)

        # Create metadata
        metadata = {"name": step_name, "description": step_description, "retry_count": retry_count, "timeout": timeout, **kwargs}

        # Attach metadata to function
        func.metadata = metadata
        func.step_name = step_name

        return func

    return decorator


def _extract_first_line_docstring(func: Callable) -> str:
    """Extract first line of docstring for description."""
    doc = getattr(func, "__doc__", None)
    if not doc:
        return f"Execute {getattr(func, '__name__', 'function')}"

    lines = doc.strip().split("\n")
    first_line = lines[0].strip()

    # Remove quotes if present
    if first_line.startswith('"') and first_line.endswith('"'):
        first_line = first_line[1:-1]
    elif first_line.startswith("'") and first_line.endswith("'"):
        first_line = first_line[1:-1]

    return first_line
