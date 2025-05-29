"""
Test the CodeContextAnalyzer for IPV optimization.
"""

from unittest.mock import Mock, patch

from lark import Token

from opendxa.dana.ipv.context_analyzer import CodeContext, CodeContextAnalyzer


class TestCodeContext:
    """Test the CodeContext data container."""

    def test_initialization(self):
        """Test that CodeContext initializes with empty collections."""
        context = CodeContext()

        assert context.comments == []
        assert context.inline_comments == []
        assert context.variable_context == {}
        assert context.function_context is None
        assert context.type_hints == {}
        assert context.surrounding_code == []
        assert context.error_context == []

    def test_to_dict(self):
        """Test converting CodeContext to dictionary."""
        context = CodeContext()
        context.comments = ["test comment"]
        context.type_hints = {"var": "int"}

        result = context.to_dict()

        assert result["comments"] == ["test comment"]
        assert result["type_hints"] == {"var": "int"}
        assert "variable_context" in result

    def test_has_context_empty(self):
        """Test has_context returns False for empty context."""
        context = CodeContext()
        assert not context.has_context()

    def test_has_context_with_comments(self):
        """Test has_context returns True when comments are present."""
        context = CodeContext()
        context.comments = ["meaningful comment"]
        assert context.has_context()

    def test_has_context_with_type_hints(self):
        """Test has_context returns True when type hints are present."""
        context = CodeContext()
        context.type_hints = {"price": "float"}
        assert context.has_context()

    def test_get_context_summary_empty(self):
        """Test context summary for empty context."""
        context = CodeContext()
        summary = context.get_context_summary()
        assert summary == "No additional context available"

    def test_get_context_summary_with_content(self):
        """Test context summary with actual content."""
        context = CodeContext()
        context.comments = ["comment1", "comment2"]
        context.type_hints = {"price": "float", "name": "str"}
        context.surrounding_code = ["line1", "line2", "line3"]

        summary = context.get_context_summary()
        assert "2 code comments" in summary
        assert "Type hints: float, str" in summary
        assert "3 lines of surrounding code" in summary


class TestCodeContextAnalyzer:
    """Test the CodeContextAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CodeContextAnalyzer()

    def test_initialization(self):
        """Test that analyzer initializes properly."""
        assert self.analyzer is not None

    def test_analyze_context_no_context(self):
        """Test analyzing context when no meaningful context is available."""
        mock_context = Mock()
        mock_context._current_program = None
        mock_context._state = {}

        # Mock the frame inspection to prevent it from picking up test environment code
        with patch("inspect.currentframe", return_value=None):
            result = self.analyzer.analyze_context(mock_context)

        assert isinstance(result, CodeContext)
        assert not result.has_context()

    def test_analyze_context_with_variable_name(self):
        """Test analyzing context with a specific variable name."""
        mock_context = Mock()
        mock_context._current_program = None
        mock_context._state = {"local.test_var": "test_value"}

        with patch("inspect.currentframe", return_value=None):
            result = self.analyzer.analyze_context(mock_context, variable_name="test_var")

        assert isinstance(result, CodeContext)
        assert "test_var" in result.variable_context

    def test_extract_ast_context_with_comments(self):
        """Test extracting context from AST with comments."""
        # Create a mock program with comments
        mock_program = Mock()
        comment_token = Mock(spec=Token)
        comment_token.type = "COMMENT"
        comment_token.value = "# This is a test comment"

        mock_program.statements = [comment_token]

        mock_context = Mock()
        mock_context._current_program = mock_program
        mock_context._state = {}

        # Mock frame inspection to prevent interference
        with patch("inspect.currentframe", return_value=None):
            result = self.analyzer.analyze_context(mock_context)

        assert len(result.comments) == 1
        assert result.comments[0] == "This is a test comment"

    def test_extract_variable_context(self):
        """Test extracting variable context from execution state."""
        mock_context = Mock()
        mock_context._current_program = None
        mock_context._state = {"local.customer_name": "John Doe", "local.account_balance": 1000.50, "global.system_var": "system_value"}

        result = self.analyzer.analyze_context(mock_context)

        assert "customer_name" in result.variable_context
        assert "account_balance" in result.variable_context
        assert result.variable_context["customer_name"]["value_type"] == "str"
        assert result.variable_context["account_balance"]["value_type"] == "float"
        # Global variables should not be included
        assert "system_var" not in result.variable_context

    def test_format_context_for_llm_no_context(self):
        """Test LLM formatting when no context is available."""
        original_prompt = "What is the capital of France?"
        empty_context = CodeContext()

        result = self.analyzer.format_context_for_llm(original_prompt, empty_context)

        assert result == original_prompt

    def test_format_context_for_llm_with_type(self):
        """Test LLM formatting with expected type only."""
        original_prompt = "Extract the price"
        empty_context = CodeContext()

        result = self.analyzer.format_context_for_llm(original_prompt, empty_context, expected_type=float)

        # Updated to match the actual format (uses "Expected output type" not "Expected return type")
        assert "Expected output type: <class 'float'>" in result
        assert "Extract the price" in result

    def test_format_context_for_llm_with_full_context(self):
        """Test LLM formatting with rich context."""
        original_prompt = "Analyze the data"

        context = CodeContext()
        context.comments = ["Process financial data", "Use precise calculations"]
        context.type_hints = {"price": "float", "quantity": "int"}
        context.variable_context = {"customer_id": {"value_type": "str"}}
        context.surrounding_code = ["def calculate_total():", "    return price * quantity"]

        result = self.analyzer.format_context_for_llm(original_prompt, context, expected_type=dict)

        # Updated to match the actual format
        assert "Expected output type: <class 'dict'>" in result
        assert "Code comments: Process financial data | Use precise calculations" in result
        assert "Variable type hints: price: float, quantity: int" in result
        assert "Variables in scope: customer_id" in result
        assert "Surrounding code context:" in result
        assert "Determine the most appropriate domain" in result
        assert "Identify the task type" in result

    def test_get_optimization_hints_from_types(self):
        """Test getting optimization hints from type information."""
        context = CodeContext()
        context.type_hints = {"price": "float", "active": "bool"}

        # Test with float expected type
        hints = self.analyzer.get_optimization_hints_from_types(float, context)
        assert "numerical_precision" in hints
        assert "extract_numbers_only" in hints
        assert "numerical_context" in hints  # From type hints

        # Test with bool expected type
        hints = self.analyzer.get_optimization_hints_from_types(bool, context)
        assert "binary_decision" in hints
        assert "clear_yes_no" in hints
        assert "boolean_context" in hints  # From type hints

        # Test with dict expected type
        hints = self.analyzer.get_optimization_hints_from_types(dict, context)
        assert "structured_output" in hints
        assert "json_format" in hints

    def test_frame_context_extraction_error_handling(self):
        """Test that frame context extraction handles errors gracefully."""
        mock_context = Mock()
        mock_context._current_program = None
        mock_context._state = {}

        # This should not raise an exception even if frame inspection fails
        result = self.analyzer.analyze_context(mock_context)

        assert isinstance(result, CodeContext)

    def test_analyze_context_exception_handling(self):
        """Test that analyze_context handles exceptions gracefully."""
        # Create a context that will cause an exception
        mock_context = Mock()
        mock_context._current_program = Mock()
        mock_context._current_program.statements = None  # This should cause an AttributeError

        # Should not raise an exception
        result = self.analyzer.analyze_context(mock_context)

        assert isinstance(result, CodeContext)

    def test_type_hint_extraction_from_ast(self):
        """Test extracting type hints from AST statements."""
        mock_program = Mock()

        # Create a mock assignment statement with type hint
        mock_stmt = Mock()
        mock_stmt.target = Mock()
        mock_stmt.target.name = "local.price"
        mock_stmt.type_hint = Mock()
        mock_stmt.type_hint.name = "float"
        mock_stmt.value = Mock()

        mock_program.statements = [mock_stmt]

        mock_context = Mock()
        mock_context._current_program = mock_program
        mock_context._state = {}

        result = self.analyzer.analyze_context(mock_context)

        assert "price" in result.type_hints
        assert result.type_hints["price"] == "float"
        assert "price" in result.variable_context
