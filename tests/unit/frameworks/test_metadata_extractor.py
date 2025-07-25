"""
Tests for POET Metadata Extractor - Automatic Workflow Metadata Construction

This module tests the automatic extraction of workflow metadata from
function docstrings and poet() decorator parameters.
"""

from unittest.mock import Mock

from dana.frameworks.poet.core.metadata_extractor import (
    FunctionMetadata,
    MetadataExtractor,
    extract_pipeline_metadata,
    extract_workflow_metadata,
    with_metadata,
    workflow_step,
)
from dana.frameworks.poet.core.workflow_helpers import build_workflow_metadata, create_pipeline_metadata, create_workflow_metadata


class TestMetadataExtractor:
    """Test suite for MetadataExtractor."""

    def test_extract_function_metadata_basic(self):
        """Test basic metadata extraction from a function."""
        extractor = MetadataExtractor()

        def test_function(x):
            """Test function with docstring."""
            return x * 2

        metadata = extractor.extract_function_metadata(test_function)

        assert metadata.name == "test_function"
        assert metadata.description == "Test function with docstring."
        assert metadata.retry_count == 3  # Default value
        assert metadata.timeout is None

    def test_extract_function_metadata_with_poet_config(self):
        """Test metadata extraction from a function with poet configuration."""
        extractor = MetadataExtractor()

        def test_function(x):
            """Test function with poet config."""
            return x * 2

        # Simulate poet decorator configuration
        test_function._poet_config = {
            "domain": "test_domain",
            "retries": 5,
            "timeout": 30.0,
            "operate": {"model": "gpt-4"},
            "enforce": {"confidence_threshold": 0.9},
        }

        metadata = extractor.extract_function_metadata(test_function)

        assert metadata.name == "test_function"
        assert metadata.description == "Test function with poet config."
        assert metadata.retry_count == 5
        assert metadata.timeout == 30.0
        assert metadata.domain == "test_domain"
        assert metadata.additional_params["model"] == "gpt-4"
        assert metadata.additional_params["confidence_threshold"] == 0.9

    def test_extract_function_metadata_with_legacy_metadata(self):
        """Test metadata extraction from function with legacy metadata attribute."""
        extractor = MetadataExtractor()

        def test_function(x):
            """Test function with legacy metadata."""
            return x * 2

        # Simulate legacy metadata
        test_function.metadata = {"description": "Legacy description", "retry_count": 7, "timeout": 60.0}
        test_function.step_name = "legacy_step"

        metadata = extractor.extract_function_metadata(test_function)

        assert metadata.name == "test_function"
        assert metadata.description == "Test function with legacy metadata."
        assert metadata.retry_count == 7
        assert metadata.timeout == 60.0

    def test_extract_description_from_docstring(self):
        """Test docstring description extraction."""
        extractor = MetadataExtractor()

        def func1():
            """Simple docstring."""
            pass

        def func2():
            """Multi-line docstring.

            This is a longer description.
            """
            pass

        def func3():
            pass  # No docstring

        assert extractor._extract_description_from_docstring(func1) == "Simple docstring."
        assert extractor._extract_description_from_docstring(func2) == "Multi-line docstring."
        assert extractor._extract_description_from_docstring(func3) == "Execute func3"


class TestWorkflowMetadataConstruction:
    """Test suite for workflow metadata construction."""

    def test_extract_workflow_metadata(self):
        """Test automatic workflow metadata construction."""

        def step1(x):
            """First step."""
            return x + 1

        def step2(x):
            """Second step."""
            return x * 2

        # Add poet config to simulate decorated functions
        step1._poet_config = {"domain": "math", "retries": 3}
        step2._poet_config = {"domain": "math", "timeout": 10.0}

        metadata = extract_workflow_metadata([step1, step2], workflow_id="test_workflow", description="Test workflow", version="1.0.0")

        assert metadata["workflow_id"] == "test_workflow"
        assert metadata["description"] == "Test workflow"
        assert metadata["version"] == "1.0.0"
        assert len(metadata["steps"]) == 2

        # Check step metadata
        step1_meta = metadata["steps"][0]
        assert step1_meta["name"] == "step1"
        assert step1_meta["description"] == "First step."
        assert step1_meta["retry_count"] == 3
        assert step1_meta["domain"] == "math"

        step2_meta = metadata["steps"][1]
        assert step2_meta["name"] == "step2"
        assert step2_meta["description"] == "Second step."
        assert step2_meta["timeout"] == 10.0
        assert step2_meta["domain"] == "math"

    def test_create_workflow_metadata(self):
        """Test create_workflow_metadata helper function."""

        def step1(x):
            """First step."""
            return x + 1

        def step2(x):
            """Second step."""
            return x * 2

        metadata = create_workflow_metadata([step1, step2], workflow_id="helper_test", description="Helper test workflow")

        assert metadata["workflow_id"] == "helper_test"
        assert metadata["description"] == "Helper test workflow"
        assert len(metadata["steps"]) == 2

    def test_build_workflow_metadata_backward_compatibility(self):
        """Test backward compatibility function."""

        def step1(x):
            """First step."""
            return x + 1

        def step2(x):
            """Second step."""
            return x * 2

        metadata = build_workflow_metadata(step1, step2, workflow_id="backward_test", description="Backward compatibility test")

        assert metadata["workflow_id"] == "backward_test"
        assert metadata["description"] == "Backward compatibility test"
        assert len(metadata["steps"]) == 2


class TestPipelineMetadataExtraction:
    """Test suite for pipeline metadata extraction."""

    def test_extract_pipeline_metadata_mock_pipeline(self):
        """Test pipeline metadata extraction with mock pipeline."""
        # Create a mock pipeline function with proper structure
        mock_pipeline = Mock()
        mock_step1 = Mock(__name__="step1", __doc__="First step.")
        mock_step2 = Mock(__name__="step2", __doc__="Second step.")
        mock_pipeline._functions = [mock_step1, mock_step2]

        metadata = extract_pipeline_metadata(mock_pipeline)

        assert "workflow_id" in metadata
        assert "steps" in metadata
        assert len(metadata["steps"]) == 2

    def test_create_pipeline_metadata(self):
        """Test create_pipeline_metadata helper function."""
        # Create a mock pipeline function with proper structure
        mock_pipeline = Mock()
        mock_step1 = Mock(__name__="step1", __doc__="First step.")
        mock_step2 = Mock(__name__="step2", __doc__="Second step.")
        mock_pipeline._functions = [mock_step1, mock_step2]

        metadata = create_pipeline_metadata(mock_pipeline, workflow_id="pipeline_test", description="Pipeline test workflow")

        assert metadata["workflow_id"] == "pipeline_test"
        assert metadata["description"] == "Pipeline test workflow"


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_with_metadata(self):
        """Test with_metadata convenience function."""

        def test_func(x):
            return x * 2

        decorated_func = with_metadata(test_func, retry_count=5, timeout=30.0, domain="test")

        assert decorated_func.metadata["retry_count"] == 5
        assert decorated_func.metadata["timeout"] == 30.0
        assert decorated_func.metadata["domain"] == "test"

    def test_workflow_step_decorator(self):
        """Test workflow_step decorator."""

        @workflow_step(name="custom_name", description="Custom description", retry_count=7, timeout=60.0)
        def test_func(x):
            """Original docstring."""
            return x * 2

        assert test_func.metadata["name"] == "custom_name"
        assert test_func.metadata["description"] == "Custom description"
        assert test_func.metadata["retry_count"] == 7
        assert test_func.metadata["timeout"] == 60.0
        assert test_func.step_name == "custom_name"

    def test_workflow_step_decorator_defaults(self):
        """Test workflow_step decorator with defaults."""

        @workflow_step()
        def test_func(x):
            """Test function docstring."""
            return x * 2

        assert test_func.metadata["name"] == "test_func"
        assert test_func.metadata["description"] == "Test function docstring."
        assert test_func.metadata["retry_count"] == 3  # Default
        assert test_func.step_name == "test_func"


class TestFunctionMetadata:
    """Test suite for FunctionMetadata dataclass."""

    def test_function_metadata_to_dict(self):
        """Test FunctionMetadata.to_dict() method."""
        metadata = FunctionMetadata(
            name="test_func",
            description="Test function",
            retry_count=5,
            timeout=30.0,
            domain="test_domain",
            additional_params={"custom_param": "value"},
        )

        result = metadata.to_dict()

        assert result["name"] == "test_func"
        assert result["description"] == "Test function"
        assert result["retry_count"] == 5
        assert result["timeout"] == 30.0
        assert result["domain"] == "test_domain"
        assert result["custom_param"] == "value"

    def test_function_metadata_to_dict_defaults(self):
        """Test FunctionMetadata.to_dict() with default values."""
        metadata = FunctionMetadata(name="test_func", description="Test function")

        result = metadata.to_dict()

        assert result["name"] == "test_func"
        assert result["description"] == "Test function"
        # retry_count is always included now
        assert result["retry_count"] == 3
        # timeout should not be included when None
        assert "timeout" not in result
