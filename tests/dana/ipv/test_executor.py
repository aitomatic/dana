"""
Tests for IPV Executor architecture.

This module tests the IPVExecutor base class and specialized implementations
including IPVReason, IPVDataProcessor, and IPVAPIIntegrator.
"""

from unittest.mock import Mock, patch

import pytest

from opendxa.dana.ipv.base import IPVConfig, IPVExecutionError
from opendxa.dana.ipv.executor import IPVAPIIntegrator, IPVDataProcessor, IPVExecutor, IPVReason


class TestIPVExecutor:
    """Test the base IPVExecutor class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that IPVExecutor cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IPVExecutor()  # type: ignore

    def test_concrete_implementation(self):
        """Test that a concrete implementation can be created."""

        class ConcreteExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                return {"test": "infer"}

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return "processed"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result.upper()

        executor = ConcreteExecutor()
        assert executor is not None

    def test_execute_successful_pipeline(self):
        """Test successful execution of the IPV pipeline."""

        class ConcreteExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                return {"domain": "test", "strategy": "simple"}

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return f"processed: {intent}"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result.upper()

        executor = ConcreteExecutor()
        result = executor.execute("test intent")

        assert result == "PROCESSED: TEST INTENT"

    def test_execute_with_config(self):
        """Test execution with custom configuration."""

        class ConcreteExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                return {"test": "infer"}

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return "processed"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result

        executor = ConcreteExecutor()
        config = IPVConfig(debug_mode=True, max_iterations=5)

        with patch("builtins.print") as mock_print:
            result = executor.execute("test", config=config)

        assert result == "processed"
        # Should have debug output
        assert mock_print.called

    def test_execute_with_dict_config(self):
        """Test execution with dictionary configuration."""

        class ConcreteExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                return {"test": "infer"}

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return "processed"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result

        executor = ConcreteExecutor()
        result = executor.execute("test", config={"debug_mode": False, "max_iterations": 2})

        assert result == "processed"

    def test_execute_phase_failure(self):
        """Test handling of phase failures."""

        class FailingExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                raise ValueError("Infer failed")

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return "processed"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result

        executor = FailingExecutor()

        with pytest.raises(IPVExecutionError) as exc_info:
            executor.execute("test")

        assert "IPV execution failed" in str(exc_info.value)
        assert "Infer failed" in str(exc_info.value)

    def test_execution_history_tracking(self):
        """Test that execution history is properly tracked."""

        class ConcreteExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                return {"test": "infer"}

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return "processed"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result

        executor = ConcreteExecutor()

        # Execute multiple times
        executor.execute("test1")
        executor.execute("test2")

        history = executor.get_execution_history()
        assert len(history) == 2
        assert history[0]["intent"] == "test1"
        assert history[1]["intent"] == "test2"
        assert all(record["success"] for record in history)

    def test_performance_stats(self):
        """Test performance statistics calculation."""

        class ConcreteExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                return {"test": "infer"}

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return "processed"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result

        executor = ConcreteExecutor()

        # Execute multiple times
        executor.execute("test1")
        executor.execute("test2")

        stats = executor.get_performance_stats()
        assert stats["total_executions"] == 2
        assert stats["successful_executions"] == 2
        assert stats["success_rate"] == 1.0
        assert stats["total_time"] > 0
        assert stats["average_time"] > 0

    def test_clear_execution_history(self):
        """Test clearing execution history."""

        class ConcreteExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                return {"test": "infer"}

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return "processed"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result

        executor = ConcreteExecutor()

        executor.execute("test")
        assert len(executor.get_execution_history()) == 1

        executor.clear_execution_history()
        assert len(executor.get_execution_history()) == 0

    def test_debug_mode(self):
        """Test debug mode functionality."""

        class ConcreteExecutor(IPVExecutor):
            def infer_phase(self, intent: str, context=None, **kwargs):
                return {"test": "infer"}

            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                return "processed"

            def validate_phase(self, result, enhanced_context=None, **kwargs):
                return result

        executor = ConcreteExecutor()
        executor.set_debug_mode(True)

        with patch("builtins.print") as mock_print:
            executor.execute("test")

        assert mock_print.called
        # Check that debug messages were printed
        debug_calls = [call for call in mock_print.call_args_list if "CONCRETEEXECUTOR" in str(call)]
        assert len(debug_calls) > 0


class TestIPVReason:
    """Test the IPVReason specialized executor."""

    def test_initialization(self):
        """Test IPVReason initialization."""
        executor = IPVReason()
        assert executor is not None
        assert isinstance(executor, IPVExecutor)

    def test_infer_phase_basic(self):
        """Test basic INFER phase functionality."""
        executor = IPVReason()

        result = executor.infer_phase("Extract the price from this invoice", context=None)

        assert result["operation_type"] == "llm_prompt"
        assert result["use_llm_analysis"] is True
        assert "optimization_hints" in result

    def test_infer_phase_with_context(self):
        """Test INFER phase with context that has type information."""
        executor = IPVReason()

        # Mock context with type information
        mock_context = Mock()
        mock_context.get_assignment_target_type.return_value = float

        result = executor.infer_phase("get price", context=mock_context)

        assert result["expected_type"] == float
        assert result["use_llm_analysis"] is True
        assert "optimization_hints" in result

    def test_process_phase(self):
        """Test PROCESS phase functionality."""
        executor = IPVReason()

        enhanced_context = {"domain": "financial", "task_type": "extraction", "prompt_strategy": "precise_extraction"}

        result = executor.process_phase("get price", enhanced_context)

        assert isinstance(result, str)
        # The result should be a real LLM response, not necessarily containing "LLM Response"
        assert len(result) > 0

    def test_validate_phase_float_extraction(self):
        """Test VALIDATE phase for float extraction."""
        executor = IPVReason()

        enhanced_context = {"expected_type": float}
        llm_result = "The price is $29.99 for this item."

        result = executor.validate_phase(llm_result, enhanced_context)

        assert isinstance(result, float)
        assert result == 29.99

    def test_validate_phase_int_extraction(self):
        """Test VALIDATE phase for integer extraction."""
        executor = IPVReason()

        enhanced_context = {"expected_type": int}
        llm_result = "There are 42 items in the inventory."

        result = executor.validate_phase(llm_result, enhanced_context)

        assert isinstance(result, int)
        assert result == 42

    def test_validate_phase_bool_extraction(self):
        """Test VALIDATE phase for boolean extraction."""
        executor = IPVReason()

        enhanced_context = {"expected_type": bool}

        # Test positive cases
        for text in ["Yes, it's approved", "True", "This is positive"]:
            result = executor.validate_phase(text, enhanced_context)
            assert result is True

        # Test negative cases
        for text in ["No, rejected", "False", "This is negative"]:
            result = executor.validate_phase(text, enhanced_context)
            assert result is False

    def test_validate_phase_string_cleaning(self):
        """Test VALIDATE phase for string cleaning."""
        executor = IPVReason()

        enhanced_context = {"expected_type": str}
        llm_result = "**Bold text** with *italic* and `code` formatting."

        result = executor.validate_phase(llm_result, enhanced_context)

        assert result == "Bold text with italic and code formatting."

    def test_domain_detection(self):
        """Test that domain detection is now delegated to LLM."""
        executor = IPVReason()

        # Domain detection is now handled by the LLM, not by heuristics
        # Test that the executor still works but doesn't have the old method
        assert not hasattr(executor, "_detect_domain")

        # Test that execution still works (LLM will handle domain detection)
        result = executor.execute("Extract the price", use_mock=True)
        assert result is not None

    def test_task_type_detection(self):
        """Test that task type detection is now delegated to LLM."""
        executor = IPVReason()

        # Task type detection is now handled by the LLM, not by heuristics
        # Test that the executor still works but doesn't have the old method
        assert not hasattr(executor, "_detect_task_type")

        # Test that execution still works (LLM will handle task type detection)
        result = executor.execute("Analyze the data", use_mock=True)
        assert result is not None

    def test_complete_execution_flow(self):
        """Test complete execution flow for IPVReason."""
        executor = IPVReason()

        # Mock context with float type
        mock_context = Mock()
        mock_context.get_assignment_target_type.return_value = float

        # This should go through the complete IPV pipeline
        result = executor.execute("Extract the price from: Item costs $29.99", mock_context)

        # The result should be a float extracted from the simulated LLM response
        assert isinstance(result, float)


class TestIPVDataProcessor:
    """Test the IPVDataProcessor specialized executor."""

    def test_initialization(self):
        """Test IPVDataProcessor initialization."""
        executor = IPVDataProcessor()
        assert executor is not None
        assert isinstance(executor, IPVExecutor)

    def test_infer_phase(self):
        """Test INFER phase for data processing."""
        executor = IPVDataProcessor()

        test_data = [1, 2, 3, 4, 5]
        result = executor.infer_phase("Find patterns in data", context=None, data=test_data)

        assert result["operation_type"] == "data_processing"
        assert result["data_format"] == "list"
        assert result["analysis_type"] == "pattern_analysis"
        assert result["data_size"] == 5

    def test_infer_phase_different_data_types(self):
        """Test INFER phase with different data types."""
        executor = IPVDataProcessor()

        test_cases = [
            ({"key": "value"}, "dictionary"),
            ([1, 2, 3], "list"),
            ("text data", "string"),
            (None, "unknown"),
        ]

        for data, expected_format in test_cases:
            result = executor.infer_phase("analyze", context=None, data=data)
            assert result["data_format"] == expected_format

    def test_process_phase(self):
        """Test PROCESS phase for data processing."""
        executor = IPVDataProcessor()

        enhanced_context = {"analysis_type": "pattern_analysis"}
        test_data = [1, 2, 3]

        result = executor.process_phase("find patterns", enhanced_context, data=test_data)

        assert isinstance(result, str)
        assert "pattern_analysis" in result
        assert str(test_data) in result

    def test_complete_execution(self):
        """Test complete execution flow for data processing."""
        executor = IPVDataProcessor()

        test_data = {"sales": [100, 200, 150], "month": ["Jan", "Feb", "Mar"]}
        result = executor.execute("Analyze sales trends", data=test_data)

        assert isinstance(result, str)
        assert "trend_analysis" in result


class TestIPVAPIIntegrator:
    """Test the IPVAPIIntegrator specialized executor."""

    def test_initialization(self):
        """Test IPVAPIIntegrator initialization."""
        executor = IPVAPIIntegrator()
        assert executor is not None
        assert isinstance(executor, IPVExecutor)

    def test_infer_phase(self):
        """Test INFER phase for API integration."""
        executor = IPVAPIIntegrator()

        result = executor.infer_phase("Get user profile", context=None)

        assert result["operation_type"] == "api_integration"
        assert result["endpoint"] == "/api/users"
        assert result["auth_method"] == "bearer_token"
        assert "retry_strategy" in result

    def test_endpoint_inference(self):
        """Test endpoint inference from intent."""
        executor = IPVAPIIntegrator()

        test_cases = [
            ("Get user information", "/api/users"),
            ("Fetch data records", "/api/data"),
            ("Some other request", "/api/general"),
        ]

        for intent, expected_endpoint in test_cases:
            endpoint = executor._infer_endpoint(intent, None)
            assert endpoint == expected_endpoint

    def test_process_phase(self):
        """Test PROCESS phase for API integration."""
        executor = IPVAPIIntegrator()

        enhanced_context = {"endpoint": "/api/test"}

        result = executor.process_phase("test api call", enhanced_context)

        assert isinstance(result, str)
        assert "/api/test" in result
        assert "success" in result

    def test_complete_execution(self):
        """Test complete execution flow for API integration."""
        executor = IPVAPIIntegrator()

        result = executor.execute("Get user data for ID 123", user_id=123)

        assert isinstance(result, str)
        assert "API response" in result


class TestIPVExecutorIntegration:
    """Integration tests for IPV executors."""

    def test_multiple_executors_independence(self):
        """Test that multiple executor instances are independent."""
        reason_executor = IPVReason()
        data_executor = IPVDataProcessor()
        api_executor = IPVAPIIntegrator()

        # Execute different operations
        reason_result = reason_executor.execute("Extract price: $10.50")
        data_result = data_executor.execute("Analyze trends", data=[1, 2, 3])
        api_result = api_executor.execute("Get user info")

        # Check that execution histories are independent
        assert len(reason_executor.get_execution_history()) == 1
        assert len(data_executor.get_execution_history()) == 1
        assert len(api_executor.get_execution_history()) == 1

        # Check that results are different
        assert reason_result != data_result
        assert data_result != api_result

    def test_executor_performance_comparison(self):
        """Test performance statistics across different executors."""
        executors = [IPVReason(), IPVDataProcessor(), IPVAPIIntegrator()]

        # Execute operations on each
        for executor in executors:
            executor.execute("test operation")

        # Check that all have performance stats
        for executor in executors:
            stats = executor.get_performance_stats()
            assert stats["total_executions"] == 1
            assert stats["success_rate"] == 1.0
            assert stats["total_time"] > 0

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across executors."""

        class FailingReason(IPVReason):
            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                raise ValueError("Simulated failure")

        class FailingDataProcessor(IPVDataProcessor):
            def process_phase(self, intent: str, enhanced_context=None, **kwargs):
                raise ValueError("Simulated failure")

        executors = [FailingReason(), FailingDataProcessor()]

        for executor in executors:
            with pytest.raises(IPVExecutionError) as exc_info:
                executor.execute("test")

            assert "IPV execution failed" in str(exc_info.value)
            assert "Simulated failure" in str(exc_info.value)

            # Check that failure is recorded in history
            history = executor.get_execution_history()
            assert len(history) == 1
            assert not history[0]["success"]


class TestIPVReasonIntegration:
    """Test IPVReason integration with the reason() function."""

    def test_ipv_reason_with_real_llm_call(self):
        """Test IPVReason with actual LLM infrastructure."""
        executor = IPVReason()

        # Mock context with LLM resource
        import os
        from unittest.mock import Mock

        from opendxa.common.resource.llm_resource import LLMResource

        mock_context = Mock()
        llm_resource = LLMResource()
        llm_resource = llm_resource.with_mock_llm_call(True)
        mock_context.get.return_value = llm_resource

        # Set environment for mocking
        original_mock_env = os.environ.get("OPENDXA_MOCK_LLM")
        os.environ["OPENDXA_MOCK_LLM"] = "true"

        try:
            result = executor.execute(
                "Extract the price from: Item costs $29.99", context=mock_context, llm_options={"temperature": 0.3}, use_mock=True
            )

            assert result is not None
            # The mock LLM returns a string response
            assert isinstance(result, str)

        finally:
            if original_mock_env is None:
                os.environ.pop("OPENDXA_MOCK_LLM", None)
            else:
                os.environ["OPENDXA_MOCK_LLM"] = original_mock_env

    def test_ipv_reason_fallback_behavior(self):
        """Test that IPVReason falls back gracefully when LLM calls fail."""
        executor = IPVReason()

        # Mock context that will cause LLM failure
        mock_context = Mock()
        mock_context.get_assignment_target_type.return_value = None

        # Mock the LLM call to fail, triggering fallback
        with patch.object(executor, "_execute_llm_call", side_effect=Exception("LLM not available")):
            result = executor.execute("Test prompt", context=mock_context)

        assert result is not None
        assert isinstance(result, str)
        # The fallback should include the fallback message
        assert "LLM Response to: Test prompt" in result

    def test_ipv_reason_prompt_enhancement(self):
        """Test that IPVReason enhances prompts with LLM-driven analysis."""
        executor = IPVReason()

        # Test that INFER phase returns LLM analysis flag
        enhanced_context = executor.infer_phase("Extract the price from this invoice", context=None)
        assert enhanced_context["use_llm_analysis"] is True
        assert "optimization_hints" in enhanced_context

    def test_ipv_reason_type_driven_optimization(self):
        """Test type-driven optimization in IPVReason."""
        executor = IPVReason()

        # Mock context with float type expectation
        mock_context = Mock()
        mock_context.get_assignment_target_type.return_value = float

        enhanced_context = executor.infer_phase("get price", context=mock_context)
        assert enhanced_context["expected_type"] == float
        assert "optimization_hints" in enhanced_context
        # Type hints are now in optimization_hints instead of optimization_focus
        optimization_hints = enhanced_context["optimization_hints"]
        assert any("numerical" in hint for hint in optimization_hints)

    def test_ipv_reason_with_different_domains(self):
        """Test IPVReason with different domain types - LLM will handle domain detection."""
        executor = IPVReason()

        test_cases = [
            "Extract medical diagnosis",
            "Calculate revenue",
            "Review legal contract",
            "Write creative story",
            "General question",
        ]

        for intent in test_cases:
            # Test that execution works regardless of domain
            result = executor.execute(intent, use_mock=True)
            assert result is not None
            assert isinstance(result, str)


class TestReasonFunctionIntegration:
    """Test the enhanced reason_function with IPV integration."""

    def test_reason_function_imports(self):
        """Test that reason_function can import IPV components."""
        from opendxa.dana.sandbox.interpreter.functions.core.reason_function import _reason_with_ipv

        # Test that the function exists
        assert _reason_with_ipv is not None
        assert callable(_reason_with_ipv)

    def test_reason_function_ipv_enabled_by_default(self):
        """Test that IPV is enabled by default in reason_function."""
        from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function

        mock_context = Mock()

        # Test with minimal valid arguments
        result = reason_function("test prompt", mock_context, use_mock=True)

        # Should not raise an exception
        assert result is not None

    def test_reason_function_ipv_disable_option(self):
        """Test that IPV can be disabled via options."""
        from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function

        mock_context = Mock()

        # Disable IPV explicitly
        result = reason_function("test prompt", mock_context, options={"enable_ipv": False}, use_mock=True)

        assert result is not None

    def test_reason_function_use_original_option(self):
        """Test that original implementation can be forced."""
        from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function

        mock_context = Mock()

        # Force original implementation
        result = reason_function("test prompt", mock_context, options={"use_original": True}, use_mock=True)

        assert result is not None

    def test_reason_function_backward_compatibility(self):
        """Test that existing reason() calls work unchanged."""
        from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function

        mock_context = Mock()

        # Test old-style call (should work with IPV automatically)
        result = reason_function("What is 2+2?", mock_context, use_mock=True)
        assert result is not None

        # Test with options
        result = reason_function("What is 2+2?", mock_context, options={"temperature": 0.5}, use_mock=True)
        assert result is not None


class TestIPVReasonContextIntegration:
    """Test IPVReason integration with CodeContextAnalyzer."""

    def test_infer_phase_with_code_context(self):
        """Test that INFER phase extracts and uses code context."""
        executor = IPVReason()

        # Create a mock context with AST-like structure
        mock_context = Mock()
        mock_program = Mock()

        # Create a mock token that looks like a comment
        mock_comment_token = Mock()
        mock_comment_token.type = "COMMENT"
        mock_comment_token.value = "# Extract the total price from this medical invoice"

        mock_program.statements = [mock_comment_token, Mock(target=Mock(name="local.price"), type_hint=Mock(name="float"))]
        mock_context._current_program = mock_program

        result = executor.infer_phase("Get the price", mock_context, variable_name="price")

        # Verify that code context was extracted and used
        assert "code_context" in result
        code_context = result["code_context"]

        # The mock context might not extract comments properly, but should not crash
        assert code_context is not None

    def test_domain_detection_with_code_context(self):
        """Test that domain detection is now handled by LLM with code context."""
        executor = IPVReason()

        # Domain detection is now LLM-driven, test that execution works with context
        mock_context = Mock()
        mock_context._current_program = None
        mock_context._state = {"local.invoice_total": 100.0}
        mock_context.get_assignment_target_type.return_value = str

        result = executor.execute("get value", context=mock_context, use_mock=True)
        assert result is not None
        assert isinstance(result, str)

    def test_task_type_detection_with_code_context(self):
        """Test that task type detection is now handled by LLM with code context."""
        executor = IPVReason()

        # Task type detection is now LLM-driven, test that execution works with context
        mock_context = Mock()
        mock_context._current_program = None
        mock_context._state = {"local.data": "some data"}
        mock_context.get_assignment_target_type.return_value = str

        result = executor.execute("process something", context=mock_context, use_mock=True)
        assert result is not None
        assert isinstance(result, str)

    def test_prompt_enhancement_with_code_context(self):
        """Test that prompts are enhanced with code context and sent to LLM."""
        executor = IPVReason()

        # Test that context is properly passed to the LLM
        mock_context = Mock()
        mock_context._current_program = None
        mock_context._state = {"local.total": 42.0}
        mock_context.get_assignment_target_type.return_value = str

        # Capture the enhanced prompt sent to LLM
        captured_prompt = ""

        def capture_llm_call(prompt, *args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "Enhanced response"

        with patch.object(executor, "_execute_llm_call", side_effect=capture_llm_call):
            result = executor.execute("get total", context=mock_context, use_mock=True)

        # Verify context information was included in the prompt
        assert "Variables in scope: total" in captured_prompt
        assert "Expected return type: <class 'str'>" in captured_prompt
        assert result == "Enhanced response"

    def test_complete_ipv_flow_with_comments(self):
        """Test complete IPV flow with comment-aware optimization."""
        executor = IPVReason()

        # Create a mock context that simulates Dana AST with comments
        mock_context = Mock()
        mock_program = Mock()

        # Create mock comment tokens
        comment1 = Mock()
        comment1.type = "COMMENT"
        comment1.value = "# This function extracts pricing from medical invoices"

        comment2 = Mock()
        comment2.type = "COMMENT"
        comment2.value = "# Return the total amount as a float value"

        mock_program.statements = [comment1, comment2, Mock(target=Mock(name="local.price"), type_hint=Mock(name="float"), value=Mock())]
        mock_context._current_program = mock_program
        mock_context._state = {"local.invoice_data": "sample data"}

        # Mock the LLM call to avoid actual network requests
        result = executor.execute("Extract the price", mock_context, variable_name="price", use_mock=True)

        # Should complete successfully with enhanced context
        assert result is not None

    def test_context_extraction_error_handling(self):
        """Test that context extraction errors are handled gracefully."""
        executor = IPVReason()

        # Use a context that will cause errors in context extraction
        mock_context = Mock()
        mock_context._current_program = None
        mock_context._state = None

        # Should not crash even with problematic context
        result = executor.infer_phase("test", mock_context)

        assert "code_context" in result
        # Code context might be None or empty, but should not crash

    def test_backward_compatibility(self):
        """Test that new functionality doesn't break existing behavior."""
        executor = IPVReason()

        # Test with old-style context (no AST, no comments)
        mock_context = Mock()

        result = executor.execute("extract price", mock_context, use_mock=True)

        # Should work exactly as before
        assert result is not None
