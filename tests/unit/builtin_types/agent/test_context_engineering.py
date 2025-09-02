"""
Tests for the context engineering system.

This module tests the ProblemContext, EventHistory, and ComputableContext classes
that form the foundation of the agent solving system's context management.
"""

from dana.core.agent.context import (
    ComputableContext,
    EventHistory,
    ProblemContext,
)


class TestProblemContext:
    """Test ProblemContext functionality."""

    def test_create_problem_context(self):
        """Test creating a basic problem context."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)

        assert context.problem_statement == "Test problem"
        assert context.objective == "Test objective"
        assert context.original_problem == "Test problem"
        assert context.depth == 0
        assert context.constraints == {}
        assert context.assumptions == []

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


# Action class removed - replaced by Event class
# class TestAction:
#     """Test Action dataclass functionality."""
#
#     def test_create_action(self):
#         """Test creating a basic action."""
#         action = Action(
#             action_type="test_action",
#             description="Test action description",
#             depth=0,
#             timestamp=datetime.now(),
#             result="test_result",
#             workflow_id="test_workflow",
#             problem_statement="Test problem",
#             success=True,
#             execution_time=1.5,
#             error_message=None,
#         )
#
#         assert action.action_type == "test_action"
#         assert action.description == "Test action description"
#         assert action.depth == 0
#         assert action.success is True
#         assert action.execution_time == 1.5
#         assert action.error_message is None
#
#     def test_create_failed_action(self):
#         """Test creating an action that failed."""
#         action = Action(
#             action_type="failed_action",
#             description="Failed action description",
#             depth=1,
#             timestamp=datetime.now(),
#             result="error_result",
#             workflow_id="test_workflow",
#             problem_statement="Test problem",
#             success=False,
#             execution_time=0.5,
#             error_message="Something went wrong",
#         )
#
#         assert action.success is False
#         assert action.error_message == "Something went wrong"
#         assert action.execution_time == 0.5


class TestEventHistory:
    """Test EventHistory functionality."""

    def test_create_event_history(self):
        """Test creating an empty event history."""
        history = EventHistory()
        assert len(history.events) == 0

    def test_add_event(self):
        """Test adding events to history."""
        history = EventHistory()

        # Add events
        event1 = history.add_event("workflow_start", {"problem": "Problem 1", "depth": 0})
        event2 = history.add_event("workflow_complete", {"result": "success", "depth": 0})

        assert len(history.events) == 2
        assert event1.event_type == "workflow_start"
        assert event2.event_type == "workflow_complete"

    def test_start_new_conversation_turn(self):
        """Test starting a new conversation turn."""
        history = EventHistory()

        turn = history.start_new_conversation_turn("New user request")
        assert turn == 1
        assert len(history.events) == 1
        assert history.events[0].event_type == "conversation_start"
        assert history.events[0].data["user_request"] == "New user request"

    def test_get_events_by_type(self):
        """Test getting events by type."""
        history = EventHistory()

        # Add different types of events
        history.add_event("workflow_start", {"problem": "Problem 1"})
        history.add_event("workflow_complete", {"result": "success"})
        history.add_event("workflow_start", {"problem": "Problem 2"})

        workflow_starts = history.get_events_by_type("workflow_start")
        workflow_completes = history.get_events_by_type("workflow_complete")

        assert len(workflow_starts) == 2
        assert len(workflow_completes) == 1


class TestComputableContext:
    """Test ComputableContext functionality."""

    def test_empty_event_history(self):
        """Test computable context with empty event history."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = EventHistory()
        computable = ComputableContext()

        indicators = computable.get_complexity_indicators(context, history)

        assert indicators["sub_problem_count"] == 0
        assert indicators["execution_time_total"] == 0.0
        assert indicators["error_rate"] == 0.0
        assert indicators["max_depth_reached"] == 0

    def test_complexity_indicators(self):
        """Test computing complexity indicators from event history."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = EventHistory()
        computable = ComputableContext()

        # Add various events
        events_data = [
            ("workflow_start", {"depth": 0, "execution_time": 0.1}),
            ("agent_solve_call", {"depth": 1, "execution_time": 1.5}),
            ("agent_solve_call", {"depth": 2, "execution_time": 2.0}),
            ("workflow_complete", {"depth": 0, "execution_time": 0.2}),
            ("workflow_error", {"depth": 1, "execution_time": 0.5, "error": "Error occurred"}),
        ]

        for event_type, data in events_data:
            history.add_event(event_type, data)

        indicators = computable.get_complexity_indicators(context, history)

        assert indicators["sub_problem_count"] == 2  # agent_solve_call events
        assert indicators["execution_time_total"] == 4.3  # sum of all execution times
        assert indicators["error_rate"] == 0.2  # 1 out of 5 events failed
        assert indicators["max_depth_reached"] == 2  # highest depth in events

    def test_constraint_violations(self):
        """Test extracting constraint violations from failed events."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = EventHistory()
        computable = ComputableContext()

        # Add events with constraint-related errors
        constraint_errors = [
            "Constraint violation: time limit exceeded",
            "Limit reached: maximum iterations",
            "Something else went wrong",  # Not constraint-related
            "Violation detected: memory usage too high",
        ]

        for i, error_message in enumerate(constraint_errors):
            history.add_event("workflow_error", {"description": f"Event {i}", "depth": 0, "error_message": error_message})

        violations = computable.get_constraint_violations(context, history)

        # Should find 3 constraint-related violations
        assert len(violations) == 3
        assert any("time limit exceeded" in v for v in violations)
        assert any("maximum iterations" in v for v in violations)
        assert any("memory usage too high" in v for v in violations)
        assert not any("Something else went wrong" in v for v in violations)

    def test_successful_patterns(self):
        """Test identifying successful patterns from events."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = EventHistory()
        computable = ComputableContext()

        # Add events that should trigger pattern recognition
        pattern_events = [
            "agent_solve_call",  # 1st solve call
            "agent_solve_call",  # 2nd solve call
            "agent_solve_call",  # 3rd solve call - triggers recursive_decomposition
            "agent_input",  # triggers user_interaction
            "agent_reason",  # 1st reason
            "agent_reason",  # 2nd reason
            "agent_reason",  # 3rd reason
            "agent_reason",  # 4th reason - triggers reasoning_intensive
        ]

        for i, event_type in enumerate(pattern_events):
            history.add_event(event_type, {"description": f"Event {i}", "depth": 0})

        patterns = computable.get_successful_patterns(context, history)

        assert "recursive_decomposition" in patterns
        assert "user_interaction" in patterns
        assert "reasoning_intensive" in patterns
        assert len(patterns) == 3

    def test_no_patterns_detected(self):
        """Test when no patterns are detected."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = EventHistory()
        computable = ComputableContext()

        # Add events that don't trigger patterns
        simple_events = [
            "workflow_start",
            "workflow_complete",
        ]

        for i, event_type in enumerate(simple_events):
            history.add_event(event_type, {"description": f"Event {i}", "depth": 0})

        patterns = computable.get_successful_patterns(context, history)

        assert len(patterns) == 0
        assert patterns == []


class TestContextIntegration:
    """Test integration between context components."""

    def test_context_propagation_chain(self):
        """Test that context properly propagates through a chain of sub-problems."""
        # Create root context
        root_context = ProblemContext(
            problem_statement="Root problem",
            objective="Solve root problem",
            original_problem="Root problem",
            depth=0,
            constraints={"hard": ["time_limit"]},
            assumptions=["assumption1"],
        )

        # Create event history
        history = EventHistory()

        # Simulate solving sub-problems
        sub_context1 = root_context.create_sub_context("Sub problem 1", "Solve sub problem 1")
        sub_context2 = sub_context1.create_sub_context("Sub problem 2", "Solve sub problem 2")

        # Add events at different depths
        for depth, context in [(0, root_context), (1, sub_context1), (2, sub_context2)]:
            history.add_event(
                "agent_solve_call",
                {
                    "description": f"Solving at depth {depth}",
                    "depth": depth,
                    "result": f"result_depth_{depth}",
                    "workflow_id": "workflow1",
                    "problem_statement": context.problem_statement,
                    "execution_time": 1.0,
                },
            )

        # Test computable context can analyze the chain
        computable = ComputableContext()
        indicators = computable.get_complexity_indicators(root_context, history)

        assert indicators["sub_problem_count"] == 3  # All agent_solve_call actions
        assert indicators["max_depth_reached"] == 2  # Highest depth reached
        assert indicators["execution_time_total"] == 3.0  # Sum of all execution times
