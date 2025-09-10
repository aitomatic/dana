"""
Tests for the context engineering system.

This module tests the ProblemContext and other context-related classes
that form the foundation of the agent solving system's context management.
"""

from dana.core.agent.context import ProblemContext, ExecutionContext
from dana.core.agent.timeline import Timeline


class TestProblemContext:
    """Test ProblemContext functionality."""

    def test_create_problem_context(self):
        """Test creating a basic problem context."""
        context = ProblemContext(problem_statement="Test problem")

        assert context.problem_statement == "Test problem"
        assert context.objective == "Test problem"  # Defaults to problem_statement
        assert context.original_problem == "Test problem"  # Defaults to problem_statement
        assert context.depth == 0
        assert context.constraints == {}
        assert context.assumptions == []

    def test_create_problem_context_with_explicit_values(self):
        """Test creating problem context with explicit values."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Original problem", depth=2)

        assert context.problem_statement == "Test problem"
        assert context.objective == "Test objective"
        assert context.original_problem == "Original problem"
        assert context.depth == 2

    def test_create_sub_context(self):
        """Test creating sub-contexts for recursive problem solving."""
        parent_context = ProblemContext(
            problem_statement="Parent problem",
            objective="Parent objective",
            original_problem="Parent problem",
            depth=0,
            constraints={"hard": ["time_limit"]},
            assumptions=["assumption1", "assumption2"],
        )

        sub_context = parent_context.create_sub_context("Sub problem", "Sub objective")

        assert sub_context.problem_statement == "Sub problem"
        assert sub_context.objective == "Sub objective"
        assert sub_context.original_problem == "Parent problem"
        assert sub_context.depth == 1
        assert sub_context.constraints == {"hard": ["time_limit"]}
        assert sub_context.assumptions == ["assumption1", "assumption2"]

    def test_context_immutability(self):
        """Test that sub-contexts don't modify parent contexts."""
        parent_context = ProblemContext(
            problem_statement="Parent problem",
            objective="Parent objective",
            original_problem="Parent problem",
            depth=0,
            constraints={"hard": ["time_limit"]},
            assumptions=["assumption1"],
        )

        # Create sub-context
        sub_context = parent_context.create_sub_context("Sub problem", "Sub objective")

        # Modify sub-context
        sub_context.constraints["hard"].append("new_constraint")
        sub_context.assumptions.append("new_assumption")

        # Parent should remain unchanged
        assert parent_context.constraints == {"hard": ["time_limit"]}
        assert parent_context.assumptions == ["assumption1"]

    def test_to_dict(self):
        """Test converting ProblemContext to dictionary."""
        context = ProblemContext(
            problem_statement="Test problem",
            objective="Test objective",
            depth=1,
            constraints={"time": "5min"},
            assumptions=["test assumption"],
        )

        result = context.to_dict()

        assert result["problem_statement"] == "Test problem"
        assert result["objective"] == "Test objective"
        assert result["depth"] == 1
        assert result["constraints"] == {"time": "5min"}
        assert result["assumptions"] == ["test assumption"]


class TestExecutionContext:
    """Test ExecutionContext functionality."""

    def test_create_execution_context(self):
        """Test creating execution context."""
        context = ExecutionContext()

        assert context.workflow_id is None
        assert context.recursion_depth == 0
        assert context.is_running is False
        assert context.can_proceed()

    def test_resource_limits(self):
        """Test resource limit checking."""
        context = ExecutionContext()

        # Default should allow proceeding
        assert context.can_proceed()

        # High memory usage should block
        context.current_metrics.memory_usage_mb = 2000
        assert not context.can_proceed()

    def test_constraints(self):
        """Test constraint management."""
        context = ExecutionContext()

        context.add_constraint("test_constraint", "test_value")
        constraints = context.get_constraints()

        assert "test_constraint" in constraints
        assert constraints["test_constraint"] == "test_value"

    def test_recursion_management(self):
        """Test recursion depth management."""
        context = ExecutionContext()

        # Should allow entering recursion initially
        assert context.enter_recursion()
        assert context.recursion_depth == 1

        # Should track depth properly
        assert context.enter_recursion()
        assert context.recursion_depth == 2

        # Should handle exit properly
        context.exit_recursion()
        assert context.recursion_depth == 1


class TestTimeline:
    """Test Timeline functionality."""

    def test_create_timeline(self):
        """Test creating an empty timeline."""
        import uuid
        timeline = Timeline(agent_id=f"test_{uuid.uuid4()}")
        assert timeline.get_event_count() == 0

    def test_add_action(self):
        """Test adding action events to timeline."""
        import uuid
        timeline = Timeline(agent_id=f"test_{uuid.uuid4()}")

        # Wait for async loading to complete
        timeline._wait_for_loading()

        # Add action event using new API
        timeline.add_action("test_event", "test_action", depth=0)

        assert timeline.get_event_count() == 1
        actions = timeline.get_events_by_type("action")
        assert len(actions) == 1
        assert actions[0].event_type == "agent_action"

    def test_timeline_basic_functionality(self):
        """Test basic Timeline functionality with multiple event types."""
        import uuid
        import time
        timeline = Timeline(agent_id=f"test_{uuid.uuid4()}")

        # Wait for async loading to complete
        timeline._wait_for_loading()

        # Add multiple events of different types
        timeline.add_action("event1", "action1", depth=0)
        timeline.add_action("event2", "action2", depth=1)
        timeline.add_conversation_turn("Hello", "Hi there!", turn_number=1)

        assert timeline.get_event_count() == 3
        
        # Check event types
        actions = timeline.get_events_by_type("action")
        conversations = timeline.get_events_by_type("conversation")
        
        assert len(actions) == 2
        assert len(conversations) == 1
        assert actions[0].event_type == "agent_action"
        assert conversations[0].event_type == "conversation_turn"
