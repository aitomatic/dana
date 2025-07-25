"""
POET Workflow Helpers - Automatic Workflow Metadata Construction

This module provides helper functions to automatically construct workflow metadata
from poet-decorated functions, eliminating the need for manual metadata definition.

Key Features:
- Automatic workflow metadata construction from poet() decorators
- Integration with Dana's pipe operator composition
- Support for both individual functions and composed pipelines
- Backward compatibility with existing workflow patterns
"""

from collections.abc import Callable
from typing import Any

from .decorator import extract_poet_metadata
from .metadata_extractor import extract_pipeline_metadata, extract_workflow_metadata


def create_workflow_metadata(
    functions: list[Callable], workflow_id: str | None = None, description: str | None = None, version: str = "1.0.0"
) -> dict[str, Any]:
    """
    Automatically create workflow metadata from a list of functions.

    This function extracts metadata from each function's docstring and poet() decorator,
    automatically constructing a complete workflow metadata dictionary.

    Args:
        functions: List of functions in the workflow (can be poet-decorated or plain)
        workflow_id: Optional workflow identifier
        description: Optional workflow description
        version: Workflow version

    Returns:
        Complete workflow metadata dictionary

    Example:
        ```python
        @poet(domain="document_processing", retries=3)
        def ingest_document(file_path):
            \"\"\"Ingest document from file system with validation.\"\"\"
            # ... implementation

        @poet(domain="ocr", timeout=30)
        def perform_ocr(document):
            \"\"\"Perform OCR on ingested document.\"\"\"
            # ... implementation

        # Automatically construct metadata
        metadata = create_workflow_metadata([
            ingest_document,
            perform_ocr
        ], workflow_id="doc_processing_001")
        ```
    """
    return extract_workflow_metadata(functions, workflow_id, description, version)


def create_pipeline_metadata(
    pipeline_func: Callable, workflow_id: str | None = None, description: str | None = None, version: str = "1.0.0"
) -> dict[str, Any]:
    """
    Automatically create workflow metadata from a composed pipeline function.

    This function extracts metadata from a pipeline created using Dana's pipe operator,
    automatically constructing workflow metadata from the individual functions.

    Args:
        pipeline_func: A composed function (e.g., from pipe operator)
        workflow_id: Optional workflow identifier
        description: Optional workflow description
        version: Workflow version

    Returns:
        Complete workflow metadata dictionary

    Example:
        ```python
        # Create pipeline using pipe operator
        document_processing_workflow = ingest_document | perform_ocr | analyze_content

        # Automatically construct metadata
        metadata = create_pipeline_metadata(
            document_processing_workflow,
            workflow_id="doc_processing_001"
        )
        ```
    """
    metadata = extract_pipeline_metadata(pipeline_func)

    # Override with provided parameters
    if workflow_id:
        metadata["workflow_id"] = workflow_id
    if description:
        metadata["description"] = description
    if version:
        metadata["version"] = version

    return metadata


def with_workflow_metadata(workflow_id: str | None = None, description: str | None = None, version: str = "1.0.0") -> Callable:
    """
    Decorator to automatically add workflow metadata to a pipeline function.

    Args:
        workflow_id: Optional workflow identifier
        description: Optional workflow description
        version: Workflow version

    Returns:
        Decorator function

    Example:
        ```python
        @with_workflow_metadata(workflow_id="doc_processing_001")
        def document_processing_workflow(input_data):
            return ingest_document | perform_ocr | analyze_content

        # The workflow now has automatic metadata
        metadata = document_processing_workflow.workflow_metadata
        ```
    """

    def decorator(pipeline_func: Callable) -> Callable:
        # Extract metadata from the pipeline
        metadata = create_pipeline_metadata(pipeline_func, workflow_id, description, version)

        # Attach metadata to the function
        pipeline_func.workflow_metadata = metadata

        return pipeline_func

    return decorator


def auto_workflow_metadata(func: Callable) -> Callable:
    """
    Decorator that automatically extracts and attaches workflow metadata.

    This is a convenience decorator that can be applied to any function
    to automatically extract its metadata for workflow construction.

    Args:
        func: The function to extract metadata from

    Returns:
        Function with metadata attached

    Example:
        ```python
        @poet(domain="document_processing", retries=3)
        @auto_workflow_metadata
        def ingest_document(file_path):
            \"\"\"Ingest document from file system with validation.\"\"\"
            # ... implementation

        # Function now has metadata attached
        metadata = ingest_document.workflow_metadata
        ```
    """
    # Extract metadata
    metadata = extract_poet_metadata(func)

    # Attach metadata to function
    func.workflow_metadata = metadata

    return func


# Convenience function for backward compatibility
def build_workflow_metadata(*args, **kwargs) -> dict[str, Any]:
    """
    Backward compatibility function for building workflow metadata.

    This function provides the same interface as the old manual metadata construction,
    but automatically extracts information from functions.

    Args:
        *args: Functions to extract metadata from
        **kwargs: Additional metadata parameters

    Returns:
        Workflow metadata dictionary
    """
    functions = list(args)

    # Extract keyword arguments for metadata
    workflow_id = kwargs.pop("workflow_id", None)
    description = kwargs.pop("description", None)
    version = kwargs.pop("version", "1.0.0")

    # Create metadata
    metadata = create_workflow_metadata(functions, workflow_id, description, version)

    # Add any additional metadata
    metadata.update(kwargs)

    return metadata
