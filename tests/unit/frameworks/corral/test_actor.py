"""Tests for CorralActorMixin mixin."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from dana.core.agent import ProblemContext
from dana.frameworks.corral.actor_mixin import CorralActorMixin
from dana.frameworks.corral.config import CORRALConfig
from dana.frameworks.corral.knowledge import Knowledge, KnowledgeCategory


class MockAgent:
    """Mock agent for testing mixin application."""

    def __init__(self, *args, **kwargs):
        # Don't call super() for object to avoid kwargs issues
        self.state = Mock()
        self.state.mind = Mock()
        self.state.mind.memory = Mock()
        self.state.execution = Mock()


class TestCorralActorMixin:
    """Test CorralActorMixin mixin functionality."""

    @pytest.fixture
    def corral_actor(self):
        """Create a mock agent with CorralActorMixin mixin."""

        class TestAgent(MockAgent, CorralActorMixin):
            def __init__(self):
                # Initialize MockAgent first
                MockAgent.__init__(self)
                # Then initialize CorralActorMixin
                CorralActorMixin.__init__(self)

        return TestAgent()

    def test_initialization(self, corral_actor):
        """Test CorralActorMixin initialization."""
        assert hasattr(corral_actor, "_corral_config")
        assert hasattr(corral_actor, "_knowledge_base")
        assert hasattr(corral_actor, "_curation_engine")
        assert hasattr(corral_actor, "_organization_engine")
        assert hasattr(corral_actor, "_retrieval_engine")
        assert hasattr(corral_actor, "_reasoning_engine")
        assert hasattr(corral_actor, "_action_engine")
        assert hasattr(corral_actor, "_learning_engine")

    def test_curate_knowledge(self, corral_actor):
        """Test knowledge curation."""
        result = corral_actor.curate_knowledge("Test knowledge source")

        assert result is not None
        assert hasattr(result, "curated_knowledge")
        assert hasattr(result, "quality_scores")

    def test_curate_from_interaction(self, corral_actor):
        """Test curating from interaction data."""
        result = corral_actor.curate_from_interaction(
            user_query="How to deploy?", agent_response="Use the deployment workflow", outcome="success"
        )

        assert result is not None
        assert len(result.curated_knowledge) > 0
        knowledge = result.curated_knowledge[0]
        assert "interaction" in knowledge.content
        assert knowledge.content["interaction"]["user_query"] == "How to deploy?"

    def test_curate_from_workflow_execution(self, corral_actor):
        """Test curating from workflow execution."""
        mock_workflow = Mock()
        mock_result = {"status": "success", "duration": 120}
        metrics = {"cpu_usage": 0.5, "memory_usage": 0.8}

        result = corral_actor.curate_from_workflow_execution(
            workflow=mock_workflow, execution_result=mock_result, performance_metrics=metrics
        )

        assert result is not None
        assert len(result.curated_knowledge) > 0
        knowledge = result.curated_knowledge[0]
        assert "workflow" in knowledge.content

    def test_organize_knowledge(self, corral_actor):
        """Test knowledge organization."""
        # Add some knowledge to the base
        knowledge = Knowledge(
            id="test_1",
            category=KnowledgeCategory.DECLARATIVE,
            content={"fact": "test"},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
        )
        corral_actor._knowledge_base["test_1"] = knowledge

        result = corral_actor.organize_knowledge()

        assert result is not None
        assert hasattr(result, "structured_knowledge")
        assert hasattr(result, "knowledge_graph")

    def test_retrieve_knowledge(self, corral_actor):
        """Test knowledge retrieval."""
        # Add knowledge to retrieve
        knowledge = Knowledge(
            id="retrieve_test",
            category=KnowledgeCategory.DECLARATIVE,
            content={"text": "deployment automation process"},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
        )
        corral_actor._knowledge_base["retrieve_test"] = knowledge

        result = corral_actor.retrieve_knowledge("deployment")

        assert result is not None
        assert hasattr(result, "ranked_knowledge")
        assert len(result.ranked_knowledge) > 0

    def test_retrieve_for_problem(self, corral_actor):
        """Test retrieving knowledge for specific problem."""
        problem_context = ProblemContext(problem_statement="How to deploy microservice?")

        result = corral_actor.retrieve_for_problem(problem_context)

        assert result is not None
        assert hasattr(result, "ranked_knowledge")

    def test_reason_with_knowledge(self, corral_actor):
        """Test reasoning with knowledge."""
        knowledge_set = [
            Knowledge(
                id="reason_test",
                category=KnowledgeCategory.CAUSAL,
                content={"cause": "high load", "effect": "scale up"},
                confidence=0.9,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        result = corral_actor.reason_with_knowledge(knowledge_set, "Why should we scale up?")

        assert result is not None
        assert hasattr(result, "conclusions")
        assert hasattr(result, "reasoning_traces")

    def test_explain_decision(self, corral_actor):
        """Test decision explanation."""
        causal_knowledge = [
            Knowledge(
                id="explain_test",
                category=KnowledgeCategory.CAUSAL,
                content={"cause": "traffic spike", "effect": "scale decision"},
                confidence=0.8,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        explanation = corral_actor.explain_decision("scale up", causal_knowledge)

        assert explanation is not None
        assert "decision" in explanation
        assert "supporting_knowledge" in explanation

    def test_predict_outcomes(self, corral_actor):
        """Test outcome prediction."""
        predictions = corral_actor.predict_outcomes("deploy new version", {"env": "prod"})

        assert predictions is not None
        assert len(predictions) > 0
        for prediction in predictions:
            assert "outcome" in prediction
            assert "probability" in prediction

    def test_act_on_knowledge(self, corral_actor):
        """Test acting on reasoning results."""
        from dana.frameworks.corral.operations import ReasoningResult

        reasoning_result = ReasoningResult(
            conclusions=["Use blue-green deployment"],
            confidence_scores={"Use blue-green deployment": 0.9},
            reasoning_traces=[],
            knowledge_gaps=[],
        )

        result = corral_actor.act_on_knowledge(reasoning_result)

        assert result is not None
        assert hasattr(result, "executed_actions")
        assert hasattr(result, "success_rate")

    def test_learn_from_outcome(self, corral_actor):
        """Test learning from outcomes."""
        knowledge_used = [
            Knowledge(
                id="learn_test",
                category=KnowledgeCategory.PROCEDURAL,
                content={"process": "deployment"},
                confidence=0.7,
                source="test",
                timestamp=datetime.now(),
            )
        ]
        corral_actor._knowledge_base["learn_test"] = knowledge_used[0]

        result = corral_actor.learn_from_outcome(
            knowledge_used=knowledge_used, action_taken="deploy", outcome={"success": True}, context={"env": "production"}
        )

        assert result is not None
        assert hasattr(result, "knowledge_updates")
        assert hasattr(result, "confidence_improvements")

    def test_execute_corral_cycle_success(self, corral_actor):
        """Test successful CORRAL cycle execution."""
        problem = "Deploy microservice with zero downtime"

        # Mock successful cycle
        with patch.multiple(
            corral_actor,
            curate_knowledge=Mock(return_value=Mock(curated_knowledge=[])),
            organize_knowledge=Mock(return_value=Mock()),
            retrieve_knowledge=Mock(return_value=Mock(knowledge_items=[])),
            reason_with_knowledge=Mock(return_value=Mock()),
            act_on_knowledge=Mock(return_value=Mock(success_rate=0.8, executed_actions=[], outcomes=[])),
            learn_from_outcome=Mock(return_value=Mock()),
        ):
            result = corral_actor.execute_corral_cycle(problem)

        assert result is not None
        assert result.problem_statement == problem
        assert result.cycle_success is True
        assert result.total_execution_time > 0

    def test_execute_corral_cycle_with_problem_context(self, corral_actor):
        """Test CORRAL cycle with ProblemContext input."""
        problem_context = ProblemContext(problem_statement="Deploy with monitoring", objective="Ensure system stability")

        with patch.multiple(
            corral_actor,
            curate_knowledge=Mock(return_value=Mock(curated_knowledge=[])),
            organize_knowledge=Mock(return_value=Mock()),
            retrieve_knowledge=Mock(return_value=Mock(knowledge_items=[])),
            reason_with_knowledge=Mock(return_value=Mock()),
            act_on_knowledge=Mock(return_value=Mock(success_rate=0.9, executed_actions=[], outcomes=[])),
            learn_from_outcome=Mock(return_value=Mock()),
        ):
            result = corral_actor.execute_corral_cycle(problem_context)

        assert result.problem_statement == "Deploy with monitoring"

    def test_execute_corral_cycle_failure(self, corral_actor):
        """Test CORRAL cycle with failure."""
        problem = "Test problem"

        # Mock failure in reasoning
        with patch.object(corral_actor, "reason_with_knowledge", side_effect=Exception("Reasoning failed")):
            result = corral_actor.execute_corral_cycle(problem)

        assert result.cycle_success is False
        assert "error" in result.metadata

    def test_get_knowledge_state(self, corral_actor):
        """Test getting knowledge state."""
        # Add some knowledge
        knowledge = Knowledge(
            id="state_test",
            category=KnowledgeCategory.DECLARATIVE,
            content={"fact": "test"},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
        )
        corral_actor._knowledge_base["state_test"] = knowledge

        state = corral_actor.get_knowledge_state()

        assert "knowledge_count" in state
        assert state["knowledge_count"] == 1
        assert "categories" in state
        assert "average_confidence" in state
        assert state["average_confidence"] == 0.8

    def test_sync_with_agent_mind(self, corral_actor):
        """Test synchronization with AgentMind."""
        # Mock the form_memory method
        corral_actor.state.mind.form_memory = Mock()

        corral_actor.sync_with_agent_mind()

        # Should call form_memory with knowledge state
        corral_actor.state.mind.form_memory.assert_called_once()
        call_args = corral_actor.state.mind.form_memory.call_args[0][0]
        assert call_args["type"] == "semantic"
        assert call_args["key"] == "corral_knowledge_state"

    def test_contribute_to_context(self, corral_actor):
        """Test contributing to context."""
        problem_context = ProblemContext(problem_statement="Test problem")

        # Mock retrieval
        with patch.object(corral_actor, "retrieve_for_problem") as mock_retrieve:
            mock_retrieve.return_value = Mock(knowledge_items=[], retrieval_confidence=0.8)

            context_contribution = corral_actor.contribute_to_context(problem_context)

        assert "relevant_knowledge_count" in context_contribution
        assert "knowledge_confidence" in context_contribution
        assert context_contribution["knowledge_confidence"] == 0.8

    def test_apply_to_instance(self):
        """Test applying mixin to existing instance."""
        # Create mock agent instance
        agent = MockAgent()

        # Apply CorralActorMixin mixin
        CorralActorMixin.apply_to_instance(agent)

        # Should have CORRAL capabilities
        assert hasattr(agent, "_corral_config")
        assert hasattr(agent, "_knowledge_base")
        assert hasattr(agent, "curate_knowledge")
        assert hasattr(agent, "execute_corral_cycle")

    def test_continuous_corral(self, corral_actor):
        """Test continuous CORRAL processing."""
        # Create problem stream
        problems = [ProblemContext(problem_statement="Problem 1"), ProblemContext(problem_statement="Problem 2")]

        # Mock execute_corral_cycle
        with patch.object(corral_actor, "execute_corral_cycle") as mock_cycle:
            mock_cycle.return_value = Mock(problem_statement="Test")

            results = list(corral_actor.continuous_corral(iter(problems)))

        assert len(results) == 2
        assert mock_cycle.call_count == 2

    def test_custom_config_initialization(self):
        """Test initialization with custom config."""
        custom_config = CORRALConfig(quality_threshold=0.9, max_retrieval_results=20)

        class TestAgent(MockAgent, CorralActorMixin):
            def __init__(self):
                # Initialize MockAgent first
                MockAgent.__init__(self)
                # Then initialize CorralActorMixin with custom config
                CorralActorMixin.__init__(self, corral_config=custom_config)

        agent = TestAgent()

        assert agent._corral_config.quality_threshold == 0.9
        assert agent._corral_config.max_retrieval_results == 20
