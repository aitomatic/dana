"""
Unit tests for the Agent classes with updated API.
"""

from unittest.mock import Mock, patch

import pytest

from adana.common.protocols import DictParams, Notifiable
from adana.core.agent import BaseAgent, BaseSTARAgent, STARAgent
from adana.core.agent.components.state import State


class TestBaseAgent:
    """Test BaseAgent class functionality."""

    def test_base_agent_initialization(self):
        """Test BaseAgent initialization."""
        agent = BaseAgent(agent_type="test_agent", agent_id="test-agent-123")

        assert agent.agent_type == "test_agent"
        assert agent.agent_id == "test-agent-123"
        assert hasattr(agent, "_created_at")
        assert hasattr(agent, "_resources")
        assert hasattr(agent, "_agents")
        assert hasattr(agent, "_workflows")

    def test_base_agent_properties(self):
        """Test BaseAgent properties."""
        agent = BaseAgent(agent_type="test_agent", agent_id="test-agent-123")

        assert agent.system_prompt == "You are a test_agent agent."
        assert "test_agent agent with ID test-agent-123" in agent.private_identity
        assert agent.created_at is not None
        assert agent.get_basic_state()["agent_type"] == "test_agent"

    def test_base_agent_notification_integration(self):
        """Test BaseAgent notification functionality."""
        agent = BaseAgent(agent_type="test_agent", agent_id="test-agent-123")

        # Test that agent inherits from Notifier
        assert hasattr(agent, "_notifiables")
        assert hasattr(agent, "broadcast")
        assert hasattr(agent, "add_notifier")
        assert hasattr(agent, "remove_notifiable")

        # Test notification sending
        mock_notifiable = Mock(spec=Notifiable)
        agent.add_notifier(mock_notifiable)

        test_message = {"type": "test", "content": "hello"}
        agent.broadcast(test_message)

        mock_notifiable.notify.assert_called_once_with(agent, test_message)

    def test_base_agent_query(self):
        """Test BaseAgent default query implementation."""
        agent = BaseAgent(agent_type="test_agent")
        result = agent.query(test_param="value")

        assert isinstance(result, dict)
        assert "response" in result
        assert "test_agent agent" in result["response"]

    def test_base_agent_resource_management(self):
        """Test BaseAgent resource management."""
        from adana.core.resource import BaseResource

        agent = BaseAgent(agent_type="test_agent")
        resource = BaseResource(resource_type="test", resource_id="test-resource-123")

        # Test fluent interface
        agent_with_resource = agent.with_resources(resource)
        assert agent_with_resource is agent  # Should return self
        assert len(agent.available_resources) == 1
        assert agent.available_resources[0] == resource

        # Test individual management
        agent.add_resource(resource)
        assert len(agent.available_resources) == 2

        # Test removal
        removed = agent.remove_resource("test-resource-123")
        assert removed is True
        assert len(agent.available_resources) == 1

    def test_base_agent_agent_management(self):
        """Test BaseAgent agent management."""
        from adana.core.agent import BaseAgent

        agent = BaseAgent(agent_type="test_agent")
        other_agent = BaseAgent(agent_type="other_agent", agent_id="other-agent-456")

        # Test fluent interface
        agent_with_agents = agent.with_agents(other_agent)
        assert agent_with_agents is agent  # Should return self
        assert len(agent.available_agents) == 1
        assert agent.available_agents[0] == other_agent

        # Test individual management
        agent.add_agent(other_agent)
        assert len(agent.available_agents) == 2

        # Test removal
        removed = agent.remove_agent("other-agent-456")
        assert removed is True
        assert len(agent.available_agents) == 1

    def test_base_agent_workflow_management(self):
        """Test BaseAgent workflow management."""
        from adana.lib.workflows import GoogleLookupWorkflow

        agent = BaseAgent(agent_type="test_agent")
        workflow = GoogleLookupWorkflow(workflow_id="test-workflow-123")

        # Test fluent interface
        agent_with_workflows = agent.with_workflows(workflow)
        assert agent_with_workflows is agent  # Should return self
        assert len(agent.available_workflows) == 1
        assert agent.available_workflows[0] == workflow

        # Test individual management
        agent.add_workflow(workflow)
        assert len(agent.available_workflows) == 2

        # Test removal
        removed = agent.remove_workflow(workflow.object_id)
        assert removed is True
        assert len(agent.available_workflows) == 1

    def test_base_agent_string_representations(self):
        """Test BaseAgent string representations."""
        agent = BaseAgent(agent_type="test_agent", agent_id="test-agent-123")

        str_repr = str(agent)
        assert "BaseAgent" in str_repr
        assert "test_agent" in str_repr

        repr_str = repr(agent)
        assert "BaseAgent" in repr_str
        assert "test_agent" in repr_str
        assert "test-agent-123" in repr_str


class TestBaseSTARAgent:
    """Test BaseSTARAgent class functionality."""

    def test_base_star_agent_abstract_methods(self):
        """Test that BaseSTARAgent has abstract STAR methods."""
        # Test that BaseSTARAgent has the required abstract methods
        assert hasattr(BaseSTARAgent, "_see")
        assert hasattr(BaseSTARAgent, "_think")
        assert hasattr(BaseSTARAgent, "_act")
        assert hasattr(BaseSTARAgent, "_reflect")
        assert hasattr(BaseSTARAgent, "_mark_star_loop_exit")
        assert hasattr(BaseSTARAgent, "_do_exit_star_loop")

    def test_base_star_agent_inheritance(self):
        """Test that BaseSTARAgent inherits from BaseAgent."""
        # Test that BaseSTARAgent has all BaseAgent functionality
        assert hasattr(BaseSTARAgent, "with_resources")
        assert hasattr(BaseSTARAgent, "with_agents")
        assert hasattr(BaseSTARAgent, "with_workflows")
        assert hasattr(BaseSTARAgent, "available_resources")
        assert hasattr(BaseSTARAgent, "available_agents")
        assert hasattr(BaseSTARAgent, "available_workflows")
        assert hasattr(BaseSTARAgent, "system_prompt")
        assert hasattr(BaseSTARAgent, "private_identity")
        assert hasattr(BaseSTARAgent, "query")

    def test_base_star_agent_cannot_instantiate(self):
        """Test that BaseSTARAgent cannot be instantiated directly (it's abstract)."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class BaseSTARAgent"):
            BaseSTARAgent(agent_type="star_agent", agent_id="star-agent-123")

    def test_base_star_agent_notification_integration(self):
        """Test BaseSTARAgent notification functionality."""

        # Create a concrete implementation to test
        class TestSTARAgent(BaseSTARAgent):
            @property
            def public_description(self) -> str:
                return "Test STAR Agent for testing purposes"
            
            def _see(self, trace_inputs: DictParams) -> DictParams:
                return trace_inputs

            def _think(self, trace_percepts: DictParams) -> DictParams:
                return trace_percepts

            def _act(self, trace_thoughts: DictParams) -> DictParams:
                return trace_thoughts

            def _reflect(self, trace_outputs: DictParams) -> DictParams:
                return trace_outputs

        agent = TestSTARAgent(agent_type="test_star", agent_id="test-star-123")

        # Test that agent inherits notification functionality
        assert hasattr(agent, "_notifiables")
        assert hasattr(agent, "broadcast")

        # Test notification sending
        mock_notifiable = Mock(spec=Notifiable)
        agent.add_notifier(mock_notifiable)

        test_message = {"type": "star_test", "content": "STAR notification"}
        agent.broadcast(test_message)

        mock_notifiable.notify.assert_called_once_with(agent, test_message)


class TestState:
    """Test State dataclass."""

    def test_state_initialization(self):
        """Verify State initializes default attribute types correctly when given a mock agent."""
        from unittest.mock import Mock

        mock_agent = Mock()
        mock_agent.object_id = "test-agent-123"
        mock_agent.agent_type = "test_agent"
        mock_agent.available_resources = []
        mock_agent._timeline = Mock()
        mock_agent._timeline.get_entry_count.return_value = 0

        state = State(_agent=mock_agent)

        assert isinstance(state.session_metadata, dict)
        assert isinstance(state.user_preferences, dict)
        assert isinstance(state.task_state, dict)
        assert isinstance(state.created_at, str)
        assert isinstance(state.last_updated, str)


class TestSTARAgent:
    """Test STARAgent class functionality."""

    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        with patch("adana.core.agent.star_agent.LLM"):
            return STARAgent(agent_type="test_agent", auto_register=False)

    def test_agent_initialization(self):
        """Test agent initialization."""
        with patch("adana.core.agent.star_agent.LLM"):
            agent = STARAgent(agent_type="test_agent", auto_register=False)

        assert agent.agent_type == "test_agent"
        assert hasattr(agent, "_timeline")
        assert hasattr(agent, "_state")
        assert hasattr(agent, "_prompt_engineer")

    def test_agent_initialization_with_class_constants(self):
        """Test agent initialization using class constants."""

        class TestSTARAgent(STARAgent):
            pass

        with patch("adana.core.agent.star_agent.LLM"):
            agent = TestSTARAgent(agent_type="test", auto_register=False)

        assert agent.agent_type == "test"

    def test_list_resources(self, agent):
        """Test listing resources (discovery-based)."""
        resources = agent.available_resources
        assert isinstance(resources, list)
        # Should have at least the default ToDoResource
        assert len(resources) >= 1
        # Check that we have a ToDoResource
        assert any(resource.resource_type == "todo" for resource in resources)

    def test_list_agents(self, agent):
        """Test listing agents from registry."""
        agents = agent.available_agents
        assert isinstance(agents, list)
        # Since agent is created with auto_register=False, it should have no registry
        # or return empty list when registry is not available
        # The test should be tolerant of other agents in global registry
        if agent._registry is None:
            assert agents == []
        else:
            # If registry exists, agent should not include itself
            assert agent.object_id not in [a.object_id for a in agents]

    def test_get_state(self, agent):
        """Test getting agent state."""
        state = agent.get_state()

        assert isinstance(state, dict)
        assert "object_id" in state
        assert "agent_type" in state
        assert "created_at" in state
        assert "last_updated" in state
        assert state["agent_type"] == "test_agent"

    def test_repr_representation(self, agent):
        """Test agent repr representation."""
        repr_str = repr(agent)
        assert "STARAgent" in repr_str
        assert "test_agent" in repr_str

    def test_star_agent_notification_integration(self, agent):
        """Test STARAgent notification functionality."""
        # Test that agent inherits notification functionality
        assert hasattr(agent, "_notifiables")
        assert hasattr(agent, "broadcast")
        assert hasattr(agent, "add_notifier")
        assert hasattr(agent, "remove_notifiable")

        # Test notification sending
        mock_notifiable = Mock(spec=Notifiable)
        agent.add_notifier(mock_notifiable)

        test_message = {"type": "star_agent_test", "content": "STARAgent notification"}
        agent.broadcast(test_message)

        mock_notifiable.notify.assert_called_once_with(agent, test_message)

    @pytest.mark.xfail(reason="STAR method notifications not working in test environment")
    def test_star_agent_star_methods_send_notifications(self, agent):
        """Test that STAR methods send notifications."""
        mock_notifiable = Mock(spec=Notifiable)
        agent.add_notifier(mock_notifiable)

        # Test that each STAR method sends notifications
        # Use proper input that won't trigger exit condition
        test_input = {"caller_message": "test message", "caller_type": "human", "caller_id": "user"}

        # Test _see method
        agent._see(test_input)
        assert mock_notifiable.notify.call_count >= 1

        # Reset for next test
        mock_notifiable.reset_mock()

        # Test _think method
        agent._think(test_input)
        assert mock_notifiable.notify.call_count >= 1

        # Reset for next test
        mock_notifiable.reset_mock()

        # Test _act method
        agent._act(test_input)
        assert mock_notifiable.notify.call_count >= 1

        # Reset for next test
        mock_notifiable.reset_mock()

        # Test _reflect method
        agent._reflect(test_input)
        assert mock_notifiable.notify.call_count >= 1
