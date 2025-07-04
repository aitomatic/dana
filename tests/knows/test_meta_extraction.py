"""
Tests for Phase 2: Meta Knowledge Extraction and Categorization

This module tests the MetaKnowledgeExtractor and KnowledgeCategorizer components.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from dana.common.types import BaseResponse
from dana.frameworks.knows.core.base import Document, KnowledgePoint
from dana.frameworks.knows.extraction.meta.categorizer import CategoryRelationship, KnowledgeCategorizer
from dana.frameworks.knows.extraction.meta.extractor import MetaKnowledgeExtractor


class TestMetaKnowledgeExtractor:
    """Test suite for MetaKnowledgeExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock LLM resource
        self.mock_llm = Mock()
        self.extractor = MetaKnowledgeExtractor(llm_resource=self.mock_llm, confidence_threshold=0.7, max_knowledge_points=5)

        # Sample document
        self.sample_document = Document(
            id="test_doc_1",
            source="test.txt",
            format="txt",
            content="This is a quality control process for semiconductor manufacturing. "
            "The process involves temperature monitoring and defect detection. "
            "Key metrics include accuracy of 95% and throughput of 100 units per hour.",
            metadata={"source": "test"},
            created_at=datetime.now(),
        )

    def test_extractor_initialization(self):
        """Test MetaKnowledgeExtractor initialization."""
        assert self.extractor.confidence_threshold == 0.7
        assert self.extractor.max_knowledge_points == 5
        assert self.extractor.llm_resource is not None

    def test_validate_input_success(self):
        """Test successful input validation."""
        assert self.extractor.validate_input(self.sample_document) is True

    def test_validate_input_invalid_type(self):
        """Test input validation with invalid type."""
        assert self.extractor.validate_input("not a document") is False

    def test_validate_input_empty_content(self):
        """Test input validation with empty content."""
        # Create a mock document with empty content to test validation
        from unittest.mock import Mock

        empty_doc = Mock()
        empty_doc.content = ""
        empty_doc.id = "empty"
        empty_doc.format = "txt"
        assert self.extractor.validate_input(empty_doc) is False

    def test_validate_input_large_document(self):
        """Test input validation with large document."""
        large_doc = Document(
            id="large",
            source="large.txt",
            format="txt",
            content="x" * 60000,  # 60KB content
            metadata={},
            created_at=datetime.now(),
        )
        # Should still be valid but with warning
        assert self.extractor.validate_input(large_doc) is True

    def test_extract_response_text_string(self):
        """Test extracting text from string response."""
        response = "This is a direct string response"
        result = self.extractor._extract_response_text(response)
        assert result == "This is a direct string response"

    def test_extract_response_text_openai_format(self):
        """Test extracting text from OpenAI format response."""
        response = {"choices": [{"message": {"content": "Extracted knowledge point"}}]}
        result = self.extractor._extract_response_text(response)
        assert result == "Extracted knowledge point"

    def test_extract_response_text_content_format(self):
        """Test extracting text from direct content format."""
        response = {"content": "Direct content response"}
        result = self.extractor._extract_response_text(response)
        assert result == "Direct content response"

    def test_parse_llm_response_valid_json(self):
        """Test parsing valid JSON response."""
        json_response = json.dumps(
            [
                {
                    "content": "Temperature monitoring is critical",
                    "type": "process",
                    "confidence": 0.9,
                    "context": {"domain": "manufacturing", "keywords": ["temperature", "monitoring"]},
                }
            ]
        )

        result = self.extractor._parse_llm_response(json_response, self.sample_document)

        assert len(result) == 1
        assert result[0].content == "Temperature monitoring is critical"
        assert result[0].type == "process"
        assert result[0].confidence == 0.9

    def test_parse_llm_response_markdown_wrapped(self):
        """Test parsing JSON wrapped in markdown."""
        markdown_response = '```json\n[{"content": "Test", "type": "fact", "confidence": 0.8, "context": {}}]\n```'

        result = self.extractor._parse_llm_response(markdown_response, self.sample_document)

        assert len(result) == 1
        assert result[0].content == "Test"

    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        invalid_response = "This is not JSON"

        result = self.extractor._parse_llm_response(invalid_response, self.sample_document)

        assert result == []

    def test_create_knowledge_point_valid(self):
        """Test creating knowledge point from valid data."""
        data = {"content": "Quality control process", "type": "process", "confidence": 0.85, "context": {"domain": "manufacturing"}}

        kp = self.extractor._create_knowledge_point(data, self.sample_document)

        assert kp is not None
        assert kp.content == "Quality control process"
        assert kp.type == "process"
        assert kp.confidence == 0.85
        assert kp.context["source_document_id"] == self.sample_document.id

    def test_create_knowledge_point_invalid_content(self):
        """Test creating knowledge point with invalid content."""
        data = {
            "content": "",  # Empty content
            "type": "process",
            "confidence": 0.85,
        }

        kp = self.extractor._create_knowledge_point(data, self.sample_document)

        assert kp is None

    def test_create_knowledge_point_invalid_confidence(self):
        """Test creating knowledge point with invalid confidence."""
        data = {
            "content": "Valid content",
            "type": "process",
            "confidence": 1.5,  # Invalid confidence > 1.0
        }

        kp = self.extractor._create_knowledge_point(data, self.sample_document)

        assert kp is not None
        assert kp.confidence == 0.5  # Should default to 0.5

    def test_is_potentially_important_true(self):
        """Test identifying important sentences."""
        important_sentence = "The quality control process is critical for ensuring product standards."

        result = self.extractor._is_potentially_important(important_sentence)

        assert result is True

    def test_is_potentially_important_false(self):
        """Test identifying unimportant sentences."""
        unimportant_sentence = "The weather is nice today."

        result = self.extractor._is_potentially_important(unimportant_sentence)

        assert result is False

    def test_fallback_extraction(self):
        """Test fallback extraction mechanism."""
        result = self.extractor._fallback_extraction(self.sample_document)

        assert isinstance(result, list)
        assert len(result) > 0

        # Check that all fallback points have correct metadata
        for kp in result:
            assert kp.metadata.get("is_fallback") is True
            assert kp.confidence == 0.5
            assert kp.type == "fact"

    @patch("dana.frameworks.knows.extraction.meta.extractor.MetaKnowledgeExtractor._extract_with_llm")
    def test_process_success(self, mock_extract):
        """Test successful processing of document."""
        # Mock LLM extraction
        mock_kp = KnowledgePoint(
            id="kp_1", type="process", content="Temperature monitoring process", context={"test": True}, confidence=0.8, metadata={}
        )
        mock_extract.return_value = [mock_kp]

        result = self.extractor.process(self.sample_document)

        assert len(result) == 1
        assert result[0].content == "Temperature monitoring process"

    @patch("dana.frameworks.knows.extraction.meta.extractor.MetaKnowledgeExtractor._extract_with_llm")
    def test_process_with_filtering(self, mock_extract):
        """Test processing with confidence filtering."""
        # Mock extraction with mixed confidence scores
        mock_kps = [
            KnowledgePoint(id="kp_1", type="process", content="High confidence", context={}, confidence=0.9, metadata={}),
            KnowledgePoint(id="kp_2", type="fact", content="Low confidence", context={}, confidence=0.3, metadata={}),  # Below threshold
        ]
        mock_extract.return_value = mock_kps

        result = self.extractor.process(self.sample_document)

        # Should only return high confidence points
        assert len(result) == 1
        assert result[0].content == "High confidence"

    @patch("dana.frameworks.knows.extraction.meta.extractor.MetaKnowledgeExtractor._extract_with_llm")
    def test_process_with_limit(self, mock_extract):
        """Test processing with knowledge point limit."""
        # Mock extraction with many points
        mock_kps = [
            KnowledgePoint(id=f"kp_{i}", type="process", content=f"Content {i}", context={}, confidence=0.8, metadata={})
            for i in range(10)  # More than the limit of 5
        ]
        mock_extract.return_value = mock_kps

        result = self.extractor.process(self.sample_document)

        # Should limit to max_knowledge_points
        assert len(result) == 5

    def test_process_invalid_input(self):
        """Test processing with invalid input."""
        with pytest.raises(ValueError, match="Invalid document provided"):
            self.extractor.process("not a document")

    @patch("dana.frameworks.knows.extraction.meta.extractor.MetaKnowledgeExtractor._extract_with_llm")
    def test_process_llm_failure_fallback(self, mock_extract):
        """Test fallback when LLM extraction fails."""
        # Mock LLM failure
        mock_extract.side_effect = Exception("LLM failed")

        result = self.extractor.process(self.sample_document)

        # Should return fallback results
        assert isinstance(result, list)
        # Fallback results should have is_fallback metadata
        if result:
            assert result[0].metadata.get("is_fallback") is True


class TestKnowledgeCategorizer:
    """Test suite for KnowledgeCategorizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.categorizer = KnowledgeCategorizer(similarity_threshold=0.6)

        # Sample knowledge points
        self.sample_knowledge_points = [
            KnowledgePoint(
                id="kp_1",
                type="process",
                content="Temperature monitoring is a critical quality control process",
                context={"domain": "manufacturing"},
                confidence=0.9,
                metadata={"extracted_from": "doc_1"},
            ),
            KnowledgePoint(
                id="kp_2",
                type="metric",
                content="Accuracy should be maintained at 95% or higher",
                context={"domain": "manufacturing"},
                confidence=0.8,
                metadata={"extracted_from": "doc_1"},
            ),
            KnowledgePoint(
                id="kp_3",
                type="problem",
                content="Defects can occur due to temperature variations",
                context={"domain": "manufacturing"},
                confidence=0.7,
                metadata={"extracted_from": "doc_1"},
            ),
        ]

    def test_categorizer_initialization(self):
        """Test KnowledgeCategorizer initialization."""
        assert self.categorizer.similarity_threshold == 0.6
        assert len(self.categorizer.categories) == 7  # Default categories
        assert "process" in self.categorizer.category_index

    def test_validate_input_success(self):
        """Test successful input validation."""
        assert self.categorizer.validate_input(self.sample_knowledge_points) is True

    def test_validate_input_empty_list(self):
        """Test input validation with empty list."""
        assert self.categorizer.validate_input([]) is False

    def test_validate_input_invalid_type(self):
        """Test input validation with invalid type."""
        assert self.categorizer.validate_input("not a list") is False

    def test_validate_input_invalid_items(self):
        """Test input validation with invalid items."""
        invalid_list = ["not", "knowledge", "points"]
        assert self.categorizer.validate_input(invalid_list) is False

    def test_categorize_knowledge_point_existing_type(self):
        """Test categorizing knowledge point with existing type."""
        kp = self.sample_knowledge_points[0]  # Has type "process"

        assignments = self.categorizer._categorize_knowledge_point(kp)

        # Should have high confidence assignment for existing type
        assert len(assignments) >= 1
        assert assignments[0]["category_id"] == "process"
        assert assignments[0]["confidence"] == 0.9
        assert assignments[0]["relationship_type"] == "exact"

    def test_categorize_knowledge_point_keyword_matching(self):
        """Test categorizing knowledge point by keyword matching."""
        # Create knowledge point without existing type
        kp = KnowledgePoint(
            id="kp_test",
            type="",  # No existing type
            content="This is a best practice recommendation for quality",
            context={},
            confidence=0.8,
            metadata={},
        )

        assignments = self.categorizer._categorize_knowledge_point(kp)

        # Should match "best_practice" category
        best_practice_assignments = [a for a in assignments if a["category_id"] == "best_practice"]
        assert len(best_practice_assignments) > 0
        assert best_practice_assignments[0]["confidence"] >= 0.6

    def test_calculate_keyword_similarity(self):
        """Test keyword similarity calculation."""
        text = "this is a quality control process with standard procedures"
        keywords = ["process", "procedure", "control"]

        similarity = self.categorizer._calculate_keyword_similarity(text, keywords)

        # Should find all 3 keywords, so 3/3 = 1.0, boosted to 1.0 (max)
        assert similarity == 1.0

    def test_calculate_keyword_similarity_no_matches(self):
        """Test keyword similarity with no matches."""
        text = "this text has no relevant terms"
        keywords = ["process", "procedure", "control"]

        similarity = self.categorizer._calculate_keyword_similarity(text, keywords)

        assert similarity == 0.0

    def test_determine_relationship_type(self):
        """Test relationship type determination."""
        assert self.categorizer._determine_relationship_type(0.9) == "exact"
        assert self.categorizer._determine_relationship_type(0.7) == "partial"
        assert self.categorizer._determine_relationship_type(0.5) == "related"

    def test_calculate_content_similarity(self):
        """Test content similarity calculation."""
        content1 = "temperature monitoring quality control"
        content2 = "quality control temperature measurement"

        similarity = self.categorizer._calculate_content_similarity(content1, content2)

        # Should have shared words: "temperature", "quality", "control"
        assert similarity > 0.5

    def test_calculate_content_similarity_no_overlap(self):
        """Test content similarity with no word overlap."""
        content1 = "apple banana cherry"
        content2 = "dog elephant fish"

        similarity = self.categorizer._calculate_content_similarity(content1, content2)

        assert similarity == 0.0

    def test_have_contextual_relationship_same_document(self):
        """Test contextual relationship detection for same document."""
        kp1 = KnowledgePoint(
            id="kp1", type="process", content="Test 1", context={"source_document_id": "doc_1"}, confidence=0.8, metadata={}
        )
        kp2 = KnowledgePoint(id="kp2", type="fact", content="Test 2", context={"source_document_id": "doc_1"}, confidence=0.8, metadata={})

        result = self.categorizer._have_contextual_relationship(kp1, kp2)

        assert result is True

    def test_have_contextual_relationship_shared_keywords(self):
        """Test contextual relationship detection for shared keywords."""
        kp1 = KnowledgePoint(
            id="kp1",
            type="process",
            content="Test 1",
            context={"keywords": ["manufacturing", "quality", "control"]},
            confidence=0.8,
            metadata={},
        )
        kp2 = KnowledgePoint(
            id="kp2",
            type="fact",
            content="Test 2",
            context={"keywords": ["manufacturing", "quality", "testing"]},
            confidence=0.8,
            metadata={},
        )

        result = self.categorizer._have_contextual_relationship(kp1, kp2)

        assert result is True  # 2+ shared keywords

    def test_have_contextual_relationship_false(self):
        """Test contextual relationship detection returning false."""
        kp1 = KnowledgePoint(
            id="kp1", type="process", content="Test 1", context={"source_document_id": "doc_1"}, confidence=0.8, metadata={}
        )
        kp2 = KnowledgePoint(id="kp2", type="fact", content="Test 2", context={"source_document_id": "doc_2"}, confidence=0.8, metadata={})

        result = self.categorizer._have_contextual_relationship(kp1, kp2)

        assert result is False

    def test_find_shared_context(self):
        """Test finding shared context between knowledge points."""
        kp1 = KnowledgePoint(
            id="kp1",
            type="process",
            content="Test 1",
            context={"domain": "manufacturing", "level": "advanced", "unique1": "value1"},
            confidence=0.8,
            metadata={},
        )
        kp2 = KnowledgePoint(
            id="kp2",
            type="fact",
            content="Test 2",
            context={"domain": "manufacturing", "level": "advanced", "unique2": "value2"},
            confidence=0.8,
            metadata={},
        )

        shared = self.categorizer._find_shared_context(kp1, kp2)

        assert shared["domain"] == "manufacturing"
        assert shared["level"] == "advanced"
        assert "unique1" not in shared
        assert "unique2" not in shared

    def test_build_category_hierarchy(self):
        """Test building category hierarchy."""
        hierarchy = self.categorizer._build_category_hierarchy()

        assert "root_categories" in hierarchy
        assert "category_tree" in hierarchy
        assert len(hierarchy["root_categories"]) == 7  # All default categories are root
        assert len(hierarchy["category_tree"]) == 7

        # Check structure of one category
        process_category = hierarchy["category_tree"]["process"]
        assert process_category["name"] == "Process"
        assert "keywords" in process_category

    def test_generate_categorization_summary(self):
        """Test generating categorization summary."""
        categorized_points = [
            {"knowledge_point": self.sample_knowledge_points[0], "categories": []},
            {"knowledge_point": self.sample_knowledge_points[1], "categories": []},
        ]

        relationships = [
            CategoryRelationship("kp_1", "process", 0.9, "exact"),
            CategoryRelationship("kp_2", "metric", 0.8, "partial"),
            CategoryRelationship("kp_1", "fact", 0.7, "related"),
        ]

        summary = self.categorizer._generate_categorization_summary(categorized_points, relationships)

        assert summary["total_knowledge_points"] == 2
        assert summary["total_categories_used"] == 3
        assert summary["category_distribution"]["process"] == 1
        assert summary["category_distribution"]["metric"] == 1
        assert summary["category_distribution"]["fact"] == 1
        assert summary["high_confidence_assignments"] == 2  # >= 0.8
        assert summary["low_confidence_assignments"] == 0  # < 0.6

    def test_process_success(self):
        """Test successful processing of knowledge points."""
        result = self.categorizer.process(self.sample_knowledge_points)

        assert "categorized_points" in result
        assert "category_relationships" in result
        assert "point_relationships" in result
        assert "category_hierarchy" in result
        assert "summary" in result

        # Check categorized points
        assert len(result["categorized_points"]) == 3

        # Check that each point has categories
        for cp in result["categorized_points"]:
            assert "knowledge_point" in cp
            assert "categories" in cp
            assert isinstance(cp["categories"], list)

        # Check relationships
        assert isinstance(result["category_relationships"], list)
        assert len(result["category_relationships"]) > 0

        # Check summary
        summary = result["summary"]
        assert summary["total_knowledge_points"] == 3
        assert isinstance(summary["category_distribution"], dict)

    def test_process_invalid_input(self):
        """Test processing with invalid input."""
        with pytest.raises(ValueError, match="Invalid knowledge points provided"):
            self.categorizer.process("not a list")

    def test_map_knowledge_point_relationships(self):
        """Test mapping relationships between knowledge points."""
        relationships = self.categorizer._map_knowledge_point_relationships(self.sample_knowledge_points)

        # Should find some type of relationships (contextual or content-based)
        assert isinstance(relationships, list)

        # Check that all points have same document source, so should find contextual relationships
        # But since our test data doesn't have 'source_document_id', check for any relationships
        if relationships:
            rel = relationships[0]
            assert "source_id" in rel
            assert "target_id" in rel
            assert "strength" in rel
            assert "metadata" in rel

        # Check if we can find relationships by improving test data
        # Add source_document_id to context to test contextual relationships
        enhanced_kps = []
        for kp in self.sample_knowledge_points:
            enhanced_kp = KnowledgePoint(
                id=kp.id,
                type=kp.type,
                content=kp.content,
                context={**kp.context, "source_document_id": "doc_1"},
                confidence=kp.confidence,
                metadata=kp.metadata,
            )
            enhanced_kps.append(enhanced_kp)

        enhanced_relationships = self.categorizer._map_knowledge_point_relationships(enhanced_kps)
        contextual_rels = [r for r in enhanced_relationships if r["relationship_type"] == "contextual"]
        assert len(contextual_rels) > 0


class TestPhase2Integration:
    """Integration tests for Phase 2 components."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.mock_llm = Mock()
        self.extractor = MetaKnowledgeExtractor(llm_resource=self.mock_llm, confidence_threshold=0.6, max_knowledge_points=10)
        self.categorizer = KnowledgeCategorizer(similarity_threshold=0.5)

    def test_end_to_end_pipeline(self):
        """Test complete Phase 2 pipeline from document to categorized knowledge points."""
        # Create test document
        document = Document(
            id="integration_test",
            source="test_integration.txt",
            format="txt",
            content="Quality control is a critical process in manufacturing. "
            "Temperature monitoring ensures product quality. "
            "Defect detection algorithms achieve 95% accuracy. "
            "Best practices recommend regular calibration procedures.",
            metadata={"test": True},
            created_at=datetime.now(),
        )

        # Mock successful LLM response
        mock_response = BaseResponse(
            success=True,
            content={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                [
                                    {
                                        "content": "Quality control is critical for manufacturing",
                                        "type": "process",
                                        "confidence": 0.9,
                                        "context": {"domain": "manufacturing", "keywords": ["quality", "control"]},
                                    },
                                    {
                                        "content": "Defect detection accuracy is 95%",
                                        "type": "metric",
                                        "confidence": 0.8,
                                        "context": {"domain": "manufacturing", "keywords": ["accuracy", "detection"]},
                                    },
                                    {
                                        "content": "Regular calibration is recommended",
                                        "type": "best_practice",
                                        "confidence": 0.7,
                                        "context": {"domain": "manufacturing", "keywords": ["calibration", "recommended"]},
                                    },
                                ]
                            )
                        }
                    }
                ]
            },
        )
        self.mock_llm.query_sync.return_value = mock_response

        # Step 1: Extract knowledge points
        knowledge_points = self.extractor.process(document)

        assert len(knowledge_points) == 3
        assert knowledge_points[0].type == "process"
        assert knowledge_points[1].type == "metric"
        assert knowledge_points[2].type == "best_practice"

        # Step 2: Categorize knowledge points
        categorization_result = self.categorizer.process(knowledge_points)

        # Verify categorization results
        assert len(categorization_result["categorized_points"]) == 3
        assert isinstance(categorization_result["category_relationships"], list)
        assert len(categorization_result["category_relationships"]) > 0

        # Verify summary
        summary = categorization_result["summary"]
        assert summary["total_knowledge_points"] == 3
        assert summary["total_categories_used"] >= 3

        # Verify relationships between points
        point_relationships = categorization_result["point_relationships"]
        contextual_rels = [r for r in point_relationships if r["relationship_type"] == "contextual"]
        assert len(contextual_rels) > 0  # Should find relationships between points from same document

    def test_phase_2_with_fallback(self):
        """Test Phase 2 pipeline with LLM fallback mechanism."""
        document = Document(
            id="fallback_test",
            source="fallback.txt",
            format="txt",
            content="This document tests the fallback extraction mechanism when LLM fails.",
            metadata={"test": True},
            created_at=datetime.now(),
        )

        # Mock LLM failure
        mock_response = BaseResponse(success=False, error="LLM service unavailable")
        self.mock_llm.query_sync.return_value = mock_response

        # Should use fallback extraction
        knowledge_points = self.extractor.process(document)

        # Should get fallback results
        assert isinstance(knowledge_points, list)
        if knowledge_points:
            assert knowledge_points[0].metadata.get("is_fallback") is True
            assert knowledge_points[0].confidence == 0.5

        # Categorization should still work with fallback points
        if knowledge_points:
            categorization_result = self.categorizer.process(knowledge_points)
            assert "categorized_points" in categorization_result
            assert len(categorization_result["categorized_points"]) == len(knowledge_points)
