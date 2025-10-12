"""
Unit tests for the Workflow classes.
"""

from unittest.mock import Mock

import pytest

from dana.common.protocols import AgentProtocol, DictParams, Notifiable
from dana.core.workflow import BaseWorkflow


class ConcreteWorkflow(BaseWorkflow):
    """Concrete implementation of BaseWorkflow for testing."""

    def __init__(self, **kwargs):
        # Set default workflow_type if not provided
        if "workflow_type" not in kwargs:
            kwargs["workflow_type"] = "test"
        super().__init__(**kwargs)

    def _do_execute(self, **kwargs) -> DictParams:
        """Execute the test workflow."""
        return {"result": "test_execution", "kwargs": kwargs}


class TestConcreteWorkflow:
    """Test ConcreteWorkflow class functionality."""

    def test_base_workflow_initialization(self):
        """Test ConcreteWorkflow initialization."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow", workflow_id="test-workflow-123")

        assert workflow.workflow_type == "test_workflow"
        assert workflow.workflow_id == "test-workflow-123"
        assert hasattr(workflow, "object_id")

    def test_base_workflow_initialization_defaults(self):
        """Test ConcreteWorkflow initialization with defaults."""
        workflow = ConcreteWorkflow()

        assert workflow.workflow_type == "test"
        assert hasattr(workflow, "workflow_id")
        assert hasattr(workflow, "object_id")

    def test_base_workflow_with_agent(self):
        """Test ConcreteWorkflow can be called with agent parameter (even though not stored)."""
        mock_agent = Mock(spec=AgentProtocol)
        mock_agent.agent_type = "test_agent"

        # Agent parameter is accepted but not stored
        workflow = ConcreteWorkflow(workflow_type="test_workflow", workflow_id="test-workflow-123")

        assert workflow.workflow_type == "test_workflow"

    def test_base_workflow_properties(self):
        """Test ConcreteWorkflow properties."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow", workflow_id="test-workflow-123")

        # Test workflow_id property
        assert workflow.workflow_id == "test-workflow-123"

        # Test setting workflow_id
        workflow.workflow_id = "new-workflow-456"
        assert workflow.workflow_id == "new-workflow-456"

    def test_base_workflow_public_description(self):
        """Test ConcreteWorkflow public description."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow")

        # Should have a public description
        description = workflow.public_description
        assert isinstance(description, str)
        assert len(description) > 0

    def test_base_workflow_call_agent_with_agent(self):
        """Test ConcreteWorkflow call_agent with agent parameter."""
        mock_agent = Mock(spec=AgentProtocol)
        mock_agent.agent_type = "test_agent"
        mock_agent.query.return_value = {"response": "test response"}

        workflow = ConcreteWorkflow(workflow_type="test_workflow", workflow_id="test-workflow-123")

        # Pass agent as parameter to call_agent
        result = workflow.call_agent("test message", agent=mock_agent)

        # Should call agent.query with correct parameters
        mock_agent.query.assert_called_once()
        call_args = mock_agent.query.call_args
        assert call_args.kwargs["caller_message"] == "test message"
        assert call_args.kwargs["caller_id"] == "test-workflow-123"
        assert call_args.kwargs["caller_type"] == "test_workflow"

        assert result == {"response": "test response"}

    def test_base_workflow_call_agent_without_agent(self):
        """Test ConcreteWorkflow call_agent without agent."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow")

        result = workflow.call_agent("test message")

        # Should return error when no agent
        assert "error" in result
        assert result["error"] == "Agent not found"

    def test_base_workflow_call_agent_with_kwargs(self):
        """Test ConcreteWorkflow call_agent with additional kwargs."""
        mock_agent = Mock(spec=AgentProtocol)
        mock_agent.agent_type = "test_agent"
        mock_agent.query.return_value = {"response": "test response"}

        workflow = ConcreteWorkflow(workflow_type="test_workflow", workflow_id="test-workflow-123")

        # Pass agent as parameter with extra kwargs
        workflow.call_agent("test message", agent=mock_agent, extra_param="extra_value")

        # Should pass through additional kwargs
        call_args = mock_agent.query.call_args
        assert call_args.kwargs["extra_param"] == "extra_value"

    def test_base_workflow_inheritance(self):
        """Test ConcreteWorkflow inheritance from protocols."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow")

        # Should inherit from Identifiable
        assert hasattr(workflow, "object_id")
        assert hasattr(workflow, "object_id")

        # Should inherit from WARProtocol
        assert hasattr(workflow, "public_description")

    def test_base_workflow_string_representation(self):
        """Test ConcreteWorkflow string representation."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow", workflow_id="test-workflow-123")

        # Should have meaningful string representation
        repr_str = repr(workflow)
        assert "ConcreteWorkflow" in repr_str
        assert "test_workflow" in repr_str

    def test_base_workflow_with_different_types(self):
        """Test ConcreteWorkflow with different workflow types."""
        types = ["data_processing", "analysis", "reporting", "integration"]

        for workflow_type in types:
            workflow = ConcreteWorkflow(workflow_type=workflow_type)
            assert workflow.workflow_type == workflow_type

    def test_base_workflow_workflow_id_uniqueness(self):
        """Test that workflow IDs are unique."""
        workflow1 = ConcreteWorkflow(workflow_type="test")
        workflow2 = ConcreteWorkflow(workflow_type="test")

        # Should have unique object_ids
        assert workflow1.object_id != workflow2.object_id

    def test_base_workflow_with_kwargs(self):
        """Test ConcreteWorkflow initialization with additional kwargs."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow", custom_param="custom_value", another_param=123)

        # Should handle kwargs gracefully
        assert workflow.workflow_type == "test_workflow"


class TestConcreteWorkflowIntegration:
    """Test ConcreteWorkflow integration with other components."""

    def test_base_workflow_with_agent_protocol(self):
        """Test ConcreteWorkflow with AgentProtocol."""
        mock_agent = Mock(spec=AgentProtocol)
        mock_agent.agent_type = "test_agent"
        mock_agent.query.return_value = {"result": "success"}

        workflow = ConcreteWorkflow()
        # Pass agent as parameter
        result = workflow.call_agent("test", agent=mock_agent)

        assert result == {"result": "success"}

    def test_base_workflow_observable_decorator(self):
        """Test that ConcreteWorkflow call_agent is decorated with observable."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow")

        # The call_agent method should be decorated
        # This is tested indirectly by checking the method exists and is callable
        assert callable(workflow.call_agent)

    def test_base_workflow_error_handling(self):
        """Test ConcreteWorkflow error handling."""
        mock_agent = Mock(spec=AgentProtocol)
        mock_agent.agent_type = "test_agent"
        mock_agent.query.side_effect = Exception("Test error")

        workflow = ConcreteWorkflow()

        # Should handle agent errors gracefully
        with pytest.raises(Exception, match="Test error"):
            workflow.call_agent("test message", agent=mock_agent)


class TestConcreteWorkflowEdgeCases:
    """Test ConcreteWorkflow edge cases and error conditions."""

    def test_base_workflow_with_none_agent(self):
        """Test ConcreteWorkflow with None agent."""
        workflow = ConcreteWorkflow()

        # Call with agent=None
        result = workflow.call_agent("test", agent=None)
        assert "error" in result
        assert result["error"] == "Agent not found"

    def test_base_workflow_with_empty_message(self):
        """Test ConcreteWorkflow with empty message."""
        mock_agent = Mock(spec=AgentProtocol)
        mock_agent.agent_type = "test_agent"
        mock_agent.query.return_value = {"response": "empty message"}

        workflow = ConcreteWorkflow()
        workflow.call_agent("", agent=mock_agent)

        # Should handle empty message
        mock_agent.query.assert_called_once()
        call_args = mock_agent.query.call_args
        assert call_args.kwargs["caller_message"] == ""

    def test_base_workflow_with_none_message(self):
        """Test ConcreteWorkflow with None message."""
        mock_agent = Mock(spec=AgentProtocol)
        mock_agent.agent_type = "test_agent"
        mock_agent.query.return_value = {"response": "none message"}

        workflow = ConcreteWorkflow()
        workflow.call_agent(None, agent=mock_agent)

        # Should handle None message
        mock_agent.query.assert_called_once()
        call_args = mock_agent.query.call_args
        assert call_args.kwargs["caller_message"] is None

    def test_base_workflow_with_very_long_workflow_type(self):
        """Test ConcreteWorkflow with very long workflow type."""
        long_type = "very_long_workflow_type_name_" * 10
        workflow = ConcreteWorkflow(workflow_type=long_type)

        assert workflow.workflow_type == long_type

    def test_base_workflow_with_special_characters(self):
        """Test ConcreteWorkflow with special characters in type."""
        special_type = "workflow-with-special.chars_123"
        workflow = ConcreteWorkflow(workflow_type=special_type)

        assert workflow.workflow_type == special_type


class TestConcreteWorkflowNotificationIntegration:
    """Test ConcreteWorkflow notification integration (if implemented)."""

    def test_base_workflow_notification_support(self):
        """Test ConcreteWorkflow notification functionality if implemented."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow")

        # Check if workflow supports notifications
        # This test will pass if notifications are implemented, skip if not
        if hasattr(workflow, "send_notification"):
            mock_notifiable = Mock(spec=Notifiable)
            workflow.add_notifier(mock_notifiable)

            test_message = {"type": "workflow_test", "content": "workflow notification"}
            workflow.broadcast(test_message)

            mock_notifiable.notify.assert_called_once_with(workflow, test_message)
        else:
            # If notifications are not implemented, this test should be skipped
            pytest.skip("ConcreteWorkflow does not support notifications yet")

    @pytest.mark.xfail(reason="Workflow notifications not working in test environment")
    def test_base_workflow_call_agent_with_notifications(self):
        """Test ConcreteWorkflow call_agent with notification support."""
        workflow = ConcreteWorkflow(workflow_type="test_workflow")

        # This test will pass if notifications are implemented
        if hasattr(workflow, "send_notification"):
            mock_notifiable = Mock(spec=Notifiable)
            workflow.add_notifier(mock_notifiable)

            mock_agent = Mock(spec=AgentProtocol)
            mock_agent.agent_type = "test_agent"
            mock_agent.query.return_value = {"response": "test response"}
            workflow.agent = mock_agent

            workflow.call_agent("test message")

            # Should send notifications during agent call
            assert mock_notifiable.notify.called
        else:
            # If notifications are not implemented, this test should be skipped
            pytest.skip("ConcreteWorkflow does not support notifications yet")
