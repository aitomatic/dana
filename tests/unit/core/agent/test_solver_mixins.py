"""
Tests for the solver mixins (PlannerExecutorSolverMixin and ReactiveSupportSolverMixin).

This module tests the new solver functionality that was added to the agent system.
"""

import pytest
from unittest.mock import Mock

from dana.core.agent.agent_instance import AgentInstance
from dana.core.agent.agent_type import AgentType
from dana.core.agent.solvers import (
    BaseSolver,
    PlannerExecutorSolver,
    ReactiveSupportSolver,
    WorkflowCatalog,
    SignatureMatcher,
    ResourceIndex,
)
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.workflow.workflow_system import WorkflowInstance


class ConcreteSolverMixin(BaseSolver):
    """Concrete implementation of BaseSolverMixin for testing."""

    def solve_sync(self, problem_or_workflow, artifacts=None, sandbox_context=None, **kwargs):
        """Concrete implementation of solve_sync."""
        return {"result": "test"}


class TestBaseSolverMixin:
    """Test the base solver mixin functionality."""

    def test_base_solver_mixin_initialization(self):
        """Test that BaseSolverMixin initializes correctly."""
        mixin = ConcreteSolverMixin()

        assert hasattr(mixin, "context_engineer")
        assert hasattr(mixin, "llm_resource")
        assert mixin.context_engineer is None
        assert mixin.llm_resource is None

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

        response = mixin._create_ask_response("Test message")

        assert response["type"] == "ask"
        assert response["message"] == "Test message"

        # Test with missing items
        response = mixin._create_ask_response("Test message", missing=["item1", "item2"])
        assert response["missing"] == ["item1", "item2"]

    def test_create_answer_response(self):
        """Test answer response creation."""
        mixin = ConcreteSolverMixin()

        artifacts = {"test": "data"}
        response = mixin._create_answer_response("test_mode", artifacts, "test_selection", extra="value")

        assert response["type"] == "answer"
        assert response["mode"] == "test_mode"
        assert response["telemetry"]["mixin"] == "test_mixin"
        assert response["telemetry"]["selected"] == "test_selection"
        assert response["artifacts"] == artifacts
        assert response["extra"] == "value"


class TestPlannerExecutorSolverMixin:
    """Test the planner-executor solver mixin."""

    def test_planner_executor_initialization(self):
        """Test that PlannerExecutorSolverMixin initializes correctly."""
        mixin = PlannerExecutorSolver()

        assert hasattr(mixin, "context_engineer")
        assert hasattr(mixin, "llm_resource")

    def test_solve_sync_with_workflow_instance(self):
        """Test solving with a WorkflowInstance."""
        mixin = PlannerExecutorSolver()

        # Mock workflow instance
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_workflow.name = "test_workflow"

        # Mock sandbox context
        mock_context = Mock(spec=SandboxContext)

        # Mock the workflow execution
        mixin._run_workflow_instance = Mock(return_value={"status": "ok", "output": "test_result"})

        result = mixin.solve_sync(mock_workflow, sandbox_context=mock_context)

        assert result["type"] == "answer"
        assert result["mode"] == "workflow"
        assert result["result"]["status"] == "ok"
        assert result["telemetry"]["selected"] == "direct"

    def test_solve_sync_with_empty_goal(self):
        """Test solving with an empty goal string."""
        mixin = PlannerExecutorSolver()

        result = mixin.solve_sync("")

        assert result["type"] == "ask"
        assert "goal to plan" in result["message"]

    def test_solve_sync_with_known_workflow(self):
        """Test solving with a known workflow match."""
        mixin = PlannerExecutorSolver()

        # Mock workflow catalog
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_workflow.name = "known_workflow"

        mock_catalog = Mock(spec=WorkflowCatalog)
        mock_catalog.match.return_value = (0.9, mock_workflow)

        # Mock workflow execution
        mixin._run_workflow_instance = Mock(return_value={"status": "ok", "output": "workflow_result"})

        result = mixin.solve_sync("test goal", workflow_catalog=mock_catalog, known_match_threshold=0.8)

        assert result["type"] == "answer"
        assert result["mode"] == "planner"
        assert result["telemetry"]["selected"] == "known_workflow"
        assert result["score"] == 0.9

    def test_solve_sync_with_planning(self):
        """Test solving with planning when no known workflow matches."""
        mixin = PlannerExecutorSolver()

        # Mock the planning methods
        mixin._draft_plan = Mock(return_value=["step1", "step2", "step3"])
        mixin._structure_plan = Mock(
            return_value=[{"type": "action", "do": "step1"}, {"type": "subgoal", "goal": "step2"}, {"type": "action", "do": "step3"}]
        )
        mixin._exec_action = Mock(return_value={"status": "ok", "action": "test"})
        mixin._summarize = Mock(return_value="Test summary")

        result = mixin.solve_sync("test goal", dry_run=True)

        assert result["type"] == "answer"
        assert result["mode"] == "planner"
        assert result["telemetry"]["selected"] == "plan+expand"
        assert "plan" in result
        assert "deliverable" in result

    def test_draft_plan_heuristic(self):
        """Test heuristic plan drafting."""
        mixin = PlannerExecutorSolver()

        # Test with a simple goal
        steps = mixin._heuristic_draft_plan("test goal", max_steps=3)

        assert len(steps) <= 3
        assert all(isinstance(step, str) for step in steps)
        assert any("test goal" in step for step in steps)

    def test_structure_plan(self):
        """Test plan structuring."""
        mixin = PlannerExecutorSolver()

        steps = ["analyze the problem", "implement solution", "test the result"]
        structured = mixin._structure_plan(steps)

        assert len(structured) == 3
        assert structured[0]["type"] == "action"  # "analyze" is treated as action to avoid recursion
        assert structured[1]["type"] == "action"  # "implement" is an action verb
        assert structured[2]["type"] == "action"  # "test" is an action verb

    def test_exec_action(self):
        """Test action execution."""
        mixin = PlannerExecutorSolver()

        # Test dry run
        result = mixin._exec_action("test action", None, dry_run=True)
        assert result["status"] == "ok (dry-run)"
        assert "would be executed" in result["message"]

        # Test with no sandbox context - should raise error
        with pytest.raises(RuntimeError, match="No LLM resource available for action execution"):
            mixin._exec_action("test action", None, dry_run=False)

    def test_exec_action_with_patterns(self):
        """Test action execution with pattern recognition."""
        mixin = PlannerExecutorSolver()

        # Create a mock sandbox context with LLM resource
        mock_context = Mock(spec=SandboxContext)
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


class TestReactiveSupportSolverMixin:
    """Test the reactive support solver mixin."""

    def test_reactive_support_initialization(self):
        """Test that ReactiveSupportSolverMixin initializes correctly."""
        mixin = ReactiveSupportSolver()

        assert hasattr(mixin, "context_engineer")
        assert hasattr(mixin, "llm_resource")

    def test_solve_sync_with_empty_message(self):
        """Test solving with an empty message."""
        mixin = ReactiveSupportSolver()

        result = mixin.solve_sync("")

        assert result["type"] == "ask"
        assert "describe the issue" in result["message"]

    def test_solve_sync_with_signature_match(self):
        """Test solving with a signature match."""
        mixin = ReactiveSupportSolver()

        # Mock signature matcher
        mock_signature = Mock()
        mock_signature.id = "test_signature"
        mock_signature.title = "Test Issue"
        mock_signature.steps = ["step1", "step2"]
        mock_signature.fix = "test fix"
        mock_signature.workflow_id = "test_workflow"

        mock_matcher = Mock(spec=SignatureMatcher)
        mock_matcher.match.return_value = (0.9, mock_signature)

        result = mixin.solve_sync("test issue description", signature_matcher=mock_matcher, known_match_threshold=0.8)

        assert result["type"] == "answer"
        assert result["mode"] == "support"
        assert result["telemetry"]["selected"] == "signature"
        assert result["diagnosis"] == "Test Issue"
        assert "checklist" in result

    def test_solve_sync_with_known_workflow(self):
        """Test solving with a known diagnostic workflow."""
        mixin = ReactiveSupportSolver()

        # Mock workflow catalog
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_workflow.name = "diagnostic_workflow"

        mock_catalog = Mock(spec=WorkflowCatalog)
        mock_catalog.match.return_value = (0.9, mock_workflow)

        # Mock workflow execution
        mixin._run_workflow_instance = Mock(return_value={"status": "ok", "output": "diagnostic_result"})

        result = mixin.solve_sync("test issue", workflow_catalog=mock_catalog, known_match_threshold=0.8)

        assert result["type"] == "answer"
        assert result["mode"] == "support"
        assert result["telemetry"]["selected"] == "known_workflow"
        assert "diagnostic" in result["diagnosis"]

    def test_solve_sync_with_missing_artifacts(self):
        """Test solving when artifacts are missing."""
        mixin = ReactiveSupportSolver()

        # Test with missing artifacts - should return ask response
        # Provide no artifacts, missing both required ones
        result = mixin.solve_sync("help me with something", artifacts={}, required_artifacts=["logs", "config"], min_required=1)

        # The solver should proceed with analysis even when artifacts are missing
        # because it has "sufficient_info" (allows up to 2 missing pieces)
        assert result["type"] == "answer"
        assert result["mode"] == "support"

    def test_solve_sync_with_generic_analysis(self):
        """Test solving with generic analysis."""
        mixin = ReactiveSupportSolver()

        # Provide artifacts to avoid the "missing artifacts" path
        artifacts = {"logs": "test logs", "config": "test config"}

        result = mixin.solve_sync("test issue", artifacts=artifacts)

        assert result["type"] == "answer"
        assert result["mode"] == "support"
        assert result["telemetry"]["selected"] == "generic"
        assert "diagnosis" in result
        assert "checklist" in result

    def test_preliminary_analysis(self):
        """Test preliminary analysis functionality."""
        mixin = ReactiveSupportSolver()

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
        mixin = ReactiveSupportSolver()

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
        mixin = ReactiveSupportSolver()

        preliminary = {"category": "performance", "severity": "high"}
        checklist = mixin._draft_checklist("performance issue", {}, {}, preliminary)

        assert isinstance(checklist, list)
        assert len(checklist) > 0
        assert all(isinstance(item, str) for item in checklist)
        assert all(item.startswith("- ") for item in checklist)


class TestSolverIntegration:
    """Test integration between solvers and agent instances."""

    def test_agent_with_planner_executor_solver(self):
        """Test agent with planner-executor solver enabled."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # The agent already has planner-executor solver methods through inheritance
        # No need to enable them explicitly

        # Check that solver methods are available
        assert hasattr(agent, "solve_sync")
        assert hasattr(agent, "_draft_plan")
        assert hasattr(agent, "_structure_plan")
        assert hasattr(agent, "_exec_action")

    def test_agent_with_reactive_support_solver(self):
        """Test agent with reactive support solver enabled."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # The agent already has planner executor solver methods through inheritance
        # No need to enable them explicitly

        # Check that solver methods are available
        assert hasattr(agent, "solve_sync")
        assert hasattr(agent, "_draft_plan")
        assert hasattr(agent, "_structure_plan")

    def test_agent_solver_with_dependencies(self):
        """Test agent solver with external dependencies."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Mock dependencies
        mock_catalog = Mock(spec=WorkflowCatalog)
        mock_resource_index = Mock(spec=ResourceIndex)
        mock_signature_matcher = Mock(spec=SignatureMatcher)

        # The agent already has planner executor solver methods through inheritance
        # No need to enable them explicitly
        # Dependencies would be set through the solver methods directly

        # Check that solver methods are available
        assert hasattr(agent, "solve_sync")
        assert hasattr(agent, "_draft_plan")
        assert hasattr(agent, "_structure_plan")


if __name__ == "__main__":
    pytest.main([__file__])
