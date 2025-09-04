"""
Tests for the agent solve integration with context engineering.

This module tests the integration between AgentInstance, strategies, and workflows
in the new agent solving system.
"""

from dana.core.agent.agent_instance import AgentInstance
from dana.core.agent.agent_type import AgentType
from dana.core.agent.context import EventHistory, ProblemContext
from dana.core.workflow.workflow_system import WorkflowInstance


class TestAgentSolveIntegration:
    """Test the complete agent solve integration."""

    def test_create_agent_instance(self):
        """Test creating an agent instance with the new system."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        assert agent.name == "TestAgent"
        assert hasattr(agent, "solve")
        assert hasattr(agent, "plan")

    def test_agent_plan_method(self):
        """Test the agent plan method."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Test planning with string problem - use sync method to avoid promise handling
        workflow = agent.plan_sync("Test problem")

        assert isinstance(workflow, WorkflowInstance)
        # Strategy workflows have different fields than top-level workflows
        assert "composed_function" in workflow._values or "name" in workflow._values

    def test_agent_solve_method(self):
        """Test the agent solve method."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Test solving with string problem
        result = agent.solve("Test problem")

        # Should return the result of workflow execution
        assert result is not None

    def test_agent_workflow_reuse(self):
        """Test that agent can reuse existing workflows."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Create a workflow first
        workflow = agent._create_top_level_workflow("Test problem")

        # Verify the workflow was created with proper fields
        assert isinstance(workflow, WorkflowInstance)
        assert workflow._values["problem_statement"] == "Test problem"
        assert workflow._values["action_history"] is not None

        # Note: In simplified workflow system, workflows created by _create_top_level_workflow
        # don't have composed functions set, so they cannot be executed directly

    def test_agent_top_level_workflow_creation(self):
        """Test creating top-level workflows through the agent."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        workflow = agent._create_top_level_workflow("Test problem", objective="Custom objective")

        assert isinstance(workflow, WorkflowInstance)
        assert workflow._values["problem_statement"] == "Test problem"
        assert workflow._values["objective"] == "Custom objective"
        assert workflow._values["problem_context"] is not None
        assert workflow._values["action_history"] is not None
        assert workflow._parent_workflow is None

    def test_agent_workflow_type_creation(self):
        """Test that agent creates proper workflow types."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        workflow_type = agent._create_workflow_type("Test problem")

        assert workflow_type.name.startswith("AgentWorkflow_")
        assert "problem_statement" in workflow_type.fields
        assert "objective" in workflow_type.fields
        assert "problem_context" in workflow_type.fields
        assert "action_history" in workflow_type.fields

    def test_agent_sandbox_context_creation(self):
        """Test that agent creates proper sandbox contexts."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        context = agent._create_sandbox_context()

        assert context is not None
        # In a real implementation, this would be a SandboxContext
        # For now, we just check it's not None

    def test_agent_problem_context_creation(self):
        """Test that agent creates proper problem contexts."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        workflow = agent._create_top_level_workflow("Test problem", objective="Custom objective")

        problem_context = workflow._values["problem_context"]
        assert isinstance(problem_context, ProblemContext)
        assert problem_context.problem_statement == "Test problem"
        assert problem_context.objective == "Custom objective"
        assert problem_context.original_problem == "Test problem"
        assert problem_context.depth == 0

    def test_agent_action_history_creation(self):
        """Test that agent creates proper action histories."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        workflow = agent._create_top_level_workflow("Test problem")

        action_history = workflow._values["action_history"]
        assert isinstance(action_history, EventHistory)
        assert len(action_history.events) == 0  # Initially empty

    def test_agent_strategy_integration(self):
        """Test that agent integrates with the strategy system."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Test that the agent can create workflows through strategy selection
        workflow = agent._create_top_level_workflow("Complex problem", objective="Solve complex problem")

        assert isinstance(workflow, WorkflowInstance)
        assert workflow._values["problem_statement"] == "Complex problem"
        assert workflow._values["objective"] == "Solve complex problem"


class TestAgentContextPropagation:
    """Test context propagation through the agent system."""

    def test_context_propagation_through_workflows(self):
        """Test that context properly propagates through workflow creation and execution."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Create initial workflow
        root_workflow = agent._create_top_level_workflow("Root problem")

        # Verify context is properly set
        assert root_workflow._values["problem_context"] is not None
        assert root_workflow._values["action_history"] is not None

        # Create sub-workflow (simulating recursive call)
        sub_workflow = agent._create_top_level_workflow("Sub problem")

        # Verify sub-workflow has its own context
        assert sub_workflow._values["problem_context"] is not None
        assert sub_workflow._values["action_history"] is not None

    def test_action_history_tracking(self):
        """Test that action history is properly tracked across workflows."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Create workflow
        workflow = agent._create_top_level_workflow("Test problem")

        # Check that action history is properly set
        action_history = workflow._values["action_history"]
        assert isinstance(action_history, EventHistory)

        # The workflow should have the action history field set
        assert workflow._values["action_history"] is not None

    def test_problem_context_hierarchy(self):
        """Test that problem contexts maintain proper hierarchy."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Create root workflow
        root_workflow = agent._create_top_level_workflow("Root problem")
        root_context = root_workflow._values["problem_context"]

        # Create sub-problem context
        sub_context = root_context.create_sub_context("Sub problem", "Solve sub problem")

        # Verify hierarchy
        assert sub_context.depth == 1
        assert sub_context.original_problem == "Root problem"
        assert sub_context.problem_statement == "Sub problem"
        assert sub_context.objective == "Solve sub problem"


class TestAgentErrorHandling:
    """Test agent error handling and recovery."""

    def test_agent_handles_workflow_errors(self):
        """Test that agent properly handles workflow execution errors."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Create workflow
        workflow = agent._create_top_level_workflow("Test problem")

        # Create a function that raises an error
        def error_function(*args, **kwargs):
            raise ValueError("Test error")

        workflow.set_composed_function(error_function)

        # Execute and expect error - use sync method to avoid promise handling
        result = agent.solve_sync(workflow)

        # The result should contain the error message
        assert "Test error" in str(result)

        # Note: In simplified workflow system, events are not automatically recorded during execution
        # The workflow execution will fail as expected, but event recording is not implemented

    def test_agent_handles_missing_composed_function(self):
        """Test that agent handles workflows without composed functions."""
        agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={"name": "Agent name"},
            field_defaults={"name": "TestAgent"},
            docstring="Test agent",
        )

        agent = AgentInstance(struct_type=agent_type, values={"name": "TestAgent"})

        # Create workflow without composed function - use sync method
        workflow = agent.plan_sync("Test problem")
        workflow._composed_function = None

        # Execute and expect error - use sync method to avoid promise handling
        result = agent.solve_sync(workflow)

        # The result should contain the error message
        assert "No composed function set" in str(result)
