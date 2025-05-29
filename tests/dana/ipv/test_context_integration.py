"""
Test integration of context analysis with IPVReason executor.
"""

from unittest.mock import Mock, patch

from opendxa.dana.ipv.context_analyzer import CodeContext
from opendxa.dana.ipv.executor import IPVReason


class TestContextIntegration:
    """Test integration of context analysis with IPVReason executor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ipv_reason = IPVReason()

    def test_llm_driven_analysis_without_context(self):
        """Test that IPVReason uses LLM for analysis when no code context is available."""
        context = Mock()
        context.get_assignment_target_type.return_value = None

        # Mock the LLM call to return a simple response
        with patch.object(self.ipv_reason, "_execute_llm_call", return_value="Test response"):
            result = self.ipv_reason.execute("What is the capital of France?", context=context, use_mock=True)

        assert result == "Test response"

    def test_llm_receives_type_context(self):
        """Test that the LLM receives proper type context information."""
        context = Mock()
        context.get_assignment_target_type.return_value = float

        # Capture the enhanced prompt that gets sent to the LLM
        captured_prompt = ""

        def capture_llm_call(prompt, *args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "42.5"

        with patch.object(self.ipv_reason, "_execute_llm_call", side_effect=capture_llm_call):
            result = self.ipv_reason.execute("Extract the price", context=context, use_mock=True)

        # Verify the prompt was enhanced with type information (using new format)
        assert captured_prompt is not None
        assert "Expected output type: <class 'float'>" in captured_prompt
        assert "Extract the price" in captured_prompt

    def test_llm_receives_code_context(self):
        """Test that the LLM receives code context when available."""
        # Create a context with code information
        context = Mock()
        context.get_assignment_target_type.return_value = str
        context._current_program = None
        context._state = {"local.customer_name": "John Doe"}

        captured_prompt = ""

        def capture_llm_call(prompt, *args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "Customer analysis complete"

        with patch.object(self.ipv_reason, "_execute_llm_call", side_effect=capture_llm_call):
            result = self.ipv_reason.execute("Analyze customer data", context=context, use_mock=True)

        # Verify the prompt includes variable context
        assert captured_prompt is not None
        assert "Variables in scope: customer_name" in captured_prompt
        assert "Analyze customer data" in captured_prompt

    def test_type_hint_optimization(self):
        """Test that type hints provide optimization hints to the LLM."""
        context = Mock()
        context.get_assignment_target_type.return_value = float
        context._current_program = None
        context._state = {}

        # Create code context with type hints
        code_context = CodeContext()
        code_context.type_hints = {"price": "float", "quantity": "int"}

        captured_prompt = ""

        def capture_llm_call(prompt, *args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "25.99"

        with patch("opendxa.dana.ipv.context_analyzer.CodeContextAnalyzer.analyze_context", return_value=code_context):
            with patch.object(self.ipv_reason, "_execute_llm_call", side_effect=capture_llm_call):
                result = self.ipv_reason.execute("Get the total cost", context=context, use_mock=True)

        # Verify type hints are included
        assert captured_prompt is not None
        assert "Variable type hints: price: float, quantity: int" in captured_prompt

    def test_context_summary_logging(self):
        """Test that context analysis is properly logged."""
        context = Mock()
        context.get_assignment_target_type.return_value = None
        context._current_program = None
        context._state = {}

        # Create code context with comments
        code_context = CodeContext()
        code_context.comments = ["Calculate financial metrics", "Use precise arithmetic"]

        with patch("opendxa.dana.ipv.context_analyzer.CodeContextAnalyzer.analyze_context", return_value=code_context):
            with patch.object(self.ipv_reason, "_execute_llm_call", return_value="Analysis complete"):
                with patch.object(self.ipv_reason, "_log_debug") as mock_log:
                    result = self.ipv_reason.execute("Analyze the data", context=context, use_mock=True)

        # Check that context was logged
        log_calls = [call[0][0] for call in mock_log.call_args_list]
        assert any("Code context extracted" in call for call in log_calls)

    def test_llm_format_includes_analysis_request(self):
        """Test that LLM prompt includes request for domain and task analysis."""
        context = Mock()
        context.get_assignment_target_type.return_value = None
        context._current_program = None
        context._state = {}

        # Create code context with comments
        code_context = CodeContext()
        code_context.comments = ["Process financial data"]

        captured_prompt = ""

        def capture_llm_call(prompt, *args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "Financial analysis complete"

        with patch("opendxa.dana.ipv.context_analyzer.CodeContextAnalyzer.analyze_context", return_value=code_context):
            with patch.object(self.ipv_reason, "_execute_llm_call", side_effect=capture_llm_call):
                result = self.ipv_reason.execute("Calculate total revenue", context=context, use_mock=True)

        # Verify the LLM is asked to analyze domain and task type
        assert captured_prompt is not None
        assert "Determine the most appropriate domain" in captured_prompt
        assert "Identify the task type" in captured_prompt
        assert "financial, medical, legal, technical, business, data, creative, or general" in captured_prompt

    def test_fallback_without_context_analyzer(self):
        """Test that IPVReason works even if CodeContextAnalyzer is not available."""
        context = Mock()
        context.get_assignment_target_type.return_value = str

        # Mock ImportError to simulate CodeContextAnalyzer not being available
        with patch("opendxa.dana.ipv.context_analyzer.CodeContextAnalyzer", side_effect=ImportError("Module not found")):
            with patch.object(self.ipv_reason, "_execute_llm_call", return_value="Fallback response"):
                result = self.ipv_reason.execute("Simple request", context=context, use_mock=True)

        assert result == "Fallback response"
