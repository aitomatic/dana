"""Tests for ContextEngineerMixin mixin."""

from unittest.mock import Mock, patch

import pytest

from dana.core.agent import ProblemContext
from dana.frameworks.ctxeng.actor_mixin import ContextEngineerMixin


class MockAgent:
    """Mock agent for testing mixin application."""

    def __init__(self, *args, **kwargs):
        # Don't call super() for object to avoid kwargs issues
        self.state = Mock()
        self.state.mind = Mock()
        self.state.mind.form_memory = Mock()


class TestContextEngineerMixin:
    """Test ContextEngineerMixin mixin functionality."""

    @pytest.fixture
    def ctxeng_actor(self):
        """Create a mock agent with ContextEngineerMixin mixin."""

        class TestAgent(MockAgent, ContextEngineerMixin):
            def __init__(self):
                # Initialize MockAgent first
                MockAgent.__init__(self)
                # Then initialize ContextEngineerMixin
                ContextEngineerMixin.__init__(self)

        return TestAgent()

    @pytest.fixture
    def ctxeng_actor_with_config(self):
        """Create a mock agent with ContextEngineerMixin and custom config."""

        class TestAgent(MockAgent, ContextEngineerMixin):
            def __init__(self):
                # Initialize MockAgent first
                MockAgent.__init__(self)
                # Then initialize ContextEngineerMixin with custom config
                ContextEngineerMixin.__init__(self, ctxeng_config={"format_type": "text", "max_tokens": 2000, "relevance_threshold": 0.8})

        return TestAgent()

    def test_initialization(self, ctxeng_actor):
        """Test ContextEngineerMixin initialization."""
        assert hasattr(ctxeng_actor, "_ctxeng_config")
        assert hasattr(ctxeng_actor, "_context_engine")
        assert hasattr(ctxeng_actor, "_template_manager")

        # Check default config
        assert ctxeng_actor._ctxeng_config == {}

        # Check that engines are initialized
        assert ctxeng_actor._context_engine is not None
        assert ctxeng_actor._template_manager is not None

    def test_initialization_with_config(self, ctxeng_actor_with_config):
        """Test ContextEngineerMixin initialization with custom config."""
        assert ctxeng_actor_with_config._ctxeng_config == {"format_type": "text", "max_tokens": 2000, "relevance_threshold": 0.8}

        # Check that engines are initialized with custom config
        assert ctxeng_actor_with_config._context_engine.format_type == "text"
        assert ctxeng_actor_with_config._context_engine.max_tokens == 2000
        assert ctxeng_actor_with_config._context_engine.relevance_threshold == 0.8

    def test_assemble_context(self, ctxeng_actor):
        """Test basic context assembly."""
        with patch.object(ctxeng_actor._context_engine, "assemble") as mock_assemble:
            mock_assemble.return_value = "<context><query>test query</query></context>"

            result = ctxeng_actor.assemble_context("test query", {"key": "value"})

            mock_assemble.assert_called_once_with(query="test query", context={"key": "value"}, template=None)
            assert result == "<context><query>test query</query></context>"

    def test_assemble_context_with_template(self, ctxeng_actor):
        """Test context assembly with specific template."""
        with patch.object(ctxeng_actor._context_engine, "assemble") as mock_assemble:
            mock_assemble.return_value = "<problem_solving><query>solve this</query></problem_solving>"

            result = ctxeng_actor.assemble_context("solve this", template="problem_solving")

            mock_assemble.assert_called_once_with(query="solve this", context=None, template="problem_solving")
            assert result == "<problem_solving><query>solve this</query></problem_solving>"

    def test_assemble_from_agent_state(self, ctxeng_actor):
        """Test context assembly from agent state."""
        mock_agent_state = Mock()

        with patch.object(ctxeng_actor._context_engine, "assemble_from_state") as mock_assemble:
            mock_assemble.return_value = "<context>from state</context>"

            result = ctxeng_actor.assemble_from_agent_state(mock_agent_state, template="analysis")

            mock_assemble.assert_called_once_with(agent_state=mock_agent_state, template="analysis")
            assert result == "<context>from state</context>"

    def test_discover_and_register_resources(self, ctxeng_actor):
        """Test resource discovery and registration."""
        mock_obj = Mock()

        with patch.object(ctxeng_actor._context_engine, "discover_resources") as mock_discover:
            ctxeng_actor.discover_and_register_resources(mock_obj)

            mock_discover.assert_called_once_with(mock_obj)

    def test_add_context_resource(self, ctxeng_actor):
        """Test adding context resources."""
        mock_resource = Mock()

        with patch.object(ctxeng_actor._context_engine, "add_resource") as mock_add:
            ctxeng_actor.add_context_resource("test_resource", mock_resource)

            mock_add.assert_called_once_with("test_resource", mock_resource)

    def test_add_context_workflow(self, ctxeng_actor):
        """Test adding context workflows."""
        mock_workflow = Mock()

        with patch.object(ctxeng_actor._context_engine, "add_workflow") as mock_add:
            ctxeng_actor.add_context_workflow("test_workflow", mock_workflow)

            mock_add.assert_called_once_with("test_workflow", mock_workflow)

    def test_get_available_templates(self, ctxeng_actor):
        """Test getting available templates."""
        with patch.object(ctxeng_actor._template_manager, "list_templates") as mock_list:
            mock_list.return_value = ["general", "problem_solving", "conversation", "analysis"]

            result = ctxeng_actor.get_available_templates()

            mock_list.assert_called_once_with(None)
            assert result == ["general", "problem_solving", "conversation", "analysis"]

    def test_get_available_templates_with_format(self, ctxeng_actor):
        """Test getting available templates with specific format."""
        with patch.object(ctxeng_actor._template_manager, "list_templates") as mock_list:
            mock_list.return_value = ["general", "problem_solving"]

            result = ctxeng_actor.get_available_templates("text")

            mock_list.assert_called_once_with("text")
            assert result == ["general", "problem_solving"]

    def test_get_template_info(self, ctxeng_actor):
        """Test getting template information."""
        mock_template = Mock()
        mock_template.get_required_context.return_value = ["query"]
        mock_template.get_optional_context.return_value = ["context"]

        with patch.object(ctxeng_actor._template_manager, "get_template") as mock_get:
            mock_get.return_value = mock_template

            result = ctxeng_actor.get_template_info("problem_solving", "xml")

            mock_get.assert_called_once_with("problem_solving", "xml")
            assert result == {"name": "problem_solving", "format": "xml", "required_context": ["query"], "optional_context": ["context"]}

    def test_detect_optimal_template(self, ctxeng_actor):
        """Test optimal template detection."""
        with patch.object(ctxeng_actor._context_engine, "_detect_template") as mock_detect:
            mock_detect.return_value = "problem_solving"

            result = ctxeng_actor.detect_optimal_template("solve this problem", {"key": "value"})

            mock_detect.assert_called_once_with("solve this problem", {"key": "value"}, {})
            assert result == "problem_solving"

    def test_assemble_for_problem_solving(self, ctxeng_actor):
        """Test problem-solving context assembly."""
        with patch.object(ctxeng_actor, "assemble_context") as mock_assemble:
            mock_assemble.return_value = "<problem_solving>context</problem_solving>"

            result = ctxeng_actor.assemble_for_problem_solving("solve this", ["resource1", "resource2"])

            mock_assemble.assert_called_once_with(
                query="solve this",
                context={"problem_context": "solve this", "available_resources": ["resource1", "resource2"]},
                template="problem_solving",
            )
            assert result == "<problem_solving>context</problem_solving>"

    def test_assemble_for_problem_solving_with_problem_context(self, ctxeng_actor):
        """Test problem-solving context assembly with ProblemContext."""
        problem_context = ProblemContext("solve this problem")

        with patch.object(ctxeng_actor, "assemble_context") as mock_assemble:
            mock_assemble.return_value = "<problem_solving>context</problem_solving>"

            ctxeng_actor.assemble_for_problem_solving(problem_context)

            mock_assemble.assert_called_once_with(
                query="solve this problem", context={"problem_context": "solve this problem"}, template="problem_solving"
            )

    def test_assemble_for_conversation(self, ctxeng_actor):
        """Test conversation context assembly."""
        with patch.object(ctxeng_actor, "assemble_context") as mock_assemble:
            mock_assemble.return_value = "<conversation>context</conversation>"

            ctxeng_actor.assemble_for_conversation("hello", ["hi", "how are you"])

            mock_assemble.assert_called_once_with(
                query="hello", context={"conversation_history": "hi\nhow are you"}, template="conversation"
            )

    def test_assemble_for_analysis(self, ctxeng_actor):
        """Test analysis context assembly."""
        with patch.object(ctxeng_actor, "assemble_context") as mock_assemble:
            mock_assemble.return_value = "<analysis>context</analysis>"

            ctxeng_actor.assemble_for_analysis("analyze data", {"data": "sample"})

            mock_assemble.assert_called_once_with(query="analyze data", context={"data": "sample"}, template="analysis")

    def test_optimize_context_for_tokens(self, ctxeng_actor):
        """Test token optimization."""
        with patch.object(ctxeng_actor, "assemble_context") as mock_assemble:
            mock_assemble.return_value = "<optimized>context</optimized>"

            ctxeng_actor.optimize_context_for_tokens("query", {"key": "value"}, max_tokens=1000)

            # Should temporarily change max_tokens and then restore it
            assert ctxeng_actor._context_engine.max_tokens == 1500  # Should be restored
            mock_assemble.assert_called_once_with("query", {"key": "value"})

    def test_get_context_engine_state(self, ctxeng_actor):
        """Test getting context engine state."""
        # Mock the context engine attributes
        ctxeng_actor._context_engine._resources = {"resource1": Mock(), "resource2": Mock()}
        ctxeng_actor._context_engine._workflows = {"workflow1": Mock()}

        with patch.object(ctxeng_actor, "get_available_templates") as mock_templates:
            mock_templates.return_value = ["general", "problem_solving"]

            result = ctxeng_actor.get_context_engine_state()

            assert result == {
                "format_type": "xml",
                "max_tokens": 1500,
                "relevance_threshold": 0.7,
                "registered_resources": ["resource1", "resource2"],
                "registered_workflows": ["workflow1"],
                "available_templates": ["general", "problem_solving"],
                "config": {},
            }

    def test_set_context_engine_state(self, ctxeng_actor):
        """Test setting context engine state."""
        engine_state = {"config": {"format_type": "text", "max_tokens": 2000}}

        with patch.object(ctxeng_actor, "_initialize_ctxeng_engine") as mock_init:
            ctxeng_actor.set_context_engine_state(engine_state)

            assert ctxeng_actor._ctxeng_config == {"format_type": "text", "max_tokens": 2000}
            mock_init.assert_called_once()

    def test_sync_with_agent_mind(self, ctxeng_actor):
        """Test synchronization with agent mind."""
        with patch.object(ctxeng_actor, "get_context_engine_state") as mock_get_state:
            mock_get_state.return_value = {"key": "value"}

            ctxeng_actor.sync_with_agent_mind()

            mock_get_state.assert_called_once()
            ctxeng_actor.state.mind.form_memory.assert_called_once_with(
                {"type": "semantic", "key": "ctxeng_engine_state", "value": {"key": "value"}, "importance": 0.8}
            )

    def test_contribute_to_context(self, ctxeng_actor):
        """Test contributing to context."""
        problem_context = ProblemContext("test problem")

        # Mock the context engine attributes
        ctxeng_actor._context_engine._resources = {"resource1": Mock()}

        with patch.object(ctxeng_actor, "get_available_templates") as mock_templates:
            mock_templates.return_value = ["general", "problem_solving"]

            result = ctxeng_actor.contribute_to_context(problem_context, "standard")

            assert result == {
                "context_engine_available": True,
                "format_type": "xml",
                "max_tokens": 1500,
                "registered_resources_count": 1,
                "available_templates": ["general", "problem_solving"],
                "registered_resources": ["resource1"],
            }

    def test_contribute_to_context_minimal(self, ctxeng_actor):
        """Test contributing to context with minimal depth."""
        problem_context = ProblemContext("test problem")

        result = ctxeng_actor.contribute_to_context(problem_context, "minimal")

        assert result == {"context_engine_available": True, "format_type": "xml", "max_tokens": 1500, "registered_resources_count": 0}

    def test_enhance_problem_context(self, ctxeng_actor):
        """Test enhancing problem context."""
        problem_context = ProblemContext("test problem")

        with patch.object(ctxeng_actor, "assemble_for_problem_solving") as mock_assemble:
            mock_assemble.return_value = "<enhanced>context</enhanced>"

            result = ctxeng_actor.enhance_problem_context(problem_context)

            mock_assemble.assert_called_once_with(problem_context)
            assert result is problem_context  # Should return the same instance
            # Check that metadata was added to constraints since ProblemContext doesn't have metadata
            assert problem_context.constraints["context_engine_enhanced"] is True
            assert problem_context.constraints["context_template"] == "problem_solving"
            assert problem_context.constraints["context_length"] == 28  # Length of "<enhanced>context</enhanced>"

    def test_create_context_engine_from_agent(self, ctxeng_actor):
        """Test creating context engine from agent."""
        with patch("dana.frameworks.ctxeng.actor_mixin.ContextEngine") as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.from_agent.return_value = mock_engine

            result = ctxeng_actor.create_context_engine_from_agent(format_type="text")

            mock_engine_class.from_agent.assert_called_once_with(ctxeng_actor, format_type="text")
            assert result == mock_engine

    def test_create_context_engine_from_state(self, ctxeng_actor):
        """Test creating context engine from agent state."""
        mock_agent_state = Mock()

        with patch("dana.frameworks.ctxeng.actor_mixin.ContextEngine") as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.from_agent_state.return_value = mock_engine

            result = ctxeng_actor.create_context_engine_from_state(mock_agent_state, max_tokens=2000)

            mock_engine_class.from_agent_state.assert_called_once_with(mock_agent_state, max_tokens=2000)
            assert result == mock_engine

    def test_apply_to_instance(self):
        """Test applying mixin to existing agent instance."""
        mock_agent = Mock()
        mock_agent.__class__ = type("MockAgent", (), {})

        # Apply the mixin
        ContextEngineerMixin.apply_to_instance(mock_agent, {"format_type": "text"})

        # Check that the agent's class was modified and config was set
        assert hasattr(mock_agent, "_ctxeng_config")
        assert mock_agent._ctxeng_config == {"format_type": "text"}

        # Check that the agent now has the mixin methods
        assert hasattr(mock_agent, "assemble_context")
        assert hasattr(mock_agent, "_context_engine")

    def test_apply_to_instance_without_config(self):
        """Test applying mixin to existing agent instance without config."""
        mock_agent = Mock()
        mock_agent.__class__ = type("MockAgent", (), {})

        # Apply the mixin
        ContextEngineerMixin.apply_to_instance(mock_agent)

        # Check that the agent's class was modified and config was set
        assert hasattr(mock_agent, "_ctxeng_config")
        assert mock_agent._ctxeng_config == {}

        # Check that the agent now has the mixin methods
        assert hasattr(mock_agent, "assemble_context")
        assert hasattr(mock_agent, "_context_engine")


if __name__ == "__main__":
    pytest.main([__file__])
