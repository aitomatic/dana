"""Tests for CORRAL operation results and data structures."""

from datetime import datetime

from dana.frameworks.corral.operations import (
    CurationResult,
    OrganizationResult,
    RetrievalResult,
    ReasoningResult,
    ActionResult,
    LearningResult,
    CORRALResult,
    RankedKnowledge,
    CrossReference,
    ReasoningTrace,
    KnowledgeGap,
    ExecutedAction,
    LearningUpdate,
    NewPattern,
)
from dana.frameworks.corral.knowledge import Knowledge, KnowledgeCategory


class TestCurationResult:
    """Test CurationResult class."""

    def test_create_curation_result(self):
        """Test creating curation result."""
        knowledge = Knowledge(
            id="test_1",
            category=KnowledgeCategory.DECLARATIVE,
            content={"fact": "test"},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
        )

        result = CurationResult(
            curated_knowledge=[knowledge], quality_scores={"test_1": 0.9}, processing_recommendations=["Good quality knowledge"]
        )

        assert len(result.curated_knowledge) == 1
        assert result.quality_scores["test_1"] == 0.9
        assert len(result.processing_recommendations) == 1
        assert result.knowledge_count == 1
        assert result.average_quality == 0.9

    def test_average_quality_empty(self):
        """Test average quality with no scores."""
        result = CurationResult(curated_knowledge=[], quality_scores={}, processing_recommendations=[])

        assert result.average_quality == 0.0

    def test_average_quality_multiple(self):
        """Test average quality with multiple scores."""
        result = CurationResult(curated_knowledge=[], quality_scores={"k1": 0.8, "k2": 0.6, "k3": 1.0}, processing_recommendations=[])

        assert abs(result.average_quality - 0.8) < 1e-10  # (0.8 + 0.6 + 1.0) / 3


class TestOrganizationResult:
    """Test OrganizationResult class."""

    def test_create_organization_result(self):
        """Test creating organization result."""
        knowledge = Knowledge(
            id="test_1", category=KnowledgeCategory.DECLARATIVE, content={}, confidence=0.8, source="test", timestamp=datetime.now()
        )

        cross_ref = CrossReference(from_knowledge_id="test_1", to_knowledge_id="test_2", relationship_type="similarity", strength=0.7)

        result = OrganizationResult(
            structured_knowledge=[knowledge],
            knowledge_graph={"test_1": ["test_2"]},
            cross_references=[cross_ref],
            indices_created=["category_index", "confidence_index"],
        )

        assert len(result.structured_knowledge) == 1
        assert "test_1" in result.knowledge_graph
        assert result.knowledge_graph["test_1"] == ["test_2"]
        assert len(result.cross_references) == 1
        assert len(result.indices_created) == 2


class TestRetrievalResult:
    """Test RetrievalResult class."""

    def test_create_retrieval_result(self):
        """Test creating retrieval result."""
        knowledge = Knowledge(
            id="test_1", category=KnowledgeCategory.DECLARATIVE, content={}, confidence=0.8, source="test", timestamp=datetime.now()
        )

        ranked = RankedKnowledge(knowledge=knowledge, relevance_score=0.9, ranking_factors={"query_match": 0.8, "confidence": 0.9})

        result = RetrievalResult(ranked_knowledge=[ranked], total_candidates=5, retrieval_confidence=0.85)

        assert len(result.ranked_knowledge) == 1
        assert result.total_candidates == 5
        assert result.retrieval_confidence == 0.85
        assert len(result.knowledge_items) == 1
        assert result.top_knowledge == knowledge

    def test_empty_retrieval_result(self):
        """Test empty retrieval result."""
        result = RetrievalResult(ranked_knowledge=[], total_candidates=0, retrieval_confidence=0.0)

        assert len(result.knowledge_items) == 0
        assert result.top_knowledge is None


class TestReasoningResult:
    """Test ReasoningResult class."""

    def test_create_reasoning_result(self):
        """Test creating reasoning result."""
        trace = ReasoningTrace(
            step_number=1,
            operation="causal_analysis",
            inputs=["input_1"],
            outputs=["conclusion_1"],
            confidence=0.8,
            reasoning_type="causal",
        )

        gap = KnowledgeGap(gap_type="missing_causal", description="Need more causal information", priority=0.9)

        result = ReasoningResult(
            conclusions=["First conclusion", "Second conclusion"],
            confidence_scores={"First conclusion": 0.8, "Second conclusion": 0.6},
            reasoning_traces=[trace],
            knowledge_gaps=[gap],
            insights={"causal_links": 3},
        )

        assert len(result.conclusions) == 2
        assert result.primary_conclusion == "First conclusion"
        assert result.overall_confidence == 0.7  # (0.8 + 0.6) / 2
        assert len(result.reasoning_traces) == 1
        assert len(result.knowledge_gaps) == 1

    def test_empty_conclusions(self):
        """Test reasoning result with no conclusions."""
        result = ReasoningResult(conclusions=[], confidence_scores={}, reasoning_traces=[], knowledge_gaps=[])

        assert result.primary_conclusion is None
        assert result.overall_confidence == 0.0


class TestActionResult:
    """Test ActionResult class."""

    def test_create_action_result(self):
        """Test creating action result."""
        action1 = ExecutedAction(
            action_type="test", action_name="action_1", parameters={}, result="Success", success=True, execution_time=0.1
        )

        action2 = ExecutedAction(
            action_type="test", action_name="action_2", parameters={}, result="Failed", success=False, execution_time=0.2
        )

        result = ActionResult(
            executed_actions=[action1, action2], outcomes=["Success", "Failed"], success_rate=0.5, performance_metrics={"total_time": 0.3}
        )

        assert result.total_actions == 2
        assert result.successful_actions == 1
        assert result.success_rate == 0.5
        assert len(result.outcomes) == 2


class TestLearningResult:
    """Test LearningResult class."""

    def test_create_learning_result(self):
        """Test creating learning result."""
        update = LearningUpdate(
            knowledge_id="k1",
            update_type="confidence_update",
            old_value=0.5,
            new_value=0.7,
            evidence="Successful outcome",
            confidence_change=0.2,
        )

        pattern = NewPattern(
            pattern_type="success_pattern",
            description="High success rate",
            confidence=0.8,
            supporting_instances=["instance_1", "instance_2"],
            potential_applications=["similar_problems"],
        )

        result = LearningResult(
            knowledge_updates=[update], new_patterns=[pattern], confidence_improvements={"k1": 0.2}, knowledge_removals=["old_k1"]
        )

        assert result.total_updates == 1
        assert result.patterns_discovered == 1
        assert len(result.knowledge_updates) == 1
        assert len(result.new_patterns) == 1
        assert result.confidence_improvements["k1"] == 0.2
        assert "old_k1" in result.knowledge_removals


class TestCORRALResult:
    """Test complete CORRAL cycle result."""

    def test_create_corral_result(self):
        """Test creating complete CORRAL result."""
        # Create minimal sub-results for testing
        curation_result = CurationResult([], {}, [])
        organization_result = OrganizationResult([], {}, [], [])
        retrieval_result = RetrievalResult([], 0, 0.0)
        reasoning_result = ReasoningResult([], {}, [], [])
        action_result = ActionResult([], [], 0.0)
        learning_result = LearningResult([], [], {}, [])

        corral_result = CORRALResult(
            problem_statement="Test problem",
            curation_result=curation_result,
            organization_result=organization_result,
            retrieval_result=retrieval_result,
            reasoning_result=reasoning_result,
            action_result=action_result,
            learning_result=learning_result,
            cycle_success=True,
            total_execution_time=1.5,
        )

        assert corral_result.problem_statement == "Test problem"
        assert corral_result.cycle_success is True
        assert corral_result.total_execution_time == 1.5
        assert len(corral_result.knowledge_gained) == 0
        assert len(corral_result.confidence_changes) == 0

    def test_success_metrics(self):
        """Test CORRAL result success metrics."""
        # Create sub-results with some data
        knowledge = Knowledge(
            id="test_1", category=KnowledgeCategory.DECLARATIVE, content={}, confidence=0.8, source="test", timestamp=datetime.now()
        )

        curation_result = CurationResult([knowledge], {"test_1": 0.9}, [])
        organization_result = OrganizationResult([], {}, [], [])
        retrieval_result = RetrievalResult([], 0, 0.0)
        reasoning_result = ReasoningResult(["conclusion"], {"conclusion": 0.7}, [], [])
        action_result = ActionResult([], [], 0.6)
        learning_result = LearningResult(
            [LearningUpdate("k1", "update", 0.5, 0.7, "evidence", 0.2)], [NewPattern("pattern", "desc", 0.8, [], [])], {"k1": 0.2}, []
        )

        corral_result = CORRALResult(
            problem_statement="Test problem",
            curation_result=curation_result,
            organization_result=organization_result,
            retrieval_result=retrieval_result,
            reasoning_result=reasoning_result,
            action_result=action_result,
            learning_result=learning_result,
            cycle_success=True,
            total_execution_time=1.5,
        )

        metrics = corral_result.success_metrics

        assert metrics["cycle_success"] == 1.0
        assert metrics["knowledge_quality"] == 0.9
        assert metrics["reasoning_confidence"] == 0.7
        assert metrics["action_success_rate"] == 0.6
        assert metrics["knowledge_updates"] == 1.0
        assert metrics["patterns_discovered"] == 1.0
