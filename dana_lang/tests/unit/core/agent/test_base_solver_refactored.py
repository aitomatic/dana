"""
Tests for the refactored BaseSolver.

This module tests the BaseSolver after the resource handling functionality
was extracted into ResourceHandlingMixin.
"""

from unittest.mock import Mock, patch

import pytest

from dana_lang.core.agent.solvers.base import BaseSolver, SolverResponse
from dana_lang.core.lang.sandbox_context import SandboxContext
from dana_lang.core.workflow.workflow_system import WorkflowInstance


class ConcreteSolver(BaseSolver):
    """Concrete implementation of BaseSolver for testing."""

    def solve_sync(self, problem_or_workflow, artifacts=None, sandbox_context=None, **kwargs):
        """Concrete implementation of solve_sync."""
        return {"result": "test"}


class TestBaseSolverRefactored:
    """Test the refactored BaseSolver functionality."""

    def create_mock_agent(self):
        """Create a mock agent for testing."""
        mock_agent = Mock()
        mock_agent.llm_resource = None
        # Ensure no state is set initially
        if hasattr(mock_agent, "state"):
            delattr(mock_agent, "state")
        return mock_agent

    def test_base_solver_initialization(self):
        """Test that BaseSolver initializes correctly after refactoring."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        assert solver.agent == mock_agent
        assert hasattr(solver, "llm_resource")

    def test_llm_resource_property(self):
        """Test LLM resource property getter and setter."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Test getter
        assert solver.llm_resource is not None

        # Test setter
        new_llm = Mock()
        solver.llm_resource = new_llm
        assert solver.llm_resource == new_llm

    def test_solve_sync_abstract_method(self):
        """Test that solve_sync is properly abstract."""
        mock_agent = self.create_mock_agent()

        # BaseSolver should not be instantiable directly
        with pytest.raises(TypeError):
            BaseSolver(mock_agent).solve_sync("test")

    def test_plan_sync_default_implementation(self):
        """Test that plan_sync returns None by default."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        result = solver.plan_sync("test problem")
        assert result is None

    def test_run_workflow_instance_with_run_method(self):
        """Test workflow execution with run() method."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock workflow with run method
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_workflow.name = "test_workflow"
        # Add the run method to the mock
        mock_workflow.run = Mock(return_value={"output": "test_result"})

        mock_context = Mock(spec=SandboxContext)

        result = solver._run_workflow_instance(mock_workflow, mock_context)

        assert result["status"] == "ok"
        assert result["output"] == {"output": "test_result"}
        assert result["name"] == "test_workflow"
        mock_workflow.run.assert_called_once_with(context=mock_context)

    def test_run_workflow_instance_with_execute_method(self):
        """Test workflow execution with execute() method."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock workflow with execute method (no run method)
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_workflow.name = "test_workflow"
        del mock_workflow.run  # Remove run method
        mock_workflow.execute.return_value = {"output": "test_result"}

        mock_context = Mock(spec=SandboxContext)

        result = solver._run_workflow_instance(mock_workflow, mock_context)

        assert result["status"] == "ok"
        assert result["output"] == {"output": "test_result"}
        assert result["name"] == "test_workflow"
        mock_workflow.execute.assert_called_once_with(context=mock_context)

    def test_run_workflow_instance_no_methods(self):
        """Test workflow execution with no run or execute methods."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock workflow with no execution methods
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_workflow.name = "test_workflow"
        del mock_workflow.run
        del mock_workflow.execute

        mock_context = Mock(spec=SandboxContext)

        result = solver._run_workflow_instance(mock_workflow, mock_context)

        assert result["status"] == "ok"  # Status is ok, error is in output
        assert "no run/execute" in result["output"]["message"]
        assert result["name"] == "test_workflow"

    def test_run_workflow_instance_exception(self):
        """Test workflow execution with exception."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock workflow that raises exception
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_workflow.name = "test_workflow"
        # Add the run method to the mock
        mock_workflow.run = Mock(side_effect=Exception("Workflow failed"))

        mock_context = Mock(spec=SandboxContext)

        result = solver._run_workflow_instance(mock_workflow, mock_context)

        assert result["status"] == "error"
        assert "Workflow failed" in result["message"]
        assert result["name"] == "test_workflow"

    def test_attach_resource_pack(self):
        """Test resource pack attachment."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock resource registry
        mock_registry = Mock()
        mock_registry.pack_resources_for_llm.return_value = {"resource1": "data1"}

        entities = {"user": "test"}
        artifacts = {}

        solver._attach_resource_pack(mock_registry, entities, artifacts)

        assert "_resources" in artifacts
        assert artifacts["_resources"] == {"resource1": "data1"}
        mock_registry.pack_resources_for_llm.assert_called_once_with(entities)

    def test_attach_resource_pack_exception(self):
        """Test resource pack attachment with exception."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock resource registry that raises exception
        mock_registry = Mock()
        mock_registry.pack_resources_for_llm.side_effect = Exception("Registry error")

        entities = {"user": "test"}
        artifacts = {}

        solver._attach_resource_pack(mock_registry, entities, artifacts)

        assert "_resources" in artifacts
        assert artifacts["_resources"] == {}

    def test_inject_dependencies_with_kwargs(self):
        """Test dependency injection with provided kwargs."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        mock_wc = Mock()
        mock_ri = Mock()
        mock_sig = Mock()

        wc, ri, sig = solver._inject_dependencies(workflow_registry=mock_wc, resource_registry=mock_ri, signature_matcher=mock_sig)

        assert wc == mock_wc
        assert ri == mock_ri
        assert sig == mock_sig

    def test_inject_dependencies_fallback_to_global(self):
        """Test dependency injection fallback to global registries."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        with patch("dana.registry.GLOBAL_REGISTRY") as mock_global:
            mock_global.workflows = Mock()
            mock_global.resources = Mock()

            wc, ri, sig = solver._inject_dependencies()

            assert wc == mock_global.workflows
            assert ri == mock_global.resources
            assert sig is None

    def test_debug_report_available_dependencies(self):
        """Test debug reporting of available dependencies."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock workflow registry
        mock_wc = Mock()
        mock_wc.get_available_workflows.return_value = {"workflow1": Mock(workflow_type="test", status="active")}

        # Mock resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"resource1": Mock(kind="test", status="active")}

        # Should not raise exception
        solver._debug_report_available_dependencies(mock_wc, mock_ri)

    def test_get_dependency_summary(self):
        """Test dependency summary generation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock dependencies
        mock_wc = Mock()
        mock_wc.get_available_workflows.return_value = {"workflow1": Mock(workflow_type="test", status="active", instance_id="wf1")}

        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"resource1": Mock(kind="test", status="active", instance_id="res1")}

        with patch.object(solver, "_inject_dependencies", return_value=(mock_wc, mock_ri, None)):
            summary = solver.get_dependency_summary()

            assert summary["resources"]["count"] == 1
            assert summary["workflows"]["count"] == 1
            assert "workflow1" in summary["workflows"]["names"]
            assert "resource1" in summary["resources"]["names"]

    def test_handle_direct_workflow_execution(self):
        """Test direct workflow execution handling."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock workflow instance
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_workflow.name = "test_workflow"

        mock_context = Mock(spec=SandboxContext)
        artifacts = {}

        with patch.object(solver, "_run_workflow_instance", return_value={"status": "ok", "output": "result"}):
            result = solver._handle_direct_workflow_execution(mock_workflow, mock_context, artifacts)

            assert result["type"] == "answer"
            assert result["mode"] == "workflow"
            assert result["result"]["status"] == "ok"

    def test_handle_direct_workflow_execution_with_string(self):
        """Test direct workflow execution with string input."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        mock_context = Mock(spec=SandboxContext)
        artifacts = {}

        result = solver._handle_direct_workflow_execution("not a workflow", mock_context, artifacts)

        assert result is None

    def test_match_known_workflow(self):
        """Test known workflow matching."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock workflow registry
        mock_wc = Mock()
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_wc.match_workflow_for_llm.return_value = (0.9, mock_workflow, {})

        entities = {"user": "test"}
        score, wf = solver._match_known_workflow("test query", entities, mock_wc, 0.8)

        assert score == 0.9
        assert wf == mock_workflow

    def test_match_known_workflow_no_registry(self):
        """Test known workflow matching with no registry."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        entities = {"user": "test"}
        score, wf = solver._match_known_workflow("test query", entities, None, 0.8)

        assert score == 0.0
        assert wf is None

    def test_match_known_workflow_low_score(self):
        """Test known workflow matching with low score."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Mock workflow registry
        mock_wc = Mock()
        mock_workflow = Mock(spec=WorkflowInstance)
        mock_wc.match_workflow_for_llm.return_value = (0.5, mock_workflow, {})

        entities = {"user": "test"}
        score, wf = solver._match_known_workflow("test query", entities, mock_wc, 0.8)

        assert score == 0.5
        assert wf is None  # Below threshold

    def test_initialize_solver_state(self):
        """Test solver state initialization."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {}
        state = solver._initialize_solver_state(artifacts, "_test_state")

        assert "_test_state" in artifacts
        assert state is artifacts["_test_state"]
        assert isinstance(state, dict)

    def test_extract_entities(self):
        """Test entity extraction from artifacts."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {"_entities": {"user": "test", "domain": "testing"}}
        entities = solver._extract_entities(artifacts)

        assert entities == {"user": "test", "domain": "testing"}

    def test_extract_entities_empty(self):
        """Test entity extraction with empty artifacts."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {}
        entities = solver._extract_entities(artifacts)

        assert entities == {}

    def test_create_ask_response(self):
        """Test ask response creation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        response = solver._create_ask_response("Test message")

        assert response["type"] == "ask"
        assert response["message"] == "Test message"

    def test_create_ask_response_with_missing(self):
        """Test ask response creation with missing items."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        response = solver._create_ask_response("Test message", missing=["item1", "item2"])

        assert response["type"] == "ask"
        assert response["message"] == "Test message"
        assert response["missing"] == ["item1", "item2"]

    def test_create_answer_response(self):
        """Test answer response creation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {"test": "data"}
        response = solver._create_answer_response("test_mode", artifacts, "test_selection")

        assert response["type"] == "answer"
        assert response["mode"] == "test_mode"
        assert response["artifacts"] == artifacts

    def test_create_solver_response(self):
        """Test SolverResponse creation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        response = solver._create_solver_response("Test content", "answer", {"key": "value"})

        assert isinstance(response, SolverResponse)
        assert response.content == "Test content"
        assert response.response_type == "answer"
        assert response.metadata == {"key": "value"}

    def test_create_solver_ask_response(self):
        """Test SolverResponse ask creation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        response = solver._create_solver_ask_response("Test message", ["item1", "item2"])

        assert isinstance(response, SolverResponse)
        assert response.content == "Test message"
        assert response.response_type == "ask"
        assert response.metadata["missing"] == ["item1", "item2"]

    def test_create_solver_answer_response(self):
        """Test SolverResponse answer creation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        response = solver._create_solver_answer_response("Test content", "test_mode")

        assert isinstance(response, SolverResponse)
        assert response.content == "Test content"
        assert response.response_type == "answer"
        assert response.metadata["mode"] == "test_mode"

    def test_create_solver_error_response(self):
        """Test SolverResponse error creation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        error = Exception("Test error")
        response = solver._create_solver_error_response("Error message", error)

        assert isinstance(response, SolverResponse)
        assert response.content == "Error message"
        assert response.response_type == "error"
        assert response.metadata["error"] == "Test error"
        assert response.metadata["error_type"] == "Exception"

    def test_check_recursion_limit(self):
        """Test recursion limit checking."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {}
        is_limit, depth = solver._check_recursion_limit(artifacts, max_depth=3)

        assert not is_limit
        assert depth == 1
        assert artifacts["_solver_state"]["recursion_depth"] == 1

    def test_check_recursion_limit_exceeded(self):
        """Test recursion limit when exceeded."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {"_solver_state": {"recursion_depth": 3}}
        is_limit, depth = solver._check_recursion_limit(artifacts, max_depth=3)

        assert is_limit
        assert depth == 3

    def test_create_recursion_limit_response(self):
        """Test recursion limit response creation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        response = solver._create_recursion_limit_response("test problem", 3, "test_mode")

        assert isinstance(response, SolverResponse)
        assert response.response_type == "error"
        assert "Recursion limit reached" in response.content
        assert response.metadata["recursion_limit"] is True
        assert response.metadata["max_depth"] == 3

    def test_prepare_recursive_call(self):
        """Test recursive call preparation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        parent_artifacts = {"_solver_state": {"goal": "parent_goal"}, "_call_stack": ["step1"]}
        entities = {"user": "test"}

        child_artifacts = solver._prepare_recursive_call("subgoal", parent_artifacts, entities, 2)

        assert child_artifacts["_entities"] == entities
        assert child_artifacts["_solver_state"]["recursion_depth"] == 2
        assert child_artifacts["_parent_goal"] == "parent_goal"
        assert child_artifacts["_call_stack"] == ["step1", "subgoal"]

    def test_validate_llm_resource(self):
        """Test LLM resource validation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Test with LLM resource (BaseSolver creates a default one)
        assert solver._validate_llm_resource()

        # Test with explicitly set Mock
        solver._llm_resource = Mock()
        assert solver._validate_llm_resource()

        # Note: The current implementation always creates a default LLM resource
        # if _llm_resource is None, so _validate_llm_resource() always returns True
        # This is the expected behavior of the current implementation

    def test_create_llm_request(self):
        """Test LLM request creation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        messages = [{"role": "user", "content": "test"}]
        request = solver._create_llm_request(messages, "system prompt")

        assert request.arguments["messages"][0]["role"] == "system"
        assert request.arguments["messages"][0]["content"] == "system prompt"
        assert request.arguments["messages"][1]["role"] == "user"
        assert request.arguments["messages"][1]["content"] == "test"

    def test_extract_llm_response_content(self):
        """Test LLM response content extraction."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Test with successful response
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "Test content"

        content = solver._extract_llm_response_content(mock_response)
        assert content == "Test content"

        # Test with failed response
        mock_response.success = False
        content = solver._extract_llm_response_content(mock_response)
        assert content is None

    def test_log_solver_phase(self):
        """Test solver phase logging."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Should not raise exception
        solver._log_solver_phase("TEST", "Test message", "🔧")

    def test_is_conversation_termination(self):
        """Test conversation termination detection."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Test termination commands
        assert solver._is_conversation_termination("quit")
        assert solver._is_conversation_termination("exit")
        assert solver._is_conversation_termination("bye")
        assert solver._is_conversation_termination("goodbye")
        assert solver._is_conversation_termination("done")

        # Test non-termination commands
        assert not solver._is_conversation_termination("hello")
        assert not solver._is_conversation_termination("help me")
        assert not solver._is_conversation_termination("continue")

    def test_get_conversation_context(self):
        """Test conversation context retrieval."""
        # Test with no agent state
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)
        context = solver._get_conversation_context()
        assert context == ""

        # Test with mock agent state
        mock_agent = self.create_mock_agent()
        mock_timeline = Mock()
        mock_timeline.get_conversation_turns.return_value = "Previous conversation"
        mock_agent.state = Mock()
        mock_agent.state.timeline = mock_timeline
        solver = ConcreteSolver(mock_agent)

        context = solver._get_conversation_context()
        assert "Previous conversation" in context
        assert "Previous conversation context:" in context

    def test_validate_and_prepare_artifacts(self):
        """Test artifact validation and preparation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Test with None artifacts
        artifacts = solver._validate_and_prepare_artifacts(None)
        assert isinstance(artifacts, dict)
        assert "_entities" in artifacts
        assert "_solver_state" in artifacts
        assert "_resources" in artifacts

    def test_validate_and_prepare_artifacts_with_required_fields(self):
        """Test artifact validation with required fields."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {"_entities": {}, "_solver_state": {}}
        result = solver._validate_and_prepare_artifacts(artifacts, ["_entities", "_solver_state"])

        assert result == artifacts

    def test_validate_artifacts_structure(self):
        """Test artifact structure validation."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        # Test valid artifacts
        artifacts = {"_entities": {}, "_solver_state": {}, "_resources": {}}
        is_valid, issues = solver._validate_artifacts_structure(artifacts)
        assert is_valid
        assert len(issues) == 0

        # Test invalid artifacts
        is_valid, issues = solver._validate_artifacts_structure("not a dict")
        assert not is_valid
        assert len(issues) > 0

    def test_sanitize_artifacts(self):
        """Test artifact sanitization."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {
            "key1": "value1",
            "key2": None,
            "key3": "x" * 15000,  # Large value
            123: "numeric_key",  # Non-string key
        }

        sanitized = solver._sanitize_artifacts(artifacts)

        assert "key1" in sanitized
        assert "key2" not in sanitized  # None values removed
        assert "key3" in sanitized
        assert len(sanitized["key3"]) < 15000  # Large value truncated
        assert "123" in sanitized  # Numeric key converted to string

    def test_merge_artifacts_update_strategy(self):
        """Test artifact merging with update strategy."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        base = {"key1": "value1", "key2": "value2"}
        new = {"key2": "new_value2", "key3": "value3"}

        result = solver._merge_artifacts(base, new, "update")

        assert result["key1"] == "value1"
        assert result["key2"] == "new_value2"  # Updated
        assert result["key3"] == "value3"  # Added

    def test_merge_artifacts_deep_merge_strategy(self):
        """Test artifact merging with deep merge strategy."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        base = {"key1": {"nested1": "value1"}, "key2": "value2"}
        new = {"key1": {"nested2": "value2"}, "key3": "value3"}

        result = solver._merge_artifacts(base, new, "deep_merge")

        assert result["key1"]["nested1"] == "value1"  # Preserved
        assert result["key1"]["nested2"] == "value2"  # Added
        assert result["key2"] == "value2"  # Preserved
        assert result["key3"] == "value3"  # Added

    def test_merge_artifacts_preserve_base_strategy(self):
        """Test artifact merging with preserve base strategy."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        base = {"key1": "value1", "key2": "value2"}
        new = {"key2": "new_value2", "key3": "value3"}

        result = solver._merge_artifacts(base, new, "preserve_base")

        assert result["key1"] == "value1"  # Preserved
        assert result["key2"] == "value2"  # Preserved (not updated)
        assert result["key3"] == "value3"  # Added

    def test_extract_artifacts_metadata(self):
        """Test artifact metadata extraction."""
        mock_agent = self.create_mock_agent()
        solver = ConcreteSolver(mock_agent)

        artifacts = {
            "_entities": {"user": "test"},
            "_solver_state": {"goal": "test"},
            "_resources": {"res1": "data1"},
            "other_key": "other_value",
        }

        metadata = solver._extract_artifacts_metadata(artifacts)

        assert metadata["total_keys"] == 4
        assert metadata["has_entities"] is True
        assert metadata["has_solver_state"] is True
        assert metadata["has_resources"] is True
        assert metadata["entity_count"] == 1
        assert "goal" in metadata["state_keys"]
        assert "res1" in metadata["resource_keys"]


if __name__ == "__main__":
    pytest.main([__file__])
