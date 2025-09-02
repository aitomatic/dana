"""
Tests for the RecursiveStrategy implementation.

This module tests the recursive strategy that implements LLM-driven problem solving
with rich context engineering integration.
"""

from dana.core.agent.context import EventHistory, ProblemContext
from dana.core.agent.strategy.recursive.recursive_strategy import RecursiveStrategy
from dana.core.workflow.workflow_system import WorkflowInstance


class TestRecursiveStrategy:
    """Test RecursiveStrategy functionality."""

    def test_create_strategy(self):
        """Test creating a recursive strategy instance."""
        strategy = RecursiveStrategy(max_depth=5)

        assert strategy.max_depth == 5
        assert strategy.computable_context is not None

    def test_can_handle_basic_problem(self):
        """Test that strategy can handle basic problems."""
        strategy = RecursiveStrategy(max_depth=5)

        context = ProblemContext(problem_statement="Test problem", objective="Solve test problem", original_problem="Test problem", depth=0)

        can_handle = strategy.can_handle("Simple problem", context)
        assert can_handle is True

    def test_can_handle_identical_problem(self):
        """Test that strategy detects identical problems."""
        strategy = RecursiveStrategy(max_depth=5)

        context = ProblemContext(problem_statement="Test problem", objective="Solve test problem", original_problem="Test problem", depth=0)

        # Try to handle the same problem
        can_handle = strategy.can_handle("Test problem", context)
        assert can_handle is False

    def test_depth_limit_checking(self):
        """Test that strategy respects depth limits."""
        strategy = RecursiveStrategy(max_depth=3)

        # Context at max depth
        context = ProblemContext(problem_statement="Deep problem", objective="Solve deep problem", original_problem="Deep problem", depth=3)

        can_handle = strategy.can_handle("Deep problem", context)
        assert can_handle is False

    def test_create_workflow_basic(self):
        """Test creating a basic workflow."""
        strategy = RecursiveStrategy(max_depth=5)

        context = ProblemContext(problem_statement="Test problem", objective="Solve test problem", original_problem="Test problem", depth=0)

        # Create mock agent instance
        mock_agent = type("MockAgent", (), {"llm": lambda self, request: "agent.output('test result')"})()

        workflow = strategy.create_workflow("Test problem", context, mock_agent)

        assert isinstance(workflow, WorkflowInstance)
        assert workflow.name.startswith("RecursiveWorkflow_")
        assert workflow.composed_function is not None

    def test_create_workflow_at_depth_limit(self):
        """Test creating workflow when depth limit is reached."""
        strategy = RecursiveStrategy(max_depth=2)

        context = ProblemContext(problem_statement="Deep problem", objective="Solve deep problem", original_problem="Deep problem", depth=2)

        # Create mock agent instance
        mock_agent = type("MockAgent", (), {"llm": lambda self, request: "agent.output('base case result')"})()

        workflow = strategy.create_workflow("Deep problem", context, mock_agent)

        assert isinstance(workflow, WorkflowInstance)
        assert "BaseCaseWorkflow" in str(workflow)

    def test_enhanced_prompt_generation(self):
        """Test enhanced LLM prompt generation with rich context."""
        strategy = RecursiveStrategy(max_depth=5)

        # Create context with workflow instance and action history
        action_history = EventHistory()
        context = ProblemContext(problem_statement="Test problem", objective="Solve test problem", original_problem="Test problem", depth=0)

        # Add workflow_instance attribute to context
        context.workflow_instance = type("MockWorkflow", (), {"_global_action_history": action_history, "_parent_workflow": None})()

        prompt = strategy._build_enhanced_analysis_prompt("Test problem", context)

        assert "Test problem" in prompt
        assert "Solve test problem" in prompt
        assert "DEPTH: 0" in prompt
        assert "AVAILABLE FUNCTIONS" in prompt
        assert "agent.output" in prompt
        assert "agent.solve" in prompt

    def test_basic_prompt_generation(self):
        """Test basic prompt generation when rich context is not available."""
        strategy = RecursiveStrategy(max_depth=5)

        context = ProblemContext(problem_statement="Test problem", objective="Solve test problem", original_problem="Test problem", depth=0)

        prompt = strategy._build_basic_prompt("Test problem", context)

        assert "Test problem" in prompt
        assert "Solve test problem" in prompt
        assert "DEPTH: 0" in prompt
        assert "AVAILABLE FUNCTIONS" in prompt
        assert "agent.output" in prompt
        assert "agent.solve" in prompt

    # Mock response method removed - now uses agent.llm() directly
    # def test_mock_llm_response_generation(self):
    #     """Test mock LLM response generation for testing."""
    #     strategy = RecursiveStrategy(max_depth=5)
    #
    #     # Test complex problem response
    #     complex_response = strategy._generate_mock_response("This is a complex problem that needs to be broken down")
    #     assert "agent.reason" in complex_response
    #     assert "agent.solve" in complex_response
    #     assert "agent.output" in complex_response
    #
    #     # Test simple problem response
    #     simple_response = strategy._generate_mock_response("Simple problem")
    #     assert "agent.reason" in simple_response
    #     assert "agent.output" in simple_response

    def test_dana_code_compilation(self):
        """Test Dana code compilation (mock implementation)."""
        strategy = RecursiveStrategy(max_depth=5)

        context = ProblemContext(problem_statement="Test problem", objective="Solve test problem", original_problem="Test problem", depth=0)

        dana_code = "agent.output('test result')"
        compiled_function = strategy._compile_dana_code(dana_code, context)

        # Should return a callable function
        assert callable(compiled_function)

        # Test execution
        result = compiled_function()
        # The function should return the actual content from agent.output()
        assert result == "test result"

    def test_workflow_instance_creation(self):
        """Test creating workflow instances with proper state."""
        strategy = RecursiveStrategy(max_depth=5)

        context = ProblemContext(problem_statement="Test problem", objective="Solve test problem", original_problem="Test problem", depth=0)

        # Mock compiled function
        def mock_function(*args, **kwargs):
            return "mock result"

        workflow = strategy._create_workflow_instance("Test problem", context, mock_function)

        assert isinstance(workflow, WorkflowInstance)
        assert workflow.name.startswith("RecursiveWorkflow_")
        assert workflow.composed_function is not None

    def test_workflow_type_creation(self):
        """Test creating workflow types for problems."""
        strategy = RecursiveStrategy(max_depth=5)

        workflow_type = strategy._create_workflow_type("Test problem")

        assert workflow_type.name.startswith("RecursiveWorkflow_")
        assert "name" in workflow_type.fields
        assert "composed_function" in workflow_type.fields
        assert "metadata" in workflow_type.fields

    def test_base_case_workflow_creation(self):
        """Test creating base case workflows for depth limits."""
        strategy = RecursiveStrategy(max_depth=3)

        context = ProblemContext(problem_statement="Deep problem", objective="Solve deep problem", original_problem="Deep problem", depth=3)

        workflow = strategy._create_base_case_workflow("Deep problem", context)

        assert isinstance(workflow, WorkflowInstance)
        assert "BaseCaseWorkflow" in str(workflow)

    def test_base_case_function_execution(self):
        """Test base case function execution."""
        strategy = RecursiveStrategy(max_depth=3)

        base_function = strategy._create_base_case_function("Test problem", None)

        result = base_function()
        assert "Base case reached" in result
        assert "Test problem" in result
        assert "Maximum recursion depth (3) exceeded" in result

    def test_recent_actions_formatting(self):
        """Test formatting of recent actions for prompts."""
        strategy = RecursiveStrategy(max_depth=5)

        # Create mock actions
        class MockAction:
            def __init__(self, action_type, description):
                self.action_type = action_type
                self.description = description

        actions = [
            MockAction("workflow_start", "Started workflow"),
            MockAction("agent_solve_call", "Called agent.solve"),
            MockAction("workflow_complete", "Completed workflow"),
        ]

        formatted = strategy._format_recent_actions(actions)

        assert "workflow_start" in formatted
        assert "agent_solve_call" in formatted
        assert "workflow_complete" in formatted
        assert "Started workflow" in formatted

    def test_empty_actions_formatting(self):
        """Test formatting when no actions are available."""
        strategy = RecursiveStrategy(max_depth=5)

        formatted = strategy._format_recent_actions([])
        assert formatted == "No recent actions"


class TestRecursiveStrategyIntegration:
    """Test RecursiveStrategy integration scenarios."""

    def test_recursive_problem_solving_flow(self):
        """Test the complete recursive problem solving flow."""
        strategy = RecursiveStrategy(max_depth=3)

        # Create initial context
        context = ProblemContext(
            problem_statement="Complex problem", objective="Solve complex problem", original_problem="Complex problem", depth=0
        )

        # Create mock agent instance
        mock_agent = type("MockAgent", (), {"llm": lambda self, request: "agent.output('complex result')"})()

        # Create workflow
        workflow = strategy.create_workflow("Complex problem", context, mock_agent)

        assert isinstance(workflow, WorkflowInstance)
        assert workflow.name.startswith("RecursiveWorkflow_")
        assert workflow.composed_function is not None

    def test_depth_progression(self):
        """Test that depth properly progresses through recursive calls."""
        strategy = RecursiveStrategy(max_depth=3)

        # Create contexts at different depths
        root_context = ProblemContext(
            problem_statement="Root problem", objective="Solve root problem", original_problem="Root problem", depth=0
        )

        sub_context1 = root_context.create_sub_context("Sub problem 1", "Solve sub problem 1")
        sub_context2 = sub_context1.create_sub_context("Sub problem 2", "Solve sub problem 2")

        # Test that strategy can handle different problems at different depths
        assert strategy.can_handle("Different sub problem 1", sub_context1) is True
        assert strategy.can_handle("Different sub problem 2", sub_context2) is True

        # Test depth limit
        sub_context3 = sub_context2.create_sub_context("Sub problem 3", "Solve sub problem 3")
        assert strategy.can_handle("Sub problem 3", sub_context3) is False

    def test_context_propagation_through_workflows(self):
        """Test that context properly propagates through workflow creation."""
        strategy = RecursiveStrategy(max_depth=3)

        # Create root context
        root_context = ProblemContext(
            problem_statement="Root problem", objective="Solve root problem", original_problem="Root problem", depth=0
        )

        # Create mock agent instance
        mock_agent = type("MockAgent", (), {"llm": lambda self, request: "agent.output('root result')"})()

        # Create root workflow
        root_workflow = strategy.create_workflow("Root problem", root_context, mock_agent)

        # Create sub-context
        sub_context = root_context.create_sub_context("Sub problem", "Solve sub problem")

        # Add workflow_instance to sub_context
        sub_context.workflow_instance = root_workflow

        # Create sub-workflow
        sub_workflow = strategy.create_workflow("Sub problem", sub_context, mock_agent)

        assert sub_workflow._parent_workflow == root_workflow
        assert sub_workflow.composed_function is not None
