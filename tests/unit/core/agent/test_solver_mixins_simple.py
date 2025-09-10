"""
Simple tests for the solver mixins without full agent system imports.

This module tests the solver functionality in isolation to avoid circular import issues.
"""

import pytest
from unittest.mock import Mock

# Import only the solver mixins directly to avoid circular imports
from dana.core.agent.methods.solvers.base import BaseSolverMixin
from dana.core.agent.methods.solvers.planner_executor import PlannerExecutorSolverMixin
from dana.core.agent.methods.solvers.reactive_support import ReactiveSupportSolverMixin


class ConcreteSolverMixin(BaseSolverMixin):
    """Concrete implementation of BaseSolverMixin for testing."""

    def solve_sync(self, problem_or_workflow, artifacts=None, sandbox_context=None, **kwargs):
        """Concrete implementation of solve_sync."""
        return {"result": "test"}


class TestBaseSolverMixinSimple:
    """Test the base solver mixin functionality in isolation."""

    def test_base_solver_mixin_initialization(self):
        """Test that BaseSolverMixin initializes correctly."""
        mixin = ConcreteSolverMixin()

        assert hasattr(mixin, "_context_engineer")
        assert hasattr(mixin, "_llm_resource")
        assert mixin._context_engineer is None
        assert mixin._llm_resource is None

    def test_inject_dependencies(self):
        """Test dependency injection functionality."""
        mixin = ConcreteSolverMixin()

        # Test with no dependencies
        wc, ri, sig = mixin._inject_dependencies()
        assert wc is None
        assert ri is None
        assert sig is None

        # Test with provided dependencies
        mock_wc = Mock()
        mock_ri = Mock()
        mock_sig = Mock()

        wc, ri, sig = mixin._inject_dependencies(workflow_catalog=mock_wc, resource_index=mock_ri, signature_matcher=mock_sig)
        assert wc is mock_wc
        assert ri is mock_ri
        assert sig is mock_sig

    def test_initialize_solver_state(self):
        """Test solver state initialization."""
        mixin = ConcreteSolverMixin()

        artifacts = {}
        state = mixin._initialize_solver_state(artifacts, "_test_state")

        assert "_test_state" in artifacts
        assert state is artifacts["_test_state"]
        assert isinstance(state, dict)

    def test_extract_entities(self):
        """Test entity extraction from artifacts."""
        mixin = ConcreteSolverMixin()

        artifacts = {"_entities": {"user": "test", "domain": "testing"}}
        entities = mixin._extract_entities(artifacts)

        assert entities == {"user": "test", "domain": "testing"}

        # Test with no entities
        artifacts = {}
        entities = mixin._extract_entities(artifacts)
        assert entities == {}

    def test_create_ask_response(self):
        """Test ask response creation."""
        mixin = ConcreteSolverMixin()
        mixin.MIXIN_NAME = "test_mixin"

        response = mixin._create_ask_response("Test message")

        assert response["type"] == "ask"
        assert response["message"] == "Test message"
        assert response["telemetry"]["mixin"] == "test_mixin"

        # Test with missing items
        response = mixin._create_ask_response("Test message", missing=["item1", "item2"])
        assert response["missing"] == ["item1", "item2"]

    def test_create_answer_response(self):
        """Test answer response creation."""
        mixin = ConcreteSolverMixin()
        mixin.MIXIN_NAME = "test_mixin"

        artifacts = {"test": "data"}
        response = mixin._create_answer_response("test_mode", artifacts, "test_selection", extra="value")

        assert response["type"] == "answer"
        assert response["mode"] == "test_mode"
        assert response["telemetry"]["mixin"] == "test_mixin"
        assert response["telemetry"]["selected"] == "test_selection"
        assert response["artifacts"] == artifacts
        assert response["extra"] == "value"


class TestPlannerExecutorSolverMixinSimple:
    """Test the planner-executor solver mixin in isolation."""

    def test_planner_executor_initialization(self):
        """Test that PlannerExecutorSolverMixin initializes correctly."""
        mixin = PlannerExecutorSolverMixin()

        assert mixin.MIXIN_NAME == "planner_executor"
        assert hasattr(mixin, "_context_engineer")
        assert hasattr(mixin, "_llm_resource")

    def test_solve_sync_with_empty_goal(self):
        """Test solving with an empty goal string."""
        mixin = PlannerExecutorSolverMixin()
        mixin.MIXIN_NAME = "planner_executor"

        result = mixin.solve_sync("")

        assert result["type"] == "ask"
        assert "goal to plan" in result["message"]
        assert result["telemetry"]["mixin"] == "planner_executor"

    def test_draft_plan_heuristic(self):
        """Test heuristic plan drafting."""
        mixin = PlannerExecutorSolverMixin()

        # Test with a simple goal
        steps = mixin._heuristic_draft_plan("test goal", max_steps=3)

        assert len(steps) <= 3
        assert all(isinstance(step, str) for step in steps)
        assert any("test goal" in step for step in steps)

    def test_structure_plan(self):
        """Test plan structuring."""
        mixin = PlannerExecutorSolverMixin()

        steps = ["analyze the problem", "implement solution", "test the result"]
        structured = mixin._structure_plan(steps)

        assert len(structured) == 3
        assert structured[0]["type"] == "action"  # "analyze" is treated as action to avoid recursion
        assert structured[1]["type"] == "action"  # "implement" is an action verb
        assert structured[2]["type"] == "action"  # "test" is an action verb

    def test_exec_action_dry_run(self):
        """Test action execution in dry run mode."""
        mixin = PlannerExecutorSolverMixin()

        # Test dry run
        result = mixin._exec_action("test action", None, dry_run=True)
        assert result["status"] == "ok (dry-run)"
        assert "would be executed" in result["message"]

        # Test with no sandbox context - should raise error
        with pytest.raises(RuntimeError, match="No LLM resource available for action execution"):
            mixin._exec_action("test action", None, dry_run=False)

    def test_exec_action_with_patterns(self):
        """Test action execution with pattern recognition."""
        mixin = PlannerExecutorSolverMixin()

        # Create a mock sandbox context with LLM resource
        mock_context = Mock()
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = {"choices": [{"message": {"content": "Action executed successfully"}}]}
        mock_llm.query_sync.return_value = mock_response
        mock_context.get_resource.return_value = mock_llm

        # Test file action
        result = mixin._exec_action("create file test.txt", mock_context, dry_run=False)
        assert result["status"] == "ok"
        assert result["action"] == "create file test.txt"
        assert "message" in result

        # Test API action
        result = mixin._exec_action("call api endpoint", mock_context, dry_run=False)
        assert result["status"] == "ok"
        assert result["action"] == "call api endpoint"
        assert "message" in result


class TestReactiveSupportSolverMixinSimple:
    """Test the reactive support solver mixin in isolation."""

    def test_reactive_support_initialization(self):
        """Test that ReactiveSupportSolverMixin initializes correctly."""
        mixin = ReactiveSupportSolverMixin()

        assert mixin.MIXIN_NAME == "reactive_support"
        assert hasattr(mixin, "_context_engineer")
        assert hasattr(mixin, "_llm_resource")

    def test_solve_sync_with_empty_message(self):
        """Test solving with an empty message."""
        mixin = ReactiveSupportSolverMixin()
        mixin.MIXIN_NAME = "reactive_support"

        result = mixin.solve_sync("")

        assert result["type"] == "ask"
        assert "describe the issue" in result["message"]
        assert result["telemetry"]["mixin"] == "reactive_support"

    def test_preliminary_analysis(self):
        """Test preliminary analysis functionality."""
        mixin = ReactiveSupportSolverMixin()

        # Test critical severity
        analysis = mixin._preliminary_analysis("system crash data loss", {})
        assert analysis["severity"] == "critical"

        # Test high severity
        analysis = mixin._preliminary_analysis("application failed to start", {})
        assert analysis["severity"] == "high"

        # Test medium severity
        analysis = mixin._preliminary_analysis("there's a bug in the system", {})
        assert analysis["severity"] == "medium"

        # Test category detection
        analysis = mixin._preliminary_analysis("configuration setting issue", {})
        assert analysis["category"] == "configuration"

        analysis = mixin._preliminary_analysis("network connection problem", {})
        assert analysis["category"] == "connectivity"

        analysis = mixin._preliminary_analysis("slow performance issue", {})
        assert analysis["category"] == "performance"

    def test_infer_missing(self):
        """Test missing artifact inference."""
        mixin = ReactiveSupportSolverMixin()

        # Test with no artifacts
        missing = mixin._infer_missing(["logs", "config"], "test message", {})
        assert "logs" in missing
        assert "config" in missing

        # Test with artifacts present
        artifacts = {"logs": "test logs"}
        missing = mixin._infer_missing(["logs", "config"], "test message", artifacts)
        assert "logs" not in missing
        assert "config" in missing

        # Test with config-like tokens in message
        missing = mixin._infer_missing(["logs", "config"], "setting = value", {})
        assert len(missing) == 0  # Should detect config-like content

    def test_draft_checklist(self):
        """Test checklist drafting."""
        mixin = ReactiveSupportSolverMixin()

        preliminary = {"category": "performance", "severity": "high"}
        checklist = mixin._draft_checklist("performance issue", {}, {}, preliminary)

        assert isinstance(checklist, list)
        assert len(checklist) > 0
        assert all(isinstance(item, str) for item in checklist)
        assert all(item.startswith("- ") for item in checklist)

    def test_canonical_key(self):
        """Test canonical key generation."""
        mixin = ReactiveSupportSolverMixin()

        assert mixin._canonical_key("log snippet") == "logs"
        assert mixin._canonical_key("config block") == "config"
        assert mixin._canonical_key("memory dump") == "dump"
        assert mixin._canonical_key("screenshot capture") == "screenshot"
        assert mixin._canonical_key("other item") == "other_item"

    def test_ref_titles(self):
        """Test reference title extraction."""
        mixin = ReactiveSupportSolverMixin()

        refs = [{"title": "Test Doc", "id": "doc1"}, {"name": "Another Doc", "id": "doc2"}, "Simple String", {"id": "doc3"}]

        titles = mixin._ref_titles(refs)
        assert titles == ["Test Doc", "Another Doc", "Simple String", "doc3"]


if __name__ == "__main__":
    pytest.main([__file__])
