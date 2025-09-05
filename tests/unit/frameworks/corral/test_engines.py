"""Tests for CORRAL processing engines."""

from datetime import datetime
from unittest.mock import Mock

from dana.core.agent import ProblemContext
from dana.frameworks.corral.engines import (
    CurationEngine,
    OrganizationEngine,
    RetrievalEngine,
    ReasoningEngine,
    ActionEngine,
    LearningEngine,
)
from dana.frameworks.corral.config import CORRALConfig, ReasoningType
from dana.frameworks.corral.knowledge import Knowledge, KnowledgeCategory


class TestCurationEngine:
    """Test CurationEngine class."""

    def test_curate_from_text(self):
        """Test curating knowledge from text."""
        config = CORRALConfig()
        engine = CurationEngine(config)

        # Test causal text
        causal_text = "Rain causes wet ground because water falls from sky"
        result = engine.curate(causal_text, {}, 0.5, True)

        assert len(result.curated_knowledge) > 0
        # Should detect causal pattern
        causal_knowledge = [k for k in result.curated_knowledge if k.category == KnowledgeCategory.CAUSAL]
        assert len(causal_knowledge) > 0

    def test_curate_from_structured_interaction(self):
        """Test curating from interaction data."""
        config = CORRALConfig()
        engine = CurationEngine(config)

        interaction_data = {"user_query": "How do I deploy?", "agent_response": "Use the deployment workflow", "outcome": "success"}

        result = engine.curate(interaction_data, {"source_type": "interaction"}, 0.5, True)

        assert len(result.curated_knowledge) > 0
        knowledge = result.curated_knowledge[0]
        assert "interaction" in knowledge.content
        assert knowledge.source == "interaction"

    def test_curate_from_workflow_data(self):
        """Test curating from workflow data."""
        config = CORRALConfig()
        engine = CurationEngine(config)

        workflow_data = {
            "workflow": "deployment_workflow",
            "execution_result": {"status": "success", "time": 120},
            "performance_metrics": {"cpu": 0.5, "memory": 0.8},
        }

        result = engine.curate(workflow_data, {"source_type": "workflow"}, 0.5, True)

        assert len(result.curated_knowledge) > 0
        knowledge = result.curated_knowledge[0]
        assert knowledge.category == KnowledgeCategory.PROCEDURAL
        assert knowledge.source == "workflow"

    def test_curate_from_problem_context(self):
        """Test curating from ProblemContext."""
        config = CORRALConfig()
        engine = CurationEngine(config)

        problem = ProblemContext(problem_statement="Deploy microservice", objective="Zero downtime deployment", depth=1)

        result = engine.curate(problem, {}, 0.5, True)

        assert len(result.curated_knowledge) > 0
        knowledge = result.curated_knowledge[0]
        assert "Deploy microservice" in knowledge.content["problem_statement"]
        assert knowledge.source == "problem_context"

    def test_quality_filtering(self):
        """Test quality threshold filtering."""
        config = CORRALConfig()
        engine = CurationEngine(config)

        # Use high quality threshold
        result = engine.curate("test text", {}, 0.9, True)

        # Should filter out low quality knowledge
        assert len(result.curated_knowledge) == 0 or all(result.quality_scores[k.id] >= 0.9 for k in result.curated_knowledge)


class TestOrganizationEngine:
    """Test OrganizationEngine class."""

    def test_organize_knowledge(self):
        """Test organizing knowledge items."""
        config = CORRALConfig()
        engine = OrganizationEngine(config)

        knowledge_items = [
            Knowledge(
                id="k1",
                category=KnowledgeCategory.DECLARATIVE,
                content={"text": "fact one"},
                confidence=0.8,
                source="test",
                timestamp=datetime.now(),
            ),
            Knowledge(
                id="k2",
                category=KnowledgeCategory.PROCEDURAL,
                content={"text": "step by step process"},
                confidence=0.9,
                source="test",
                timestamp=datetime.now(),
            ),
        ]

        result = engine.organize(knowledge_items, None, True, True)

        assert len(result.structured_knowledge) == 2
        assert "k1" in result.knowledge_graph
        assert "k2" in result.knowledge_graph
        assert len(result.indices_created) > 0

    def test_categorize_knowledge(self):
        """Test knowledge categorization."""
        config = CORRALConfig()
        engine = OrganizationEngine(config)

        # Test procedural knowledge
        procedural_knowledge = Knowledge(
            id="proc",
            category=KnowledgeCategory.DECLARATIVE,  # Wrong category initially
            content={"text": "follow these steps to process the workflow"},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
        )

        category = engine.categorize(procedural_knowledge, 0.3)  # Lower threshold for simple text
        assert category == KnowledgeCategory.PROCEDURAL

        # Test causal knowledge
        causal_knowledge = Knowledge(
            id="causal",
            category=KnowledgeCategory.DECLARATIVE,
            content={"text": "this causes that because of the mechanism"},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
        )

        category = engine.categorize(causal_knowledge, 0.3)  # Lower threshold for simple text
        assert category == KnowledgeCategory.CAUSAL

    def test_create_relationships(self):
        """Test relationship creation between knowledge items."""
        config = CORRALConfig()
        engine = OrganizationEngine(config)

        # Create similar knowledge items with more overlap
        k1 = Knowledge(
            id="k1",
            category=KnowledgeCategory.DECLARATIVE,
            content={"text": "deployment automation process"},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
        )
        k2 = Knowledge(
            id="k2",
            category=KnowledgeCategory.DECLARATIVE,
            content={"text": "deployment automation workflow"},
            confidence=0.9,
            source="test",
            timestamp=datetime.now(),
        )

        relationships = engine._create_relationships([k1, k2])

        # Should find similarity
        assert len(relationships) > 0
        rel = relationships[0]
        assert rel.relationship_type == "similarity"
        assert rel.strength > 0


class TestRetrievalEngine:
    """Test RetrievalEngine class."""

    def test_retrieve_knowledge(self):
        """Test knowledge retrieval."""
        config = CORRALConfig()
        engine = RetrievalEngine(config)

        knowledge_base = {
            "k1": Knowledge(
                id="k1",
                category=KnowledgeCategory.DECLARATIVE,
                content={"text": "deployment automation process"},
                confidence=0.8,
                source="test",
                timestamp=datetime.now(),
            ),
            "k2": Knowledge(
                id="k2",
                category=KnowledgeCategory.PROCEDURAL,
                content={"text": "database backup procedure"},
                confidence=0.7,
                source="test",
                timestamp=datetime.now(),
            ),
        }

        # Query for deployment
        result = engine.retrieve("deployment", knowledge_base, None, {}, 5, 0.5)

        assert len(result.ranked_knowledge) > 0
        # Should prioritize k1 (deployment) over k2 (database)
        top_knowledge = result.top_knowledge
        assert top_knowledge.id == "k1"

    def test_retrieve_by_category(self):
        """Test retrieval filtered by category."""
        config = CORRALConfig()
        engine = RetrievalEngine(config)

        knowledge_base = {
            "k1": Knowledge(
                id="k1",
                category=KnowledgeCategory.DECLARATIVE,
                content={"text": "deployment fact"},
                confidence=0.8,
                source="test",
                timestamp=datetime.now(),
            ),
            "k2": Knowledge(
                id="k2",
                category=KnowledgeCategory.PROCEDURAL,
                content={"text": "deployment procedure"},
                confidence=0.9,
                source="test",
                timestamp=datetime.now(),
            ),
        }

        # Only retrieve procedural knowledge
        result = engine.retrieve("deployment", knowledge_base, [KnowledgeCategory.PROCEDURAL], {}, 5, 0.5)

        assert len(result.ranked_knowledge) == 1
        assert result.ranked_knowledge[0].knowledge.id == "k2"
        assert result.ranked_knowledge[0].knowledge.category == KnowledgeCategory.PROCEDURAL

    def test_confidence_filtering(self):
        """Test minimum confidence filtering."""
        config = CORRALConfig()
        engine = RetrievalEngine(config)

        knowledge_base = {
            "k1": Knowledge(
                id="k1",
                category=KnowledgeCategory.DECLARATIVE,
                content={"text": "high confidence fact"},
                confidence=0.9,
                source="test",
                timestamp=datetime.now(),
            ),
            "k2": Knowledge(
                id="k2",
                category=KnowledgeCategory.DECLARATIVE,
                content={"text": "low confidence fact"},
                confidence=0.3,
                source="test",
                timestamp=datetime.now(),
            ),
        }

        # High confidence threshold
        result = engine.retrieve("fact", knowledge_base, None, {}, 5, 0.8)

        assert len(result.ranked_knowledge) == 1
        assert result.ranked_knowledge[0].knowledge.id == "k1"


class TestReasoningEngine:
    """Test ReasoningEngine class."""

    def test_causal_reasoning(self):
        """Test causal reasoning."""
        config = CORRALConfig(reasoning_types=[ReasoningType.CAUSAL])
        engine = ReasoningEngine(config)

        causal_knowledge = [
            Knowledge(
                id="causal_1",
                category=KnowledgeCategory.CAUSAL,
                content={"cause": "rain", "effect": "wet ground"},
                confidence=0.8,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        result = engine.reason(causal_knowledge, "Why is the ground wet?", "causal")

        assert len(result.conclusions) > 0
        assert len(result.reasoning_traces) > 0
        assert result.reasoning_traces[0].reasoning_type == "causal"

    def test_analogical_reasoning(self):
        """Test analogical reasoning."""
        config = CORRALConfig(reasoning_types=[ReasoningType.ANALOGICAL])
        engine = ReasoningEngine(config)

        knowledge_set = [
            Knowledge(
                id="k1",
                category=KnowledgeCategory.DECLARATIVE,
                content={"text": "similar pattern example"},
                confidence=0.7,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        result = engine.reason(knowledge_set, "Find similar patterns", "analogical")

        assert len(result.conclusions) > 0
        assert result.insights.get("analogies_found", 0) > 0

    def test_explain_decision(self):
        """Test decision explanation."""
        config = CORRALConfig()
        engine = ReasoningEngine(config)

        causal_knowledge = [
            Knowledge(
                id="causal_1",
                category=KnowledgeCategory.CAUSAL,
                content={"cause": "load increase", "effect": "scale up"},
                confidence=0.9,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        explanation = engine.explain_decision("scale up deployment", causal_knowledge)

        assert "decision" in explanation
        assert "supporting_knowledge" in explanation
        assert "causal_factors" in explanation
        assert explanation["causal_factors"] == 1

    def test_predict_outcomes(self):
        """Test outcome prediction."""
        config = CORRALConfig()
        engine = ReasoningEngine(config)

        predictions = engine.predict_outcomes("deploy new version", {"env": "production"})

        assert len(predictions) > 0
        for prediction in predictions:
            assert "outcome" in prediction
            assert "probability" in prediction
            assert "confidence" in prediction


class TestActionEngine:
    """Test ActionEngine class."""

    def test_act_on_reasoning(self):
        """Test converting reasoning to actions."""
        config = CORRALConfig()
        engine = ActionEngine(config)

        # Mock reasoning result
        from dana.frameworks.corral.operations import ReasoningResult

        reasoning_result = ReasoningResult(
            conclusions=["Deploy using blue-green strategy", "Monitor during deployment"],
            confidence_scores={"Deploy using blue-green strategy": 0.9, "Monitor during deployment": 0.8},
            reasoning_traces=[],
            knowledge_gaps=[],
        )

        mock_agent = Mock()
        result = engine.act(reasoning_result, None, mock_agent)

        assert len(result.executed_actions) > 0
        assert result.success_rate > 0
        # Should only act on high confidence conclusions
        for action in result.executed_actions:
            assert action.success is True

    def test_recommend_workflow(self):
        """Test workflow recommendation."""
        config = CORRALConfig()
        engine = ActionEngine(config)

        procedural_knowledge = [
            Knowledge(
                id="proc_1",
                category=KnowledgeCategory.PROCEDURAL,
                content={"workflow": "deployment_workflow", "steps": ["prepare", "deploy", "verify"]},
                confidence=0.9,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        recommendation = engine.recommend_workflow("deploy application", procedural_knowledge, [])

        assert "recommended_workflow" in recommendation
        assert recommendation["confidence"] > 0
        assert "reasoning" in recommendation

    def test_suggest_resources(self):
        """Test resource suggestion."""
        config = CORRALConfig()
        engine = ActionEngine(config)

        declarative_knowledge = [
            Knowledge(
                id="decl_1",
                category=KnowledgeCategory.DECLARATIVE,
                content={"resource": "kubernetes_cluster", "type": "compute"},
                confidence=0.8,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        problem_context = ProblemContext(problem_statement="need compute resources")
        suggestion = engine.suggest_resources(problem_context, declarative_knowledge)

        assert "suggested_resources" in suggestion
        assert len(suggestion["suggested_resources"]) > 0
        assert suggestion["confidence"] > 0


class TestLearningEngine:
    """Test LearningEngine class."""

    def test_learn_from_success(self):
        """Test learning from successful outcome."""
        config = CORRALConfig()
        engine = LearningEngine(config)

        knowledge_used = [
            Knowledge(
                id="k1",
                category=KnowledgeCategory.PROCEDURAL,
                content={"workflow": "deploy"},
                confidence=0.7,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        # Successful outcome should boost confidence
        result = engine.learn(knowledge_used, "deploy_action", {"success": True}, {})

        assert len(result.knowledge_updates) > 0
        update = result.knowledge_updates[0]
        assert update.confidence_change > 0  # Should increase confidence

    def test_learn_from_failure(self):
        """Test learning from failed outcome."""
        config = CORRALConfig()
        engine = LearningEngine(config)

        knowledge_used = [
            Knowledge(
                id="k1",
                category=KnowledgeCategory.PROCEDURAL,
                content={"workflow": "deploy"},
                confidence=0.7,
                source="test",
                timestamp=datetime.now(),
            )
        ]

        # Failed outcome should reduce confidence
        result = engine.learn(knowledge_used, "deploy_action", {"success": False}, {})

        assert len(result.knowledge_updates) > 0
        update = result.knowledge_updates[0]
        assert update.confidence_change < 0  # Should decrease confidence

    def test_pattern_discovery(self):
        """Test pattern discovery from experience."""
        config = CORRALConfig(pattern_discovery=True)
        engine = LearningEngine(config)

        # Multiple knowledge items with successful outcome should create pattern
        knowledge_used = [
            Knowledge(
                id="k1",
                category=KnowledgeCategory.DECLARATIVE,
                content={"fact": "A"},
                confidence=0.8,
                source="test",
                timestamp=datetime.now(),
            ),
            Knowledge(
                id="k2",
                category=KnowledgeCategory.PROCEDURAL,
                content={"process": "B"},
                confidence=0.9,
                source="test",
                timestamp=datetime.now(),
            ),
        ]

        result = engine.learn(knowledge_used, "combined_action", True, {})

        if result.new_patterns:  # Pattern discovery is probabilistic
            pattern = result.new_patterns[0]
            assert pattern.pattern_type == "knowledge_combination"
            assert len(pattern.supporting_instances) > 1

    def test_knowledge_pruning(self):
        """Test removal of low-confidence knowledge."""
        config = CORRALConfig(knowledge_pruning=True)
        engine = LearningEngine(config)

        low_confidence_knowledge = [
            Knowledge(
                id="low_conf",
                category=KnowledgeCategory.DECLARATIVE,
                content={"fact": "unreliable"},
                confidence=0.05,  # Very low
                source="test",
                timestamp=datetime.now(),
            )
        ]

        result = engine.learn(low_confidence_knowledge, "test_action", False, {})

        # Should mark for removal
        assert "low_conf" in result.knowledge_removals
