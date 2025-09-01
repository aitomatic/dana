"""
Tests for the context engineering system.

This module tests the ProblemContext, ActionHistory, and ComputableContext classes
that form the foundation of the agent solving system's context management.
"""

from datetime import datetime

from dana.builtin_types.agent.context import (
    Action,
    ActionHistory,
    ComputableContext,
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


class TestAction:
    """Test Action dataclass functionality."""

    def test_create_action(self):
        """Test creating a basic action."""
        action = Action(
            action_type="test_action",
            description="Test action description",
            depth=0,
            timestamp=datetime.now(),
            result="test_result",
            workflow_id="test_workflow",
            problem_statement="Test problem",
            success=True,
            execution_time=1.5,
            error_message=None,
        )

        assert action.action_type == "test_action"
        assert action.description == "Test action description"
        assert action.depth == 0
        assert action.success is True
        assert action.execution_time == 1.5
        assert action.error_message is None

    def test_create_failed_action(self):
        """Test creating an action that failed."""
        action = Action(
            action_type="failed_action",
            description="Failed action description",
            depth=1,
            timestamp=datetime.now(),
            result="error_result",
            workflow_id="test_workflow",
            problem_statement="Test problem",
            success=False,
            execution_time=0.5,
            error_message="Something went wrong",
        )

        assert action.success is False
        assert action.error_message == "Something went wrong"
        assert action.execution_time == 0.5


class TestActionHistory:
    """Test ActionHistory functionality."""

    def test_create_action_history(self):
        """Test creating an empty action history."""
        history = ActionHistory()
        assert len(history.actions) == 0

    def test_add_action(self):
        """Test adding actions to history."""
        history = ActionHistory()

        action1 = Action(
            action_type="action1",
            description="First action",
            depth=0,
            timestamp=datetime.now(),
            result="result1",
            workflow_id="workflow1",
            problem_statement="Problem 1",
            success=True,
            execution_time=1.0,
            error_message=None,
        )

        action2 = Action(
            action_type="action2",
            description="Second action",
            depth=0,
            timestamp=datetime.now(),
            result="result2",
            workflow_id="workflow1",
            problem_statement="Problem 1",
            success=True,
            execution_time=2.0,
            error_message=None,
        )

        history.add_action(action1)
        history.add_action(action2)

        assert len(history.actions) == 2
        assert history.actions[0] == action1
        assert history.actions[1] == action2

    def test_get_recent_actions(self):
        """Test getting recent actions."""
        history = ActionHistory()

        # Add 5 actions
        for i in range(5):
            action = Action(
                action_type=f"action{i}",
                description=f"Action {i}",
                depth=0,
                timestamp=datetime.now(),
                result=f"result{i}",
                workflow_id="workflow1",
                problem_statement="Problem 1",
                success=True,
                execution_time=float(i),
                error_message=None,
            )
            history.add_action(action)

        # Get last 3 actions
        recent = history.get_recent_actions(3)
        assert len(recent) == 3
        assert recent[0].action_type == "action2"
        assert recent[1].action_type == "action3"
        assert recent[2].action_type == "action4"

    def test_get_actions_by_depth(self):
        """Test getting actions by recursion depth."""
        history = ActionHistory()

        # Add actions at different depths
        for depth in [0, 1, 0, 2, 1]:
            action = Action(
                action_type=f"action_depth_{depth}",
                description=f"Action at depth {depth}",
                depth=depth,
                timestamp=datetime.now(),
                result=f"result_depth_{depth}",
                workflow_id="workflow1",
                problem_statement="Problem 1",
                success=True,
                execution_time=1.0,
                error_message=None,
            )
            history.add_action(action)

        depth_0_actions = history.get_actions_by_depth(0)
        depth_1_actions = history.get_actions_by_depth(1)
        depth_2_actions = history.get_actions_by_depth(2)

        assert len(depth_0_actions) == 2
        assert len(depth_1_actions) == 2
        assert len(depth_2_actions) == 1

    def test_get_actions_by_type(self):
        """Test getting actions by action type."""
        history = ActionHistory()

        # Add different types of actions
        action_types = ["workflow_start", "agent_solve_call", "workflow_complete", "agent_solve_call"]

        for i, action_type in enumerate(action_types):
            action = Action(
                action_type=action_type,
                description=f"Action {i}",
                depth=0,
                timestamp=datetime.now(),
                result=f"result{i}",
                workflow_id="workflow1",
                problem_statement="Problem 1",
                success=True,
                execution_time=1.0,
                error_message=None,
            )
            history.add_action(action)

        solve_calls = history.get_actions_by_type("agent_solve_call")
        workflow_starts = history.get_actions_by_type("workflow_start")

        assert len(solve_calls) == 2
        assert len(workflow_starts) == 1


class TestComputableContext:
    """Test ComputableContext functionality."""

    def test_empty_action_history(self):
        """Test computable context with empty action history."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = ActionHistory()
        computable = ComputableContext()

        indicators = computable.get_complexity_indicators(context, history)

        assert indicators["sub_problem_count"] == 0
        assert indicators["execution_time_total"] == 0.0
        assert indicators["error_rate"] == 0.0
        assert indicators["max_depth_reached"] == 0

    def test_complexity_indicators(self):
        """Test computing complexity indicators from action history."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = ActionHistory()
        computable = ComputableContext()

        # Add various actions
        actions_data = [
            ("workflow_start", True, 0, 0.1),
            ("agent_solve_call", True, 1, 1.5),
            ("agent_solve_call", True, 2, 2.0),
            ("workflow_complete", True, 0, 0.2),
            ("workflow_error", False, 1, 0.5),
        ]

        for action_type, success, depth, execution_time in actions_data:
            action = Action(
                action_type=action_type,
                description=f"{action_type} action",
                depth=depth,
                timestamp=datetime.now(),
                result=f"result_{action_type}",
                workflow_id="workflow1",
                problem_statement="Problem 1",
                success=success,
                execution_time=execution_time,
                error_message="Error occurred" if not success else None,
            )
            history.add_action(action)

        indicators = computable.get_complexity_indicators(context, history)

        assert indicators["sub_problem_count"] == 2  # agent_solve_call actions
        assert indicators["execution_time_total"] == 4.3  # sum of all execution times
        assert indicators["error_rate"] == 0.2  # 1 out of 5 actions failed
        assert indicators["max_depth_reached"] == 2  # highest depth in actions

    def test_constraint_violations(self):
        """Test extracting constraint violations from failed actions."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = ActionHistory()
        computable = ComputableContext()

        # Add actions with constraint-related errors
        constraint_errors = [
            "Constraint violation: time limit exceeded",
            "Limit reached: maximum iterations",
            "Something else went wrong",  # Not constraint-related
            "Violation detected: memory usage too high",
        ]

        for i, error_message in enumerate(constraint_errors):
            action = Action(
                action_type=f"action{i}",
                description=f"Action {i}",
                depth=0,
                timestamp=datetime.now(),
                result=f"result{i}",
                workflow_id="workflow1",
                problem_statement="Problem 1",
                success=False,
                execution_time=1.0,
                error_message=error_message,
            )
            history.add_action(action)

        violations = computable.get_constraint_violations(context, history)

        # Should find 3 constraint-related violations
        assert len(violations) == 3
        assert any("time limit exceeded" in v for v in violations)
        assert any("maximum iterations" in v for v in violations)
        assert any("memory usage too high" in v for v in violations)
        assert not any("Something else went wrong" in v for v in violations)

    def test_successful_patterns(self):
        """Test identifying successful patterns from actions."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = ActionHistory()
        computable = ComputableContext()

        # Add actions that should trigger pattern recognition
        pattern_actions = [
            ("agent_solve_call", True),  # 1st solve call
            ("agent_solve_call", True),  # 2nd solve call
            ("agent_solve_call", True),  # 3rd solve call - triggers recursive_decomposition
            ("agent_input", True),  # triggers user_interaction
            ("agent_reason", True),  # 1st reason
            ("agent_reason", True),  # 2nd reason
            ("agent_reason", True),  # 3rd reason
            ("agent_reason", True),  # 4th reason - triggers reasoning_intensive
        ]

        for i, (action_type, success) in enumerate(pattern_actions):
            action = Action(
                action_type=action_type,
                description=f"Action {i}",
                depth=0,
                timestamp=datetime.now(),
                result=f"result{i}",
                workflow_id="workflow1",
                problem_statement="Problem 1",
                success=success,
                execution_time=1.0,
                error_message=None,
            )
            history.add_action(action)

        patterns = computable.get_successful_patterns(context, history)

        assert "recursive_decomposition" in patterns
        assert "user_interaction" in patterns
        assert "reasoning_intensive" in patterns
        assert len(patterns) == 3

    def test_no_patterns_detected(self):
        """Test when no patterns are detected."""
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        history = ActionHistory()
        computable = ComputableContext()

        # Add actions that don't trigger patterns
        simple_actions = [
            ("workflow_start", True),
            ("workflow_complete", True),
        ]

        for i, (action_type, success) in enumerate(simple_actions):
            action = Action(
                action_type=action_type,
                description=f"Action {i}",
                depth=0,
                timestamp=datetime.now(),
                result=f"result{i}",
                workflow_id="workflow1",
                problem_statement="Problem 1",
                success=success,
                execution_time=1.0,
                error_message=None,
            )
            history.add_action(action)

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

        # Create action history
        history = ActionHistory()

        # Simulate solving sub-problems
        sub_context1 = root_context.create_sub_context("Sub problem 1", "Solve sub problem 1")
        sub_context2 = sub_context1.create_sub_context("Sub problem 2", "Solve sub problem 2")

        # Add actions at different depths
        for depth, context in [(0, root_context), (1, sub_context1), (2, sub_context2)]:
            action = Action(
                action_type="agent_solve_call",
                description=f"Solving at depth {depth}",
                depth=depth,
                timestamp=datetime.now(),
                result=f"result_depth_{depth}",
                workflow_id="workflow1",
                problem_statement=context.problem_statement,
                success=True,
                execution_time=1.0,
                error_message=None,
            )
            history.add_action(action)

        # Test computable context can analyze the chain
        computable = ComputableContext()
        indicators = computable.get_complexity_indicators(root_context, history)

        assert indicators["sub_problem_count"] == 3  # All agent_solve_call actions
        assert indicators["max_depth_reached"] == 2  # Highest depth reached
        assert indicators["execution_time_total"] == 3.0  # Sum of all execution times
