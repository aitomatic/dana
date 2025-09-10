"""
Tests for the new centralized AgentState architecture.
"""

from datetime import datetime

from dana.core.agent import AgentState, ProblemContext, AgentMind, CapabilityRegistry
from dana.core.agent.context import ExecutionContext
from dana.core.agent.timeline import Timeline


class TestAgentState:
    """Test cases for centralized AgentState."""

    def test_create_agent_state(self):
        """Test creating a new centralized agent state."""
        state = AgentState()

        # Test core components are initialized
        assert state.problem_context is None
        assert isinstance(state.mind, AgentMind)
        assert isinstance(state.timeline, Timeline)
        assert isinstance(state.execution, ExecutionContext)
        assert isinstance(state.capabilities, CapabilityRegistry)

        # Test metadata
        assert state.session_id is None
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.last_updated, datetime)

    def test_set_problem_context(self):
        """Test setting problem context."""
        state = AgentState()
        problem = ProblemContext(problem_statement="Test problem", depth=2)

        state.set_problem_context(problem)

        assert state.problem_context == problem
        assert state.execution.recursion_depth == 2
        assert state.last_updated > state.created_at

    def test_start_new_conversation_turn(self):
        """Test starting new conversation turn."""
        import uuid
        # Create timeline with unique agent ID to avoid loading existing events
        timeline = Timeline(agent_id=f"test_{uuid.uuid4()}")
        state = AgentState()
        state.timeline = timeline

        state.start_new_conversation_turn("Hello")

        # Should update timeline
        conversations = state.timeline.get_events_by_type("conversation")
        assert len(conversations) == 1
        assert conversations[0].user_input == "Hello"
        assert state.last_updated > state.created_at

    def test_get_llm_context_minimal(self):
        """Test getting minimal LLM context."""
        state = AgentState()
        problem = ProblemContext(problem_statement="Test problem")
        state.set_problem_context(problem)

        context = state.get_llm_context(depth="minimal")

        # Should have basic context
        assert "query" in context
        assert "problem_statement" in context
        assert context["query"] == "Test problem"
        assert context["problem_statement"] == "Test problem"

        # Minimal should not have conversation history
        assert "conversation_history" not in context or not context.get("conversation_history")

    def test_get_llm_context_standard(self):
        """Test getting standard LLM context."""
        state = AgentState()
        problem = ProblemContext(problem_statement="Test problem")
        state.set_problem_context(problem)

        context = state.get_llm_context(depth="standard")

        # Should have comprehensive context
        assert "query" in context
        assert "problem_statement" in context
        assert "conversation_history" in context
        assert "user_context" in context
        assert "available_strategies" in context
        assert "available_tools" in context
        assert "execution_state" in context
        assert "relevant_memory" in context
        assert "context_priorities" in context

    def test_get_llm_context_comprehensive(self):
        """Test getting comprehensive LLM context."""
        state = AgentState()
        problem = ProblemContext(problem_statement="Test problem")
        state.set_problem_context(problem)

        context = state.get_llm_context(depth="comprehensive")

        # Should have comprehensive context (recent_events only included if there are events)
        assert all(
            key in context
            for key in ["query", "problem_statement", "conversation_history", "user_context", "available_strategies", "execution_state"]
        )

    def test_discover_resources_for_ctxeng(self):
        """Test resource discovery for ContextEngine integration."""
        state = AgentState()
        problem = ProblemContext(problem_statement="Test problem")
        state.set_problem_context(problem)

        resources = state.discover_resources_for_ctxeng()

        # Should discover key resources
        assert "problem_context" in resources
        assert "memory" in resources
        assert "world_model" in resources
        assert "execution_context" in resources
        assert "capabilities" in resources

        # Resources should be actual objects
        assert resources["problem_context"] == state.problem_context
        assert resources["memory"] == state.mind.memory
        assert resources["execution_context"] == state.execution

    def test_agent_mind_integration(self):
        """Test integration with AgentMind."""
        state = AgentState()

        # Mind should be initialized with all subsystems
        assert state.mind.memory is not None
        assert state.mind.world_model is not None
        assert state.mind.patterns is not None

        # Test memory integration
        state.mind.form_memory({"type": "working", "key": "test_key", "value": "test_value", "importance": 0.8})

        # Should be stored in working memory
        working_context = state.mind.memory.get_working_context()
        assert "test_key" in working_context
        assert working_context["test_key"] == "test_value"

    def test_capabilities_integration(self):
        """Test integration with CapabilityRegistry."""
        state = AgentState()

        # Should start empty
        assert state.capabilities.get_available_strategies() == []
        assert state.capabilities.get_available_tools() == []

        # Add capabilities
        from dana.core.agent.capabilities import Strategy, Tool

        strategy = Strategy(name="test_strategy", description="Test strategy", type="test")
        tool = Tool(name="test_tool", description="Test tool")

        state.capabilities.register_strategy(strategy)
        state.capabilities.register_tool(tool)

        # Should be available
        assert "test_strategy" in state.capabilities.get_available_strategies()
        assert "test_tool" in state.capabilities.get_available_tools()

    def test_execution_context_integration(self):
        """Test integration with ExecutionContext."""
        state = AgentState()

        # Should be able to proceed initially
        assert state.execution.can_proceed()

        # Test resource limits
        state.execution.current_metrics.memory_usage_mb = 2000  # Over limit
        assert not state.execution.can_proceed()

        # Test constraint management
        state.execution.add_constraint("test_constraint", "test_value")
        constraints = state.execution.get_constraints()
        assert "test_constraint" in constraints
        assert constraints["test_constraint"] == "test_value"

    def test_timeline_integration(self):
        """Test integration with Timeline."""
        import uuid
        # Create timeline with unique agent ID to avoid loading existing events
        timeline = Timeline(agent_id=f"test_{uuid.uuid4()}")
        state = AgentState()
        state.timeline = timeline

        # Timeline should be empty initially
        assert state.timeline.get_event_count() == 0

        # Add events using new API
        state.timeline.add_action("test", "test_action", depth=0)
        state.timeline.add_conversation_turn("Hello", "Hi!", turn_number=1)

        assert state.timeline.get_event_count() == 2

        # Check specific event types
        actions = state.timeline.get_events_by_type("action")
        conversations = state.timeline.get_events_by_type("conversation")

        assert len(actions) == 1
        assert len(conversations) == 1

    def test_get_state_summary(self):
        """Test getting comprehensive state summary."""
        state = AgentState()
        state.session_id = "test_session"

        problem = ProblemContext(problem_statement="Test problem")
        state.set_problem_context(problem)

        summary = state.get_state_summary()

        # Should have key summary information
        assert summary["session_id"] == "test_session"
        assert summary["problem_statement"] == "Test problem"
        assert summary["recursion_depth"] == 0
        assert summary["can_proceed"] is True
        assert "memory_status" in summary
        assert "last_updated" in summary

    def test_problem_context_to_dict(self):
        """Test ProblemContext to_dict method."""
        problem = ProblemContext(problem_statement="Test problem", objective="Test objective", depth=1)

        result = problem.to_dict()

        assert result["problem_statement"] == "Test problem"
        assert result["objective"] == "Test objective"
        assert result["depth"] == 1
        assert "constraints" in result
        assert "assumptions" in result

    def test_update_timestamp(self):
        """Test timestamp updating."""
        state = AgentState()
        original_time = state.last_updated

        # Wait a tiny bit and update
        import time

        time.sleep(0.001)
        state.update_timestamp()

        assert state.last_updated > original_time
