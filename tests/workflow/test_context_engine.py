"""
Tests for ContextEngine - Phase 1 Foundation Testing
"""

import pytest
from datetime import datetime
from typing import Any

from dana.frameworks.workflow.context_engine import (
    ContextEngine, KnowledgePoint, ContextSnapshot
)


class TestKnowledgePoint:
    """Test suite for KnowledgePoint."""
    
    def test_knowledge_point_creation(self):
        """Test basic knowledge point creation."""
        now = datetime.now()
        kp = KnowledgePoint(
            id="test_id",
            content="Test knowledge",
            source="test_source",
            timestamp=now,
            metadata={"key": "value"},
            tags=["tag1", "tag2"]
        )
        
        assert kp.id == "test_id"
        assert kp.content == "Test knowledge"
        assert kp.source == "test_source"
        assert kp.timestamp == now
        assert kp.metadata == {"key": "value"}
        assert kp.tags == ["tag1", "tag2"]
    
    def test_knowledge_point_timestamp_conversion(self):
        """Test automatic timestamp conversion from string."""
        now_str = datetime.now().isoformat()
        kp = KnowledgePoint(
            id="test_id",
            content="Test",
            source="test",
            timestamp=now_str
        )
        
        assert isinstance(kp.timestamp, datetime)


class TestContextSnapshot:
    """Test suite for ContextSnapshot."""
    
    def test_snapshot_creation(self):
        """Test context snapshot creation."""
        now = datetime.now()
        knowledge_points = [
            KnowledgePoint(
                id="kp1", content="Content 1", source="source1", timestamp=now
            ),
            KnowledgePoint(
                id="kp2", content="Content 2", source="source2", timestamp=now
            )
        ]
        
        snapshot = ContextSnapshot(
            id="snapshot_id",
            timestamp=now,
            knowledge_points=knowledge_points,
            metadata={"version": "1.0"}
        )
        
        assert snapshot.id == "snapshot_id"
        assert snapshot.timestamp == now
        assert len(snapshot.knowledge_points) == 2
        assert snapshot.metadata == {"version": "1.0"}


class TestContextEngine:
    """Test suite for ContextEngine."""
    
    def test_initialization_default(self):
        """Test engine initialization with default parameters."""
        engine = ContextEngine()
        assert engine.max_knowledge_points == 1000
        assert len(engine._knowledge_store) == 0
        assert len(engine._tag_index) == 0
    
    def test_initialization_custom(self):
        """Test engine initialization with custom parameters."""
        engine = ContextEngine(max_knowledge_points=100)
        assert engine.max_knowledge_points == 100
    
    def test_add_knowledge_basic(self):
        """Test basic knowledge addition."""
        engine = ContextEngine()
        
        knowledge_id = engine.add_knowledge(
            content="Test knowledge",
            source="test_source"
        )
        
        assert knowledge_id is not None
        assert len(engine._knowledge_store) == 1
        
        kp = engine.get_knowledge(knowledge_id)
        assert kp is not None
        assert kp.content == "Test knowledge"
        assert kp.source == "test_source"
    
    def test_add_knowledge_with_tags_and_metadata(self):
        """Test knowledge addition with tags and metadata."""
        engine = ContextEngine()
        
        knowledge_id = engine.add_knowledge(
            content="Tagged knowledge",
            source="test",
            tags=["tag1", "tag2"],
            metadata={"priority": "high"}
        )
        
        kp = engine.get_knowledge(knowledge_id)
        assert kp.tags == ["tag1", "tag2"]
        assert kp.metadata == {"priority": "high"}
    
    def test_get_knowledge_not_found(self):
        """Test getting non-existent knowledge."""
        engine = ContextEngine()
        
        kp = engine.get_knowledge("nonexistent")
        assert kp is None
    
    def test_find_by_tag(self):
        """Test finding knowledge by tag."""
        engine = ContextEngine()
        
        engine.add_knowledge("Content 1", "source1", ["tag1", "common"])
        engine.add_knowledge("Content 2", "source2", ["tag2", "common"])
        engine.add_knowledge("Content 3", "source3", ["tag3"])
        
        # Find by single tag
        results = engine.find_by_tag("tag1")
        assert len(results) == 1
        assert results[0].content == "Content 1"
        
        # Find by common tag
        common_results = engine.find_by_tag("common")
        assert len(common_results) == 2
        
        # Find by non-existent tag
        empty_results = engine.find_by_tag("nonexistent")
        assert len(empty_results) == 0
    
    def test_search_knowledge_basic(self):
        """Test basic knowledge search."""
        engine = ContextEngine()
        
        engine.add_knowledge("Python programming guide", "source1")
        engine.add_knowledge("Java programming tutorial", "source2")
        engine.add_knowledge("Data science with Python", "source1")
        
        results = engine.search_knowledge("python")
        assert len(results) == 2
        assert all("python" in kp.content.lower() for kp in results)
    
    def test_search_knowledge_with_filters(self):
        """Test knowledge search with filters."""
        engine = ContextEngine()
        
        engine.add_knowledge(
            "Python basics", "python_docs", ["basics", "python"], {"level": "beginner"}
        )
        engine.add_knowledge(
            "Advanced Python", "python_docs", ["advanced", "python"], {"level": "advanced"}
        )
        engine.add_knowledge(
            "Java basics", "java_docs", ["basics", "java"], {"level": "beginner"}
        )
        
        # Search with source filter
        python_results = engine.search_knowledge("basics", sources=["python_docs"])
        assert len(python_results) == 1
        assert python_results[0].content == "Python basics"
        
        # Search with tag filter
        advanced_results = engine.search_knowledge("python", tags=["advanced"])
        assert len(advanced_results) == 1
        assert advanced_results[0].content == "Advanced Python"
    
    def test_search_knowledge_limit(self):
        """Test knowledge search with limit."""
        engine = ContextEngine()
        
        for i in range(10):
            engine.add_knowledge(f"Knowledge {i}", f"source{i}")
        
        results = engine.search_knowledge("Knowledge", limit=5)
        assert len(results) == 5
    
    def test_create_context_snapshot(self):
        """Test creating context snapshots."""
        engine = ContextEngine()
        
        # Add some knowledge
        for i in range(3):
            engine.add_knowledge(f"Knowledge {i}", f"source{i}")
        
        snapshot_id = engine.create_context_snapshot(
            metadata={"description": "Test snapshot"}
        )
        
        assert snapshot_id is not None
        snapshot = engine.get_context_snapshot(snapshot_id)
        assert snapshot is not None
        assert len(snapshot.knowledge_points) == 3
        assert snapshot.metadata == {"description": "Test snapshot"}
    
    def test_get_context_snapshot_not_found(self):
        """Test getting non-existent snapshot."""
        engine = ContextEngine()
        
        snapshot = engine.get_context_snapshot("nonexistent")
        assert snapshot is None
    
    def test_clear_knowledge_all(self):
        """Test clearing all knowledge."""
        engine = ContextEngine()
        
        engine.add_knowledge("Knowledge 1", "source1")
        engine.add_knowledge("Knowledge 2", "source2")
        
        assert len(engine._knowledge_store) == 2
        
        removed_count = engine.clear_knowledge()
        assert removed_count == 2
        assert len(engine._knowledge_store) == 0
        assert len(engine._tag_index) == 0
    
    def test_clear_knowledge_by_source(self):
        """Test clearing knowledge by source."""
        engine = ContextEngine()
        
        engine.add_knowledge("K1", "source1")
        engine.add_knowledge("K2", "source1")
        engine.add_knowledge("K3", "source2")
        
        removed_count = engine.clear_knowledge(source="source1")
        assert removed_count == 2
        assert len(engine._knowledge_store) == 1
        assert engine._knowledge_store[list(engine._knowledge_store.keys())[0]].source == "source2"
    
    def test_enforce_knowledge_limit(self):
        """Test enforcing knowledge point limit."""
        engine = ContextEngine(max_knowledge_points=3)
        
        # Add more than the limit
        for i in range(5):
            engine.add_knowledge(f"Knowledge {i}", f"source{i}")
        
        assert len(engine._knowledge_store) == 3
        
        stats = engine.get_stats()
        assert stats["total_knowledge_points"] == 3
    
    def test_get_stats(self):
        """Test getting engine statistics."""
        engine = ContextEngine()
        
        engine.add_knowledge("K1", "source1", ["tag1"])
        engine.add_knowledge("K2", "source2", ["tag1", "tag2"])
        engine.add_knowledge("K3", "source1", ["tag2"])
        
        stats = engine.get_stats()
        
        assert stats["total_knowledge_points"] == 3
        assert stats["total_snapshots"] == 0
        assert stats["unique_tags"] == 2
        assert set(stats["sources"]) == {"source1", "source2"}
        assert stats["memory_usage"]["knowledge_store"] == 3
        assert stats["memory_usage"]["tag_index"] == 2
    
    def test_export_import_knowledge(self):
        """Test exporting and importing knowledge."""
        engine = ContextEngine()
        
        # Add knowledge
        engine.add_knowledge("Test content", "test_source", ["tag1"])
        
        # Export
        exported = engine.export_knowledge()
        assert "knowledge_points" in exported
        assert len(exported["knowledge_points"]) == 1
        
        # Clear and import
        engine.clear_knowledge()
        assert len(engine._knowledge_store) == 0
        
        imported = engine.import_knowledge(exported)
        assert imported == 1
        assert len(engine._knowledge_store) == 1
        
        # Verify imported data
        kp = list(engine._knowledge_store.values())[0]
        assert kp.content == "Test content"
        assert kp.source == "test_source"
    
    def test_import_invalid_data(self):
        """Test importing invalid knowledge data."""
        engine = ContextEngine()
        
        # Invalid data structure
        invalid_data = {"invalid": "structure"}
        imported = engine.import_knowledge(invalid_data)
        assert imported == 0
        
        # Missing required fields
        invalid_kp = [{"content": "No id"}]
        imported = engine.import_knowledge({"knowledge_points": invalid_kp})
        assert imported == 0