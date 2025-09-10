"""Tests for CORRALEngineer using composition pattern."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from dana.core.agent import ProblemContext
from dana.frameworks.corral.engineer import CORRALEngineer
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


class TestCORRALEngineer:
    """Test CORRALEngineer functionality using composition pattern."""

    @pytest.fixture
    def corral_engineer(self):
        """Create a CORRALEngineer instance."""
        return CORRALEngineer()

    def test_initialization(self, corral_engineer):
        """Test CORRALEngineer initialization."""
        assert hasattr(corral_engineer, "_knowledge_base")
        assert hasattr(corral_engineer, "_curation_engine")
        assert hasattr(corral_engineer, "_organization_engine")
        assert hasattr(corral_engineer, "_retrieval_engine")
        assert hasattr(corral_engineer, "_reasoning_engine")
        assert hasattr(corral_engineer, "_action_engine")
        assert hasattr(corral_engineer, "_learning_engine")

    def test_curate_knowledge(self, corral_engineer):
        """Test knowledge curation."""
        result = corral_engineer.curate_knowledge("Test knowledge source")

        assert result is not None
        assert hasattr(result, "curated_knowledge")
        assert hasattr(result, "quality_scores")

    def test_curate_from_interaction(self, corral_engineer):
        """Test curating from interaction data."""
        result = corral_engineer.curate_from_interaction(
            user_query="How to deploy?", agent_response="Use the deployment workflow", outcome="success"
        )

        assert result is not None
        assert len(result.curated_knowledge) > 0
        knowledge = result.curated_knowledge[0]
        assert "interaction" in knowledge.content
        assert knowledge.content["interaction"]["user_query"] == "How to deploy?"

    def test_curate_from_workflow_execution(self, corral_engineer):
        """Test curating from workflow execution."""
        mock_workflow = Mock()
        mock_result = {"status": "success", "duration": 120}
        metrics = {"cpu_usage": 0.5, "memory_usage": 0.8}

        result = corral_engineer.curate_from_workflow_execution(
            workflow=mock_workflow, execution_result=mock_result, performance_metrics=metrics
        )

        assert result is not None
        assert len(result.curated_knowledge) > 0
        knowledge = result.curated_knowledge[0]
        assert "workflow" in knowledge.content

    def test_organize_knowledge(self, corral_engineer):
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
        corral_engineer._knowledge_base["test_1"] = knowledge

        result = corral_engineer.organize_knowledge()

        assert result is not None
        assert hasattr(result, "structured_knowledge")
        assert hasattr(result, "knowledge_graph")

    def test_retrieve_knowledge(self, corral_engineer):
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
        corral_engineer._knowledge_base["retrieve_test"] = knowledge

        result = corral_engineer.retrieve_knowledge("deployment")

        assert result is not None
        assert hasattr(result, "ranked_knowledge")
        assert len(result.ranked_knowledge) > 0

    def test_retrieve_for_problem(self, corral_engineer):
        """Test retrieving knowledge for specific problem."""
        problem_context = ProblemContext(problem_statement="How to deploy microservice?")

        result = corral_engineer.retrieve_for_problem(problem_context)

        assert result is not None
        assert hasattr(result, "ranked_knowledge")

    def test_reason_with_knowledge(self, corral_engineer):
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

        result = corral_engineer.reason_with_knowledge(knowledge_set, "Why should we scale up?")

        assert result is not None
        assert hasattr(result, "conclusions")
        assert hasattr(result, "reasoning_traces")

    def test_explain_decision(self, corral_engineer):
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

        explanation = corral_engineer.explain_decision("scale up", causal_knowledge)

        assert explanation is not None
        assert "decision" in explanation
        assert "supporting_knowledge" in explanation

    def test_predict_outcomes(self, corral_engineer):
        """Test outcome prediction."""
        predictions = corral_engineer.predict_outcomes("deploy new version", {"env": "prod"})

        assert predictions is not None
        assert len(predictions) > 0
        for prediction in predictions:
            assert "outcome" in prediction
            assert "probability" in prediction

    def test_act_on_knowledge(self, corral_engineer):
        """Test acting on reasoning results."""
        from dana.frameworks.corral.operations import ReasoningResult

        reasoning_result = ReasoningResult(
            conclusions=["Use blue-green deployment"],
            confidence_scores={"Use blue-green deployment": 0.9},
            reasoning_traces=[],
            knowledge_gaps=[],
        )

        result = corral_engineer.act_on_knowledge(reasoning_result)

        assert result is not None
        assert hasattr(result, "executed_actions")
        assert hasattr(result, "success_rate")

    def test_learn_from_outcome(self, corral_engineer):
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
        corral_engineer._knowledge_base["learn_test"] = knowledge_used[0]

        result = corral_engineer.learn_from_outcome(
            knowledge_used=knowledge_used, action_taken="deploy", outcome={"success": True}, context={"env": "production"}
        )

        assert result is not None
        assert hasattr(result, "knowledge_updates")
        assert hasattr(result, "confidence_improvements")

    def test_execute_corral_cycle_success(self, corral_engineer):
        """Test successful CORRAL cycle execution."""
        problem = "Deploy microservice with zero downtime"

        # Mock successful cycle
        from datetime import datetime
        from dana.frameworks.corral.operations import OrganizationResult, RetrievalResult, ReasoningResult, ActionResult, LearningResult

        with patch.multiple(
            corral_engineer,
            curate_knowledge=Mock(return_value=Mock(curated_knowledge=[])),
            organize_knowledge=Mock(return_value=OrganizationResult(structured_knowledge=[], knowledge_graph={}, cross_references=[], indices_created=[], metadata={}, timestamp=datetime.now())),
            retrieve_knowledge=Mock(return_value=RetrievalResult(ranked_knowledge=[], total_candidates=0, retrieval_confidence=0.0, retrieval_metadata={}, timestamp=datetime.now())),
            reason_with_knowledge=Mock(return_value=ReasoningResult(conclusions=[], confidence_scores={}, reasoning_traces=[], knowledge_gaps=[], insights={}, metadata={}, timestamp=datetime.now())),
            learn_from_outcome=Mock(return_value=LearningResult(knowledge_updates=[], new_patterns=[], confidence_improvements={}, knowledge_removals=[], insights={}, metadata={}, timestamp=datetime.now())),
        ), patch.object(corral_engineer._action_engine, 'act', return_value=ActionResult(executed_actions=[], outcomes=[], success_rate=0.8, performance_metrics={}, side_effects=[], metadata={}, timestamp=datetime.now())):
            result = corral_engineer.execute_corral_cycle(problem)

        assert result is not None
        assert result.problem_statement == problem
        assert result.cycle_success is True
        assert result.total_execution_time > 0

    def test_execute_corral_cycle_with_problem_context(self, corral_engineer):
        """Test CORRAL cycle with ProblemContext input."""
        problem_context = ProblemContext(problem_statement="Deploy with monitoring", objective="Ensure system stability")

        with patch.multiple(
            corral_engineer,
            curate_knowledge=Mock(return_value=Mock(curated_knowledge=[])),
            organize_knowledge=Mock(return_value=Mock()),
            retrieve_knowledge=Mock(return_value=Mock(knowledge_items=[])),
            reason_with_knowledge=Mock(return_value=Mock()),
            act_on_knowledge=Mock(return_value=Mock(success_rate=0.9, executed_actions=[], outcomes=[])),
            learn_from_outcome=Mock(return_value=Mock()),
        ):
            result = corral_engineer.execute_corral_cycle(problem_context)

        assert result.problem_statement == "Deploy with monitoring"

    def test_execute_corral_cycle_failure(self, corral_engineer):
        """Test CORRAL cycle with failure."""
        problem = "Test problem"

        # Mock failure in reasoning
        with patch.object(corral_engineer, "reason_with_knowledge", side_effect=Exception("Reasoning failed")):
            result = corral_engineer.execute_corral_cycle(problem)

        assert result.cycle_success is False
        assert "error" in result.metadata

    def test_get_knowledge_state(self, corral_engineer):
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
        corral_engineer._knowledge_base["state_test"] = knowledge

        state = corral_engineer.get_knowledge_state()

        assert "knowledge_count" in state
        assert state["knowledge_count"] == 1
        assert "categories" in state
        assert "average_confidence" in state
        assert state["average_confidence"] == 0.8

    def test_sync_with_agent_mind(self, corral_engineer):
        """Test synchronization with AgentMind - method doesn't exist in CORRALEngineer."""
        # This test is skipped because sync_with_agent_mind is not implemented in CORRALEngineer
        # It's implemented in the EnhancedAgent class instead
        pytest.skip("sync_with_agent_mind is not implemented in CORRALEngineer")

    def test_contribute_to_context(self, corral_engineer):
        """Test contributing to context."""
        problem_context = ProblemContext(problem_statement="Test problem")

        # Mock retrieval
        with patch.object(corral_engineer, "retrieve_for_problem") as mock_retrieve:
            mock_retrieve.return_value = Mock(knowledge_items=[], retrieval_confidence=0.8)

            context_contribution = corral_engineer.contribute_to_context(problem_context)

        assert "relevant_knowledge_count" in context_contribution
        assert "knowledge_confidence" in context_contribution
        assert context_contribution["knowledge_confidence"] == 0.8

    def test_apply_to_instance(self):
        """Test applying CORRALEngineer to existing instance."""
        # Create mock agent instance
        agent = MockAgent()

        # Add CORRALEngineer via composition
        agent._corral_engineer = CORRALEngineer.from_agent(agent)

        # Should have CORRAL capabilities
        assert hasattr(agent, "_corral_engineer")
        assert hasattr(agent._corral_engineer, "_knowledge_base")
        assert hasattr(agent._corral_engineer, "curate_knowledge")
        assert hasattr(agent._corral_engineer, "execute_corral_cycle")

    def test_continuous_corral(self, corral_engineer):
        """Test continuous CORRAL processing."""
        # Create problem stream
        problems = [ProblemContext(problem_statement="Problem 1"), ProblemContext(problem_statement="Problem 2")]

        # Mock execute_corral_cycle
        with patch.object(corral_engineer, "execute_corral_cycle") as mock_cycle:
            mock_cycle.return_value = Mock(problem_statement="Test")

            results = list(corral_engineer.continuous_corral(iter(problems)))

        assert len(results) == 2
        assert mock_cycle.call_count == 2

    def test_custom_config_initialization(self):
        """Test initialization with custom config."""
        custom_config = CORRALConfig(quality_threshold=0.9, max_retrieval_results=20)

        class TestAgent(MockAgent):
            def __init__(self):
                MockAgent.__init__(self)
                self._corral_engineer = CORRALEngineer(config=custom_config)

        agent = TestAgent()

        assert agent._corral_engineer.config.quality_threshold == 0.9
        assert agent._corral_engineer.config.max_retrieval_results == 20
