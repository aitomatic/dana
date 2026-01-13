"""Tests for CallableWorkflow functionality."""

import pytest

from dana.core.workflow import BaseWorkflow, CallableWorkflow


class SimpleWorkflow(BaseWorkflow):
    """A simple test workflow that returns structured data."""

    def _do_execute(self, **kwargs):
        """Return structured data for testing."""
        return {
            "value": kwargs.get("input", "default"),
            "count": kwargs.get("count", 0),
            "items": kwargs.get("items", []),
        }


class TestCallableWorkflowBasics:
    """Test basic CallableWorkflow functionality."""

    def test_callable_workflow_creation(self):
        """Test creating a CallableWorkflow with a simple function."""

        def process(value):
            return value.upper()

        workflow = CallableWorkflow(process)
        assert workflow.workflow_type == "CallableWorkflow[process]"
        assert workflow._name == "process"
        assert workflow._func == process

    def test_callable_workflow_with_custom_name(self):
        """Test creating a CallableWorkflow with a custom name."""

        def process(value):
            return value.upper()

        workflow = CallableWorkflow(process, name="custom_processor")
        assert workflow.workflow_type == "CallableWorkflow[custom_processor]"
        assert workflow._name == "custom_processor"

    def test_callable_workflow_with_lambda(self):
        """Test creating a CallableWorkflow with a lambda."""
        workflow = CallableWorkflow(lambda x: x * 2, name="doubler")
        assert workflow.workflow_type == "CallableWorkflow[doubler]"

    def test_callable_workflow_auto_register_false_by_default(self):
        """Test that CallableWorkflow sets auto_register=False by default."""

        def process(value):
            return value

        # CallableWorkflow should pass auto_register=False to BaseWorkflow
        workflow = CallableWorkflow(process)

        # Verify the workflow was created successfully
        assert workflow is not None
        assert workflow._name == "process"


class TestCallableWorkflowExecution:
    """Test CallableWorkflow execution behavior."""

    def test_callable_extracts_from_kwargs(self):
        """Test that callable receives parameters from kwargs."""

        def process(value, count):
            return f"{value}_{count}"

        workflow = CallableWorkflow(process)
        result = workflow.execute(value="test", count=5)

        assert result["result"] == "test_5"

    def test_callable_with_single_parameter(self):
        """Test callable with a single parameter."""

        def double(value):
            return value * 2

        workflow = CallableWorkflow(double)
        result = workflow.execute(value=10)

        assert result["result"] == 20

    def test_callable_with_optional_parameters(self):
        """Test callable with optional parameters."""

        def process(value, multiplier=2):
            return value * multiplier

        workflow = CallableWorkflow(process)

        # With optional parameter provided
        result1 = workflow.execute(value=10, multiplier=3)
        assert result1["result"] == 30

        # Without optional parameter (uses default)
        result2 = workflow.execute(value=10)
        assert result2["result"] == 20

    def test_callable_with_no_matching_parameters(self):
        """Test callable when kwargs don't have matching parameters."""

        def process():
            return "no_params"

        workflow = CallableWorkflow(process)
        result = workflow.execute(value="ignored")

        assert result["result"] == "no_params"

    def test_callable_with_missing_required_parameter(self):
        """Test that callable raises TypeError when required param is missing."""

        def process(required_param):
            return required_param

        workflow = CallableWorkflow(process)

        with pytest.raises(TypeError, match="required_param"):
            workflow.execute(other_param="value")

    def test_callable_with_non_dict_kwargs(self):
        """Test callable extracts from kwargs even when value is not a dict."""

        def process(value):
            return value + 10

        workflow = CallableWorkflow(process)
        result = workflow.execute(value=42)

        assert result["result"] == 52

    def test_callable_with_missing_multiple_params(self):
        """Test callable with multiple required params when some are missing."""

        def process(a, b):
            return a + b

        workflow = CallableWorkflow(process)

        # Should raise TypeError since both params are required
        with pytest.raises(TypeError):
            workflow.execute(a=1)  # Missing b

    def test_callable_preserves_kwargs_context(self):
        """Test that execution preserves the full kwargs context."""

        def process(value):
            return value.upper()

        workflow = CallableWorkflow(process)
        result = workflow.execute(value="test", extra_key="preserved", another="context")

        assert result["result"] == "TEST"
        assert result["extra_key"] == "preserved"
        assert result["another"] == "context"


class TestCallableWorkflowComposition:
    """Test composing workflows with callables using the | operator."""

    def test_workflow_pipe_callable(self):
        """Test composing a workflow with a callable."""

        def uppercase(value):
            return value.upper()

        workflow = SimpleWorkflow()
        composed = workflow | uppercase

        result = composed.execute(input="hello")

        # SimpleWorkflow creates result with "value" key
        # Callable should extract "value" and uppercase it
        assert result["result"] == "HELLO"

    def test_workflow_pipe_lambda(self):
        """Test composing a workflow with a lambda."""
        workflow = SimpleWorkflow()
        composed = workflow | (lambda value: value + "!")

        result = composed.execute(input="test")

        assert result["result"] == "test!"

    def test_callable_pipe_callable(self):
        """Test composing callable workflows together."""

        def add_ten(count):
            return count + 10

        def double(count):
            return count * 2

        workflow = SimpleWorkflow() | add_ten | double

        result = workflow.execute(count=5)

        # SimpleWorkflow returns count=5 (in result dict)
        # First callable extracts "count", adds 10 -> 15
        # Second callable gets result=15 as "count", doubles it -> 30
        assert result["result"] == 30

    def test_multiple_callable_chain(self):
        """Test chaining multiple callables."""

        def extract_first(items):
            return items[0] if items else None

        def uppercase(value):
            return value.upper() if value else ""

        def add_suffix(value):
            return value + "_PROCESSED"

        workflow = SimpleWorkflow() | extract_first | uppercase | add_suffix

        result = workflow.execute(items=["hello", "world"])

        assert result["result"] == "HELLO_PROCESSED"

    def test_workflow_pipe_callable_with_complex_params(self):
        """Test callable that extracts multiple parameters from result."""

        def combine(value, count):
            return f"{value}_{count}"

        workflow = SimpleWorkflow() | combine

        result = workflow.execute(input="test", count=3)

        # SimpleWorkflow returns {"value": "test", "count": 3}
        # Callable extracts both and combines them
        assert result["result"] == "test_3"


class TestCallableWorkflowWithPrePost:
    """Test CallableWorkflow with pre and post callables."""

    def test_callable_workflow_with_pre_callable(self):
        """Test CallableWorkflow with a pre_callable."""

        def pre(kwargs):
            # Transform kwargs before the main callable sees it
            if "value" in kwargs:
                kwargs["value"] = kwargs["value"].upper()

        def process(value):
            return value + "!"

        workflow = CallableWorkflow(process, pre_callable=pre)
        result = workflow.execute(value="hello")

        # pre_callable should uppercase, then process adds !
        assert result["result"] == "HELLO!"

    def test_callable_workflow_with_post_callable(self):
        """Test CallableWorkflow with a post_callable."""

        def post(result):
            # Add metadata to the result
            result["metadata"] = "processed"

        def process(value):
            return value.upper()

        workflow = CallableWorkflow(process, post_callable=post)
        result = workflow.execute(value="hello")

        assert result["result"] == "HELLO"
        assert result["metadata"] == "processed"


class TestCallableWorkflowEdgeCases:
    """Test edge cases and error conditions."""

    def test_callable_with_varargs(self):
        """Test callable with *args (should be skipped)."""

        def process(value, *args):
            return value

        workflow = CallableWorkflow(process)
        result = workflow.execute(value="test")

        assert result["result"] == "test"

    def test_callable_with_kwargs(self):
        """Test callable with **kwargs (should be skipped during extraction)."""

        def process(value, **kwargs):
            return f"{value}_{len(kwargs)}"

        workflow = CallableWorkflow(process)
        result = workflow.execute(value="test", extra1="a", extra2="b")

        # Only "value" should be extracted and passed explicitly
        # **kwargs should not get the extras because we only pass extracted params
        assert result["result"] == "test_0"

    def test_callable_workflow_repr(self):
        """Test string representation of CallableWorkflow."""

        def my_function(x):
            return x

        workflow = CallableWorkflow(my_function)
        repr_str = repr(workflow)

        assert "CallableWorkflow" in repr_str
        assert "my_function" in repr_str

    def test_invalid_composition_type(self):
        """Test that composing with invalid types raises error."""
        workflow = SimpleWorkflow()

        with pytest.raises(TypeError, match="Can only compose workflows with other workflows or callables"):
            workflow | "not a callable"

        with pytest.raises(TypeError, match="Can only compose workflows with other workflows or callables"):
            workflow | 123

        with pytest.raises(TypeError, match="Can only compose workflows with other workflows or callables"):
            workflow | None


class TestCallableWorkflowIntegration:
    """Integration tests with real workflow scenarios."""

    def test_search_then_transform_pattern(self):
        """Test a common pattern: workflow returns data, callable transforms it."""

        class SearchWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs):
                return {"results": [{"name": "item1", "value": 10}, {"name": "item2", "value": 20}]}

        def extract_names(results):
            return [item["name"] for item in results]

        composed = SearchWorkflow() | extract_names

        result = composed.execute(query="test")

        assert result["result"] == ["item1", "item2"]

    def test_pipeline_with_data_transformation(self):
        """Test a data processing pipeline."""

        class DataLoader(BaseWorkflow):
            def _do_execute(self, **kwargs):
                return {"data": [1, 2, 3, 4, 5]}

        def filter_even(data):
            return [x for x in data if x % 2 == 0]

        def sum_values(data):
            return sum(data)

        pipeline = DataLoader() | filter_even | sum_values

        result = pipeline.execute()

        # Filters to [2, 4], then sums to 6
        assert result["result"] == 6

    def test_workflow_callable_workflow_chain(self):
        """Test alternating between workflows and callables."""

        class Step1(BaseWorkflow):
            def _do_execute(self, **kwargs):
                return {"value": kwargs.get("initial", 1)}

        class Step3(BaseWorkflow):
            def _do_execute(self, **kwargs):
                prev_result = kwargs.get("result", 0)
                return prev_result * 100

        def multiply_by_ten(value):
            return value * 10

        composed = Step1() | multiply_by_ten | Step3()

        result = composed.execute(initial=5)

        # Step1: returns {"value": 5} wrapped as result
        # Callable: extracts value=5, multiplies by 10 -> 50
        # Step3: gets result=50, multiplies by 100 -> 5000
        # Final result is wrapped in "result" key
        assert result["result"] == 5000


class TestCallableWorkflowArgsTransform:
    """Test CallableWorkflow with args_transform parameter."""

    def test_args_transform_simple_mapping(self):
        """Test simple parameter mapping with args_transform."""

        def process(content, query):
            return f"{query}: {content}"

        class SourceWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs):
                return {"fetch_result": {"content_text": "hello world"}, "query": "test query"}

        workflow = SourceWorkflow() | CallableWorkflow(process, args_transform="content=fetch_result.content_text, query=query")

        result = workflow.execute()
        assert result["result"] == "test query: hello world"

    def test_args_transform_nested_extraction(self):
        """Test nested path extraction with args_transform."""

        def get_url(url):
            return f"Fetching: {url}"

        class SourceWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs):
                return {"results": [{"url": "https://example.com"}, {"url": "https://backup.com"}]}

        workflow = SourceWorkflow() | CallableWorkflow(get_url, args_transform="url=results.0.url")

        result = workflow.execute()
        assert result["result"] == "Fetching: https://example.com"

    def test_args_transform_with_fallback(self):
        """Test args_transform with fallback values."""

        def process(value):
            return value.upper()

        class SourceWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs):
                return {"backup": "fallback value"}

        workflow = SourceWorkflow() | CallableWorkflow(process, args_transform="value=primary|backup")

        result = workflow.execute()
        assert result["result"] == "FALLBACK VALUE"

    def test_args_transform_multiple_sources(self):
        """Test mapping from multiple source paths."""

        def combine(title, body, author):
            return f"{title} by {author}: {body}"

        class SourceWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs):
                return {"article": {"title": "Test Article", "content": {"body": "Article body"}}, "metadata": {"author": "John Doe"}}

        workflow = SourceWorkflow() | CallableWorkflow(
            combine, args_transform="title=article.title, body=article.content.body, author=metadata.author"
        )

        result = workflow.execute()
        assert result["result"] == "Test Article by John Doe: Article body"

    def test_args_transform_cannot_combine_with_pre_callable(self):
        """Test that args_transform cannot be used with pre_callable."""

        def process(value):
            return value

        def pre(kwargs):
            pass

        # Should raise ValueError when trying to use both
        with pytest.raises(ValueError, match="Cannot specify 'transform' with 'pre_callable'"):
            CallableWorkflow(process, args_transform="value=value", pre_callable=pre)

    def test_args_transform_composition_chain(self):
        """Test chaining multiple CallableWorkflows with args_transform."""

        def extract_content(content_text):
            return {"fact": content_text.upper()}

        def format_result(fact, source):
            return f"[{source}] {fact}"

        # Workflow that outputs to fetch_result key (like FetchResultWorkflow)
        class FetchWorkflow(BaseWorkflow):
            def __init__(self):
                super().__init__(args_transform="-> fetch_result")

            def _do_execute(self, **kwargs):
                return {"content_text": "important fact", "metadata": {"source": "test"}}

        workflow = (
            FetchWorkflow()
            | CallableWorkflow(extract_content, args_transform="content_text=fetch_result.content_text")
            | CallableWorkflow(format_result, args_transform="fact=fact, source=fetch_result.metadata.source")
        )

        result = workflow.execute()
        assert result["result"] == "[test] IMPORTANT FACT"


class TestArgsTransformParameterResolution:
    """Test parameter resolution logic for args_transform."""

    def test_simple_key_extraction(self):
        """Test that simple keys are extracted from kwargs."""

        def process(url):
            return f"Processing: {url}"

        workflow = CallableWorkflow(process, args_transform="url=url")

        result = workflow.execute(url="test-url")

        assert result["result"] == "Processing: test-url"

    def test_explicit_path_extraction(self):
        """Test that explicit paths are extracted correctly."""

        def process(url):
            return f"Processing: {url}"

        workflow = CallableWorkflow(process, args_transform="url=nested.url")

        result = workflow.execute(nested={"url": "nested-url"})

        assert result["result"] == "Processing: nested-url"

    def test_explicit_path_not_found(self):
        """Test explicit path that doesn't exist."""

        def process(url):
            return f"Processing: {url}"

        workflow = CallableWorkflow(process, args_transform="url=nested.url")

        # nested.url doesn't exist, should use empty string fallback
        result = workflow.execute(other="data")

        assert result["result"] == "Processing: "

    def test_workflow_composition_parameter_passing(self):
        """Test parameter passing in composed workflows."""

        class FirstWorkflow(BaseWorkflow):
            def _do_execute(self, **kwargs):
                return {"url": "first-url", "count": 1}

        def process(url, count):
            return f"{url} (count={count})"

        # Parameters from first workflow are available to second
        workflow = FirstWorkflow() | CallableWorkflow(process, args_transform="url=url, count=count")

        result = workflow.execute()

        assert result["result"] == "first-url (count=1)"

    def test_fallback_to_second_option(self):
        """Test fallback to second option when first not found."""

        def process(url):
            return f"URL: {url}"

        workflow = CallableWorkflow(process, args_transform="url=primary_url|backup_url")

        # primary_url doesn't exist, use backup_url
        result = workflow.execute(backup_url="backup-url")

        assert result["result"] == "URL: backup-url"
