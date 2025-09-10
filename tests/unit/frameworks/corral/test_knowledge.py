"""Tests for CORRAL knowledge representation."""

from datetime import datetime

from dana.frameworks.corral.knowledge import (
    Knowledge,
    KnowledgeCategory,
    DeclarativeKnowledge,
    ProceduralKnowledge,
    CausalKnowledge,
    RelationalKnowledge,
    ConditionalKnowledge,
    Condition,
    ProcedureStep,
    Evidence,
    create_knowledge,
)


class TestKnowledge:
    """Test basic Knowledge class."""

    def test_create_knowledge(self):
        """Test creating basic knowledge item."""
        knowledge = Knowledge(
            id="test_1",
            category=KnowledgeCategory.DECLARATIVE,
            content={"fact": "The sky is blue"},
            confidence=0.9,
            source="observation",
            timestamp=datetime.now(),
        )

        assert knowledge.id == "test_1"
        assert knowledge.category == KnowledgeCategory.DECLARATIVE
        assert knowledge.content["fact"] == "The sky is blue"
        assert knowledge.confidence == 0.9
        assert knowledge.source == "observation"
        assert knowledge.usage_count == 0
        assert knowledge.last_accessed is None
        assert len(knowledge.relationships) == 0

    def test_update_confidence(self):
        """Test updating confidence with validation."""
        knowledge = Knowledge(
            id="test_1",
            category=KnowledgeCategory.DECLARATIVE,
            content={"fact": "Test fact"},
            confidence=0.5,
            source="test",
            timestamp=datetime.now(),
        )

        # old_confidence = knowledge.confidence  # TODO: Use in assertion if needed
        knowledge.update_confidence(0.8, "test_validator", "Strong evidence")

        assert knowledge.confidence == 0.8
        assert len(knowledge.validation_history) == 1

        validation = knowledge.validation_history[0]
        assert validation.validator == "test_validator"
        assert validation.result is True  # Increased confidence
        assert abs(validation.confidence_change - 0.3) < 1e-10
        assert validation.evidence == "Strong evidence"

    def test_confidence_clamping(self):
        """Test confidence is clamped to [0,1] range."""
        knowledge = Knowledge(
            id="test_1", category=KnowledgeCategory.DECLARATIVE, content={}, confidence=0.5, source="test", timestamp=datetime.now()
        )

        # Test upper bound
        knowledge.update_confidence(1.5, "test_validator")
        assert knowledge.confidence == 1.0

        # Test lower bound
        knowledge.update_confidence(-0.5, "test_validator")
        assert knowledge.confidence == 0.0

    def test_record_access(self):
        """Test recording knowledge access."""
        knowledge = Knowledge(
            id="test_1", category=KnowledgeCategory.DECLARATIVE, content={}, confidence=0.5, source="test", timestamp=datetime.now()
        )

        assert knowledge.usage_count == 0
        assert knowledge.last_accessed is None

        knowledge.record_access()

        assert knowledge.usage_count == 1
        assert knowledge.last_accessed is not None

        knowledge.record_access()
        assert knowledge.usage_count == 2

    def test_add_relationship(self):
        """Test adding relationships."""
        knowledge = Knowledge(
            id="test_1", category=KnowledgeCategory.DECLARATIVE, content={}, confidence=0.5, source="test", timestamp=datetime.now()
        )

        knowledge.add_relationship("related_1")
        knowledge.add_relationship("related_2")

        assert len(knowledge.relationships) == 2
        assert "related_1" in knowledge.relationships
        assert "related_2" in knowledge.relationships

        # Test duplicate prevention
        knowledge.add_relationship("related_1")
        assert len(knowledge.relationships) == 2


class TestDeclarativeKnowledge:
    """Test DeclarativeKnowledge class."""

    def test_create_declarative_knowledge(self):
        """Test creating declarative knowledge."""
        knowledge = DeclarativeKnowledge(
            id="decl_1",
            category=KnowledgeCategory.DECLARATIVE,
            content={},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
            entity="sky",
            property="color",
            value="blue",
        )

        assert knowledge.category == KnowledgeCategory.DECLARATIVE
        assert knowledge.entity == "sky"
        assert knowledge.property == "color"
        assert knowledge.value == "blue"

    def test_auto_category_correction(self):
        """Test automatic category correction in post_init."""
        knowledge = DeclarativeKnowledge(
            id="decl_1",
            category=KnowledgeCategory.PROCEDURAL,  # Wrong category
            content={},
            confidence=0.8,
            source="test",
            timestamp=datetime.now(),
            entity="sky",
            property="color",
            value="blue",
        )

        assert knowledge.category == KnowledgeCategory.DECLARATIVE


class TestProceduralKnowledge:
    """Test ProceduralKnowledge class."""

    def test_create_procedural_knowledge(self):
        """Test creating procedural knowledge."""
        steps = [
            ProcedureStep(1, "start", "Start the process"),
            ProcedureStep(2, "execute", "Execute main logic"),
            ProcedureStep(3, "finish", "Complete the process"),
        ]

        knowledge = ProceduralKnowledge(
            id="proc_1",
            category=KnowledgeCategory.PROCEDURAL,
            content={},
            confidence=0.9,
            source="manual",
            timestamp=datetime.now(),
            procedure_name="Test Procedure",
            steps=steps,
            success_rate=0.85,
        )

        assert knowledge.category == KnowledgeCategory.PROCEDURAL
        assert knowledge.procedure_name == "Test Procedure"
        assert len(knowledge.steps) == 3
        assert knowledge.success_rate == 0.85
        assert knowledge.steps[0].action == "start"


class TestCausalKnowledge:
    """Test CausalKnowledge class."""

    def test_create_causal_knowledge(self):
        """Test creating causal knowledge."""
        knowledge = CausalKnowledge(
            id="causal_1",
            category=KnowledgeCategory.CAUSAL,
            content={},
            confidence=0.7,
            source="observation",
            timestamp=datetime.now(),
            cause="rain",
            effect="wet ground",
            mechanism="water falls from sky",
            strength=0.9,
        )

        assert knowledge.category == KnowledgeCategory.CAUSAL
        assert knowledge.cause == "rain"
        assert knowledge.effect == "wet ground"
        assert knowledge.mechanism == "water falls from sky"
        assert knowledge.strength == 0.9

    def test_add_evidence(self):
        """Test adding evidence to causal knowledge."""
        knowledge = CausalKnowledge(
            id="causal_1",
            category=KnowledgeCategory.CAUSAL,
            content={},
            confidence=0.7,
            source="test",
            timestamp=datetime.now(),
            cause="A",
            effect="B",
            mechanism="test",
        )

        supporting_evidence = Evidence(description="Observed correlation", strength=0.8, source="experiment", timestamp=datetime.now())

        counter_evidence = Evidence(description="Contradictory observation", strength=0.3, source="experiment", timestamp=datetime.now())

        knowledge.add_evidence(supporting_evidence, supporting=True)
        knowledge.add_evidence(counter_evidence, supporting=False)

        assert len(knowledge.supporting_evidence) == 1
        assert len(knowledge.counter_evidence) == 1
        assert knowledge.supporting_evidence[0].description == "Observed correlation"
        assert knowledge.counter_evidence[0].description == "Contradictory observation"


class TestRelationalKnowledge:
    """Test RelationalKnowledge class."""

    def test_create_relational_knowledge(self):
        """Test creating relational knowledge."""
        knowledge = RelationalKnowledge(
            id="rel_1",
            category=KnowledgeCategory.RELATIONAL,
            content={},
            confidence=0.8,
            source="analysis",
            timestamp=datetime.now(),
            entity1="user",
            entity2="system",
            relationship_type="interacts_with",
            bidirectional=True,
            strength=0.9,
        )

        assert knowledge.category == KnowledgeCategory.RELATIONAL
        assert knowledge.entity1 == "user"
        assert knowledge.entity2 == "system"
        assert knowledge.relationship_type == "interacts_with"
        assert knowledge.bidirectional is True
        assert knowledge.strength == 0.9


class TestConditionalKnowledge:
    """Test ConditionalKnowledge class."""

    def test_create_conditional_knowledge(self):
        """Test creating conditional knowledge."""
        conditions = [Condition("environment", "production", True), Condition("time", "business_hours", True)]

        knowledge = ConditionalKnowledge(
            id="cond_1",
            category=KnowledgeCategory.CONDITIONAL,
            content={},
            confidence=0.9,
            source="policy",
            timestamp=datetime.now(),
            base_knowledge_id="base_1",
            conditions=conditions,
            override_priority=1,
        )

        assert knowledge.category == KnowledgeCategory.CONDITIONAL
        assert knowledge.base_knowledge_id == "base_1"
        assert len(knowledge.conditions) == 2
        assert knowledge.override_priority == 1

    def test_applies_to_context(self):
        """Test context applicability checking."""
        knowledge = ConditionalKnowledge(
            id="cond_1",
            category=KnowledgeCategory.CONDITIONAL,
            content={},
            confidence=0.9,
            source="test",
            timestamp=datetime.now(),
            base_knowledge_id="base_1",
            context_requirements={"env": "prod", "user_type": "admin"},
        )

        # Matching context
        matching_context = {"env": "prod", "user_type": "admin", "extra": "ignored"}
        assert knowledge.applies_to_context(matching_context) is True

        # Non-matching context
        non_matching_context = {"env": "dev", "user_type": "admin"}
        assert knowledge.applies_to_context(non_matching_context) is False

        # Partial context
        partial_context = {"env": "prod"}
        assert knowledge.applies_to_context(partial_context) is False


class TestKnowledgeFactory:
    """Test knowledge factory function."""

    def test_create_declarative(self):
        """Test factory creates declarative knowledge."""
        knowledge = create_knowledge(
            category=KnowledgeCategory.DECLARATIVE, content={"test": "data"}, confidence=0.8, source="factory_test"
        )

        assert isinstance(knowledge, DeclarativeKnowledge)
        assert knowledge.category == KnowledgeCategory.DECLARATIVE
        assert knowledge.content["test"] == "data"

    def test_create_procedural(self):
        """Test factory creates procedural knowledge."""
        knowledge = create_knowledge(category=KnowledgeCategory.PROCEDURAL, content={"test": "data"}, confidence=0.8, source="factory_test")

        assert isinstance(knowledge, ProceduralKnowledge)
        assert knowledge.category == KnowledgeCategory.PROCEDURAL

    def test_create_causal(self):
        """Test factory creates causal knowledge."""
        knowledge = create_knowledge(category=KnowledgeCategory.CAUSAL, content={"test": "data"}, confidence=0.8, source="factory_test")

        assert isinstance(knowledge, CausalKnowledge)
        assert knowledge.category == KnowledgeCategory.CAUSAL

    def test_create_relational(self):
        """Test factory creates relational knowledge."""
        knowledge = create_knowledge(category=KnowledgeCategory.RELATIONAL, content={"test": "data"}, confidence=0.8, source="factory_test")

        assert isinstance(knowledge, RelationalKnowledge)
        assert knowledge.category == KnowledgeCategory.RELATIONAL

    def test_create_conditional(self):
        """Test factory creates conditional knowledge."""
        knowledge = create_knowledge(
            category=KnowledgeCategory.CONDITIONAL, content={"test": "data"}, confidence=0.8, source="factory_test"
        )

        assert isinstance(knowledge, ConditionalKnowledge)
        assert knowledge.category == KnowledgeCategory.CONDITIONAL

    def test_factory_sets_timestamp(self):
        """Test factory sets timestamp."""
        knowledge = create_knowledge(category=KnowledgeCategory.DECLARATIVE, content={}, confidence=0.8, source="test")

        assert isinstance(knowledge.timestamp, datetime)
        # Should be recent
        time_diff = datetime.now() - knowledge.timestamp
        assert time_diff.total_seconds() < 1.0

    def test_factory_generates_id(self):
        """Test factory generates ID."""
        knowledge = create_knowledge(category=KnowledgeCategory.DECLARATIVE, content={}, confidence=0.8, source="test")

        assert knowledge.id.startswith("declarative_")
        assert len(knowledge.id) > len("declarative_")
