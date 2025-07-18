"""
Tests for Phase 3: Context Engineering with KNOWS Integration

These tests verify the advanced context management and KNOWS knowledge extraction
features for the Dana workflow system.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json

from dana.frameworks.workflow.phases.context_engineering import (
    ContextEngineeringEngine, ContextAwareWorkflowEngine, 
    KnowledgeTrace, ContextSnapshot, KNOWSExtractor
)
from dana.frameworks.workflow import WorkflowStep, WorkflowEngine, ContextEngine


class TestKNOWSExtractor:
    """Test KNOWS knowledge extraction system."""
    
    def test_extract_from_step(self):
        """Test knowledge extraction from workflow step."""
        context_engine = ContextEngine()
        extractor = KNOWSExtractor(context_engine)
        
        step = WorkflowStep(
            name="test_step", 
            function=lambda x: x + 1,
            metadata={"description": "Test step"}
        )
        
        knowledge = extractor.extract_from_step(step, {"test": "context"})
        
        assert len(knowledge) >= 1
        assert any("metadata" in kp["content"] for kp in knowledge)
        assert any(kp["source"].startswith("workflow_step_") for kp in knowledge)
    
    def test_extract_from_result(self):
        """Test knowledge extraction from step results."""
        context_engine = ContextEngine()
        extractor = KNOWSExtractor(context_engine)
        
        step = WorkflowStep(name="test_step", function=lambda x: x + 1)
        
        knowledge = extractor.extract_from_result(step, 42, {"test": "context"})
        
        assert len(knowledge) == 1
        assert "42" in knowledge[0]["content"]
        assert "step_result_test_step" in knowledge[0]["source"]
        assert "int" in knowledge[0]["tags"]
    
    def test_extract_from_error(self):
        """Test knowledge extraction from step errors."""
        context_engine = ContextEngine()
        extractor = KNOWSExtractor(context_engine)
        
        step = WorkflowStep(name="test_step", function=lambda x: x + 1)
        error = ValueError("Test error")
        
        knowledge = extractor.extract_from_error(step, error, {"test": "context"})
        
        assert len(knowledge) == 1
        assert "ValueError" in knowledge[0]["content"]
        assert "Test error" in knowledge[0]["content"]
        assert "step_error_test_step" in knowledge[0]["source"]


class TestContextEngineeringEngine:
    """Test ContextEngineeringEngine functionality."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = ContextEngineeringEngine()
        
        assert engine.context_engine is not None
        assert engine.knows_extractor is not None
        assert isinstance(engine.knowledge_traces, list)
        assert isinstance(engine.context_snapshots, dict)
    
    def test_create_context_snapshot(self):
        """Test context snapshot creation."""
        engine = ContextEngineeringEngine()
        
        # Add some knowledge
        engine.context_engine.add_knowledge("Test knowledge", "test_source")
        
        snapshot = engine.create_context_snapshot("test_workflow", "test_stage")
        
        assert snapshot.snapshot_id.startswith("test_workflow_test_stage_")
        assert len(snapshot.knowledge_points) == 1
        assert snapshot.context_metadata["workflow_id"] == "test_workflow"
        assert snapshot.context_metadata["stage"] == "test_stage"
    
    def test_enhance_step_with_context(self):
        """Test step enhancement with context awareness."""
        engine = ContextEngineeringEngine()
        
        def test_func(x):
            return x * 2
        
        step = WorkflowStep(name="test_step", function=test_func)
        enhanced_step = engine.enhance_step_with_context(step)
        
        assert enhanced_step.name == "test_step_context_aware"
        assert enhanced_step.metadata["context_aware"] is True
        assert enhanced_step.metadata["knows_integration"] is True
    
    def test_execute_with_context(self):
        """Test workflow execution with context engineering."""
        engine = ContextEngineeringEngine()
        workflow_engine = WorkflowEngine()
        
        def add_ten(x):
            return x + 10
        
        def double(x):
            return x * 2
        
        steps = [
            WorkflowStep(name="add", function=add_ten),
            WorkflowStep(name="double", function=double)
        ]
        
        result = engine.execute_with_context(workflow_engine, steps, 5, "test_workflow")
        
        assert result == 30  # (5 + 10) * 2
        assert len(engine.knowledge_traces) > 0
        assert len(engine.context_snapshots) == 2  # initial and final
    
    def test_get_knowledge_traces(self):
        """Test knowledge trace retrieval."""
        engine = ContextEngineeringEngine()
        
        # Add a trace
        trace = KnowledgeTrace(
            step_id="test_step",
            workflow_id="test_workflow",
            timestamp=datetime.now(),
            source="test",
            transformation="test_transformation",
            input_context={"test": "input"},
            output_context={"test": "output"}
        )
        engine.knowledge_traces.append(trace)
        
        traces = engine.get_knowledge_traces("test_workflow")
        assert len(traces) == 1
        assert traces[0].step_id == "test_step"
    
    def test_search_context_knowledge(self):
        """Test searching context knowledge."""
        engine = ContextEngineeringEngine()
        
        # Add knowledge
        engine.context_engine.add_knowledge(
            "Test knowledge point", 
            "test_source", 
            tags=["test", "knowledge"]
        )
        
        results = engine.search_context_knowledge("Test", tags=["test"])
        assert len(results) == 1
        assert results[0]["content"] == "Test knowledge point"
    
    def test_export_context_state(self):
        """Test context state export."""
        engine = ContextEngineeringEngine()
        
        # Add some knowledge and traces
        engine.context_engine.add_knowledge("Test knowledge", "test_source")
        
        trace = KnowledgeTrace(
            step_id="test_step",
            workflow_id="test_workflow",
            timestamp=datetime.now(),
            source="test",
            transformation="test_transformation",
            input_context={"test": "input"},
            output_context={"test": "output"}
        )
        engine.knowledge_traces.append(trace)
        
        state = engine.export_context_state("test_workflow")
        
        assert state["workflow_id"] == "test_workflow"
        assert len(state["knowledge_traces"]) == 1
        assert len(state["context_stats"]) > 0


class TestContextAwareWorkflowEngine:
    """Test ContextAwareWorkflowEngine high-level interface."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = ContextAwareWorkflowEngine()
        
        assert engine.workflow_engine is not None
        assert engine.context_engine is not None
        assert engine.context_engineering is not None
    
    def test_run_workflow(self):
        """Test running workflow with context engineering."""
        engine = ContextAwareWorkflowEngine()
        
        def simple_func(x):
            return x + 1
        
        steps = [WorkflowStep(name="test", function=simple_func)]
        
        result = engine.run(steps, 42, "test_workflow")
        
        assert result["result"] == 43
        assert result["workflow_id"] == "test_workflow"
        assert result["context_state"] is not None
        assert result["context_snapshots"] >= 2
    
    def test_run_workflow_without_id(self):
        """Test running workflow without explicit ID."""
        engine = ContextAwareWorkflowEngine()
        
        def simple_func(x):
            return x + 1
        
        steps = [WorkflowStep(name="test", function=simple_func)]
        
        result = engine.run(steps, 42)
        
        assert result["result"] == 43
        assert "context_workflow_" in result["workflow_id"]


class TestContextEngineeringIntegration:
    """Integration tests for Phase 3."""
    
    def test_end_to_end_context_workflow(self):
        """Test complete context-aware workflow execution."""
        engine = ContextAwareWorkflowEngine()
        
        def process_data(x):
            return x ** 2
        
        def validate_result(x):
            return x * 1  # Simple pass-through instead of boolean check
        
        def format_output(x):
            return f"Result: {x}"
        
        steps = [
            WorkflowStep(name="process", function=process_data),
            WorkflowStep(name="validate", function=validate_result),
            WorkflowStep(name="format", function=format_output)
        ]
        
        result = engine.run(steps, 5)
        
        assert result["result"] == "Result: 25"
        assert result["context_snapshots"] >= 2  # Initial and final
        
        # Verify context state structure
        context_state = result["context_state"]
        assert "knowledge_traces" in context_state
        assert "context_snapshots" in context_state
    
    def test_error_handling_with_context(self):
        """Test error handling with context extraction."""
        engine = ContextAwareWorkflowEngine()
        
        def failing_step(x):
            raise ValueError("Test error")
        
        def error_handler(error, input_data, context):
            return f"Handled: {str(error)}"
        
        steps = [
            WorkflowStep(
                name="failing", 
                function=failing_step,
                error_handler=error_handler
            )
        ]
        
        result = engine.run(steps, 42)
        
        assert result["result"] == "Handled: Test error"
        
        # Should have error knowledge
        error_knowledge = [
            kp for kp in engine.context_engineering.search_context_knowledge("error")
            if "ValueError" in kp["content"]
        ]
        assert len(error_knowledge) > 0
    
    def test_complex_workflow_context(self):
        """Test complex workflow with rich context."""
        engine = ContextAwareWorkflowEngine()
        
        def step1(x):
            return {"data": x, "processed": True}
        
        def step2(data_dict):
            return data_dict["data"] * 2
        
        def step3(result):
            return {"final": result, "status": "complete"}
        
        # Create steps with metadata
        steps = [
            WorkflowStep(
                name="initialize", 
                function=step1,
                metadata={"purpose": "data_initialization", "priority": "high"}
            ),
            WorkflowStep(
                name="process", 
                function=step2,
                metadata={"purpose": "data_processing", "algorithm": "multiplication"}
            ),
            WorkflowStep(
                name="finalize", 
                function=step3,
                metadata={"purpose": "result_finalization", "format": "structured"}
            )
        ]
        
        result = engine.run(steps, 7)
        
        assert result["result"] == {"final": 14, "status": "complete"}
        
        # Verify rich context knowledge
        metadata_knowledge = [
            kp for kp in engine.context_engineering.search_context_knowledge("metadata")
        ]
        assert len(metadata_knowledge) > 0
        
        # Verify specific metadata was captured
        priority_knowledge = [
            kp for kp in engine.context_engineering.search_context_knowledge("high")
        ]
        assert len(priority_knowledge) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])