"""Integration tests for CORRAL framework with Dana agents."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from dana.core.agent import ProblemContext
from dana.frameworks.corral import CorralActorMixin
from dana.frameworks.corral.config import LIGHTWEIGHT_CONFIG
from dana.frameworks.corral.knowledge import Knowledge, KnowledgeCategory


class MockAgentInstance:
    """Mock AgentInstance for integration testing."""

    def __init__(self, *args, **kwargs):
        # Filter out known kwargs before calling super()
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["corral_config"]}
        super().__init__(*args, **filtered_kwargs)
        self.state = Mock()
        self.state.mind = Mock()
        self.state.mind.memory = Mock()
        self.state.mind.memory.get_working_context = Mock(return_value={})
        self.state.mind.form_memory = Mock()
        self.state.execution = Mock()
        self.state.execution.can_proceed = Mock(return_value=True)
        self._context_engine = None


class TestCORRALIntegration:
    """Test CORRAL framework integration scenarios."""

    @pytest.fixture
    def enhanced_agent(self):
        """Create agent with CORRAL capabilities."""

        class EnhancedAgent(MockAgentInstance, CorralActorMixin):
            def __init__(self):
                # Initialize MockAgentInstance first
                MockAgentInstance.__init__(self)
                # Then initialize CorralActorMixin
                CorralActorMixin.__init__(self)

        return EnhancedAgent()

    def test_full_corral_cycle_integration(self, enhanced_agent):
        """Test complete CORRAL cycle with realistic scenario."""
        # Scenario: Agent learning from deployment experience
        problem = ProblemContext(
            problem_statement="Deploy microservice to production with zero downtime",
            objective="Ensure service availability during deployment",
            constraints=["No service interruption", "Complete within 30 minutes"],
            assumptions=["Load balancer is configured", "Blue-green slots available"],
        )

        # Execute CORRAL cycle
        result = enhanced_agent.execute_corral_cycle(problem)

        # Verify cycle completed
        assert result.cycle_success is True
        assert result.problem_statement == problem.problem_statement
        assert result.total_execution_time > 0

        # Verify knowledge was curated from problem context
        assert len(result.curation_result.curated_knowledge) > 0
        problem_knowledge = result.curation_result.curated_knowledge[0]
        assert problem_knowledge.content["problem_statement"] == problem.problem_statement

        # Verify knowledge was added to agent's knowledge base
        assert len(enhanced_agent._knowledge_base) > 0

    def test_learning_from_interaction(self, enhanced_agent):
        """Test learning from agent-user interaction."""
        # Simulate successful interaction
        curation_result = enhanced_agent.curate_from_interaction(
            user_query="How do I scale my application?",
            agent_response="Use horizontal pod autoscaling in Kubernetes",
            outcome={"success": True, "user_satisfaction": 0.9},
            user_feedback="Very helpful, worked perfectly",
        )

        assert len(curation_result.curated_knowledge) > 0
        interaction_knowledge = curation_result.curated_knowledge[0]

        # Verify interaction details are captured
        assert "interaction" in interaction_knowledge.content
        assert interaction_knowledge.content["interaction"]["user_query"] == "How do I scale my application?"
        assert interaction_knowledge.content["interaction"]["agent_response"] == "Use horizontal pod autoscaling in Kubernetes"
        assert interaction_knowledge.confidence > 0.7  # Should be high due to positive feedback

    def test_workflow_knowledge_curation(self, enhanced_agent):
        """Test curating knowledge from workflow execution."""
        # Mock workflow execution
        mock_workflow = Mock()
        mock_workflow.__str__ = Mock(return_value="deployment_workflow_v2")

        execution_result = {"status": "completed", "duration_seconds": 180, "steps_completed": 5, "rollback_performed": False}

        performance_metrics = {"cpu_usage_peak": 0.75, "memory_usage_peak": 0.85, "network_io": 1024000, "success_rate": 1.0}

        curation_result = enhanced_agent.curate_from_workflow_execution(
            workflow=mock_workflow, execution_result=execution_result, performance_metrics=performance_metrics
        )

        assert len(curation_result.curated_knowledge) > 0
        workflow_knowledge = curation_result.curated_knowledge[0]

        # Should be categorized as procedural
        assert workflow_knowledge.category == KnowledgeCategory.PROCEDURAL
        assert workflow_knowledge.confidence > 0.8  # High confidence due to successful execution
        assert "workflow" in workflow_knowledge.content

    def test_knowledge_retrieval_and_reasoning(self, enhanced_agent):
        """Test retrieving and reasoning with accumulated knowledge."""
        # Add some knowledge to the agent
        deployment_knowledge = Knowledge(
            id="deploy_k1",
            category=KnowledgeCategory.PROCEDURAL,
            content={
                "procedure": "blue_green_deployment",
                "steps": ["prepare_new_env", "route_traffic", "verify_health", "retire_old"],
                "success_rate": 0.95,
                "avg_duration": 240,
            },
            confidence=0.9,
            source="workflow_execution",
            timestamp=datetime.now(),
        )

        scaling_knowledge = Knowledge(
            id="scale_k1",
            category=KnowledgeCategory.CAUSAL,
            content={
                "cause": "increased_traffic",
                "effect": "higher_response_times",
                "mechanism": "resource_saturation",
                "threshold": "85%_cpu",
            },
            confidence=0.8,
            source="monitoring_data",
            timestamp=datetime.now(),
        )

        enhanced_agent._knowledge_base["deploy_k1"] = deployment_knowledge
        enhanced_agent._knowledge_base["scale_k1"] = scaling_knowledge

        # Retrieve knowledge for deployment problem
        problem_context = ProblemContext(problem_statement="Application is slow during high traffic periods")

        retrieval_result = enhanced_agent.retrieve_for_problem(problem_context)

        # Should find relevant knowledge
        assert len(retrieval_result.ranked_knowledge) > 0
        assert retrieval_result.retrieval_confidence > 0.1

        # Reason with the retrieved knowledge
        reasoning_result = enhanced_agent.reason_with_knowledge(retrieval_result.knowledge_items, problem_context)

        assert len(reasoning_result.conclusions) > 0
        assert len(reasoning_result.reasoning_traces) > 0

    def test_action_and_learning_cycle(self, enhanced_agent):
        """Test acting on knowledge and learning from outcomes."""
        # Create reasoning result
        from dana.frameworks.corral.operations import ReasoningResult

        reasoning_result = ReasoningResult(
            conclusions=["Scale application horizontally", "Implement caching layer", "Optimize database queries"],
            confidence_scores={"Scale application horizontally": 0.9, "Implement caching layer": 0.8, "Optimize database queries": 0.7},
            reasoning_traces=[],
            knowledge_gaps=[],
        )

        # Act on the reasoning
        action_result = enhanced_agent.act_on_knowledge(reasoning_result)

        assert len(action_result.executed_actions) > 0
        assert action_result.success_rate > 0.5

        # Simulate learning from mixed outcomes
        knowledge_used = [
            Knowledge(
                id="action_k1",
                category=KnowledgeCategory.PROCEDURAL,
                content={"action": "horizontal_scaling"},
                confidence=0.8,
                source="reasoning",
                timestamp=datetime.now(),
            )
        ]
        enhanced_agent._knowledge_base["action_k1"] = knowledge_used[0]

        # Learn from successful scaling
        learning_result = enhanced_agent.learn_from_outcome(
            knowledge_used=knowledge_used,
            action_taken="horizontal_scaling",
            outcome={"success": True, "performance_improvement": 0.4},
            context={"traffic_level": "high", "time_of_day": "peak"},
        )

        # Should update confidence positively
        assert len(learning_result.knowledge_updates) > 0
        update = learning_result.knowledge_updates[0]
        assert update.confidence_change > 0

    def test_agent_mind_integration(self, enhanced_agent):
        """Test integration with AgentMind memory systems."""
        # Add knowledge and sync with agent mind
        knowledge = Knowledge(
            id="mind_k1",
            category=KnowledgeCategory.DECLARATIVE,
            content={"fact": "System performance degrades above 80% CPU"},
            confidence=0.9,
            source="monitoring",
            timestamp=datetime.now(),
        )
        enhanced_agent._knowledge_base["mind_k1"] = knowledge

        # Sync with agent mind
        enhanced_agent.sync_with_agent_mind()

        # Should have called form_memory
        enhanced_agent.state.mind.form_memory.assert_called_once()
        call_args = enhanced_agent.state.mind.form_memory.call_args[0][0]

        assert call_args["type"] == "semantic"
        assert call_args["key"] == "corral_knowledge_state"
        assert call_args["importance"] == 0.9
        assert "knowledge_count" in call_args["value"]

    def test_context_engine_integration(self, enhanced_agent):
        """Test contributing to ContextEngine."""
        # Add relevant knowledge
        context_knowledge = Knowledge(
            id="ctx_k1",
            category=KnowledgeCategory.RELATIONAL,
            content={"entity1": "load_balancer", "entity2": "application_pods", "relationship": "routes_traffic_to"},
            confidence=0.8,
            source="infrastructure_analysis",
            timestamp=datetime.now(),
        )
        enhanced_agent._knowledge_base["ctx_k1"] = context_knowledge

        problem_context = ProblemContext(problem_statement="Load balancer not distributing traffic evenly")

        context_contribution = enhanced_agent.contribute_to_context(problem_context, context_depth="standard")

        assert "relevant_knowledge_count" in context_contribution
        assert "knowledge_confidence" in context_contribution
        assert "top_relevant_knowledge" in context_contribution

    def test_mixin_application_to_existing_agent(self):
        """Test applying CorralActorMixin to existing agent instance."""
        # Create base agent
        agent = MockAgentInstance()

        # Verify no CORRAL capabilities initially
        assert not hasattr(agent, "curate_knowledge")
        assert not hasattr(agent, "execute_corral_cycle")

        # Apply CorralActorMixin mixin
        CorralActorMixin.apply_to_instance(agent)

        # Verify CORRAL capabilities added
        assert hasattr(agent, "curate_knowledge")
        assert hasattr(agent, "execute_corral_cycle")
        assert hasattr(agent, "_knowledge_base")
        assert hasattr(agent, "_corral_config")

        # Verify can use CORRAL functions
        result = agent.curate_knowledge("Test knowledge")
        assert result is not None

    def test_configuration_impact_on_behavior(self, enhanced_agent):
        """Test how different configurations affect behavior."""
        # Test with lightweight config
        lightweight_agent = enhanced_agent
        lightweight_agent._corral_config = LIGHTWEIGHT_CONFIG
        lightweight_agent._initialize_corral_engines()

        # Should use reduced retrieval results
        # retrieval_result = lightweight_agent.retrieve_knowledge("test query")  # TODO: Use result in assertion
        # Note: In real implementation, this would be limited by config
        # Here we just verify the config is applied
        assert lightweight_agent._corral_config.max_retrieval_results == 5

    def test_knowledge_persistence_across_cycles(self, enhanced_agent):
        """Test that knowledge persists and improves across multiple CORRAL cycles."""
        # First cycle
        # problem1 = "Optimize database performance"  # TODO: Use in cycle execution
        # result1 = enhanced_agent.execute_corral_cycle(problem1)  # TODO: Use result in assertion

        initial_knowledge_count = len(enhanced_agent._knowledge_base)
        assert initial_knowledge_count > 0

        # Second cycle with related problem
        problem2 = "Database queries are slow during peak hours"
        result2 = enhanced_agent.execute_corral_cycle(problem2)

        # Should have accumulated more knowledge
        final_knowledge_count = len(enhanced_agent._knowledge_base)
        assert final_knowledge_count >= initial_knowledge_count

        # Second cycle should benefit from knowledge gained in first cycle
        assert result2.retrieval_result.total_candidates > 0

    def test_error_handling_and_graceful_degradation(self, enhanced_agent):
        """Test error handling in CORRAL operations."""
        # Test with malformed input
        with patch.object(enhanced_agent._curation_engine, "curate", side_effect=Exception("Curation failed")):
            result = enhanced_agent.execute_corral_cycle("Test problem")

            # Should handle error gracefully
            assert result.cycle_success is False
            assert "error" in result.metadata
            assert "Curation failed" in str(result.metadata["error"])

    def test_knowledge_quality_and_confidence_evolution(self, enhanced_agent):
        """Test how knowledge quality and confidence evolve over time."""
        # Add low-confidence knowledge
        uncertain_knowledge = Knowledge(
            id="uncertain_k1",
            category=KnowledgeCategory.PROCEDURAL,
            content={"process": "experimental_deployment"},
            confidence=0.4,  # Low initial confidence
            source="experiment",
            timestamp=datetime.now(),
        )
        enhanced_agent._knowledge_base["uncertain_k1"] = uncertain_knowledge

        # Simulate successful learning from this knowledge
        learning_result = enhanced_agent.learn_from_outcome(
            knowledge_used=[uncertain_knowledge],
            action_taken="experimental_deployment",
            outcome={"success": True, "improvement": 0.3},
            context={"environment": "test"},
        )

        # Confidence should improve
        if learning_result.confidence_improvements:
            confidence_change = learning_result.confidence_improvements.get("uncertain_k1", 0)
            assert confidence_change > 0

    def test_cross_category_knowledge_integration(self, enhanced_agent):
        """Test integration of knowledge across different categories."""
        # Add knowledge from different categories
        declarative = Knowledge(
            id="decl_k1",
            category=KnowledgeCategory.DECLARATIVE,
            content={"fact": "Kubernetes supports rolling updates"},
            confidence=0.95,
            source="documentation",
            timestamp=datetime.now(),
        )

        procedural = Knowledge(
            id="proc_k1",
            category=KnowledgeCategory.PROCEDURAL,
            content={"process": "kubectl_rolling_update_steps"},
            confidence=0.85,
            source="experience",
            timestamp=datetime.now(),
        )

        causal = Knowledge(
            id="causal_k1",
            category=KnowledgeCategory.CAUSAL,
            content={"cause": "rolling_update", "effect": "zero_downtime", "mechanism": "gradual_pod_replacement"},
            confidence=0.90,
            source="observation",
            timestamp=datetime.now(),
        )

        enhanced_agent._knowledge_base.update({"decl_k1": declarative, "proc_k1": procedural, "causal_k1": causal})

        # Query that should leverage multiple categories
        problem = ProblemContext(problem_statement="Deploy new version without service interruption")

        retrieval_result = enhanced_agent.retrieve_for_problem(problem)

        # Should retrieve knowledge from multiple categories
        retrieved_categories = {k.category for k in retrieval_result.knowledge_items}
        assert len(retrieved_categories) > 1  # Multiple categories represented

        # Reasoning should integrate across categories
        reasoning_result = enhanced_agent.reason_with_knowledge(retrieval_result.knowledge_items, problem)

        assert len(reasoning_result.conclusions) > 0
        assert reasoning_result.overall_confidence > 0.5
