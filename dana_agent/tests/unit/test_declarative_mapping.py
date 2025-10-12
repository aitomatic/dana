"""Tests for declarative input/output mapping in BaseWorkflow."""

import pytest

from dana_agent.common.protocols import DictParams
from dana_agent.core.workflow.base_workflow import BaseWorkflow


class SimpleWorkflow(BaseWorkflow):
    """A simple workflow for testing."""

    def _do_execute(self, **kwargs) -> DictParams:
        """Just return what was passed in."""
        return {"data": kwargs.get("input_data", "default")}


class TestDeclarativeMapping:
    """Test the declarative mapping functionality in BaseWorkflow."""

    def test_input_mapping_simple(self):
        """Test simple input mapping with direct path."""
        workflow = SimpleWorkflow("input_data=source.value")

        result = workflow.execute(source={"value": "test_value"})

        # The input mapping should have extracted source.value and set input_data
        assert result["result"]["data"] == "test_value"

    def test_input_mapping_with_fallback(self):
        """Test input mapping with fallback paths."""
        workflow = SimpleWorkflow("input_data=primary.value|backup")

        # Test with primary path available
        result = workflow.execute(primary={"value": "from_primary"}, backup="from_backup")
        assert result["result"]["data"] == "from_primary"

        # Test with only fallback path available
        result = workflow.execute(backup="from_backup")
        assert result["result"]["data"] == "from_backup"

    def test_input_mapping_array_indexing(self):
        """Test input mapping with array indexing."""
        workflow = SimpleWorkflow("input_data=items.0.name")

        result = workflow.execute(items=[{"name": "first"}, {"name": "second"}])

        assert result["result"]["data"] == "first"

    def test_input_mapping_multiple_fields(self):
        """Test input mapping with multiple field mappings."""

        class MultiFieldWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs) -> DictParams:
                return {"field1": kwargs.get("a"), "field2": kwargs.get("b")}

        workflow = MultiFieldWorkflow("a=source.x, b=source.y")

        result = workflow.execute(source={"x": "value1", "y": "value2"})

        assert result["result"]["field1"] == "value1"
        assert result["result"]["field2"] == "value2"

    def test_output_mapping(self):
        """Test output key renaming."""
        workflow = SimpleWorkflow("-> custom_result")

        result = workflow.execute(input_data="test")

        # Should have renamed "result" to "custom_result"
        assert "custom_result" in result
        assert "result" not in result
        assert result["custom_result"]["data"] == "test"

    def test_output_mapping_default(self):
        """Test that output defaults to 'result'."""
        workflow = SimpleWorkflow()

        result = workflow.execute(input_data="test")

        # Should keep the default "result" key
        assert "result" in result
        assert result["result"]["data"] == "test"

    def test_combined_input_output_mapping(self):
        """Test using both input and output mapping together."""
        workflow = SimpleWorkflow("input_data=source.nested.value|fallback -> custom_output")

        result = workflow.execute(source={"nested": {"value": "nested_value"}}, fallback="backup")

        # Should have mapped input and renamed output
        assert "custom_output" in result
        assert "result" not in result
        assert result["custom_output"]["data"] == "nested_value"

    def test_input_mapping_missing_path(self):
        """Test input mapping when path doesn't exist."""
        workflow = SimpleWorkflow("input_data=nonexistent.path")

        result = workflow.execute()

        # Should set empty string for missing path
        assert result["result"]["data"] == ""

    def test_cannot_use_transform_with_pre_callable(self):
        """Test that using both transform and pre_callable raises an error."""
        with pytest.raises(ValueError, match="Cannot specify 'transform' with 'pre_callable' or 'post_callable'"):
            SimpleWorkflow("a=b", pre_callable=lambda x: x)

    def test_cannot_use_transform_with_post_callable(self):
        """Test that using both transform and post_callable raises an error."""
        with pytest.raises(ValueError, match="Cannot specify 'transform' with 'pre_callable' or 'post_callable'"):
            SimpleWorkflow("-> custom", post_callable=lambda x: x)

    def test_composite_workflow_with_declarative_mapping(self):
        """Test that declarative mapping works with composite workflows."""

        class FirstWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs) -> DictParams:
                return {"items": [{"url": "http://example.com"}]}

        class SecondWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs) -> DictParams:
                return {"fetched": kwargs.get("target_url", "no url")}

        composite = FirstWorkflow("-> search_result") | SecondWorkflow("target_url=search_result.items.0.url -> fetch_result")

        result = composite.execute()

        # Should have both outputs with correct mappings
        assert "search_result" in result
        assert "fetch_result" in result
        assert result["fetch_result"]["fetched"] == "http://example.com"

    def test_output_only_mapping(self):
        """Test using only output mapping without input mappings."""
        workflow = SimpleWorkflow("-> renamed_output")

        result = workflow.execute(input_data="test")

        # Should only rename output, not transform inputs
        assert "renamed_output" in result
        assert "result" not in result
        assert result["renamed_output"]["data"] == "test"

    def test_input_only_mapping(self):
        """Test using only input mapping without output renaming."""
        workflow = SimpleWorkflow("input_data=source.value")

        result = workflow.execute(source={"value": "test"})

        # Should transform input but keep default output name
        assert "result" in result
        assert result["result"]["data"] == "test"
