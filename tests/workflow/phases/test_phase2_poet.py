"""
Tests for Phase 2: POET Integration

These tests verify the integration between the Dana workflow system
and the POET framework for runtime objectives and validation.
"""

import pytest
from unittest.mock import Mock, patch

from dana.frameworks.workflow.phases.poet_integration import (
    POETRuntimeEngine, POETWorkflowEngine, POETObjective
)
from dana.frameworks.workflow.core import WorkflowStep, WorkflowEngine
from dana.frameworks.poet.core.types import POETConfig


class TestPOETObjective:
    """Test POETObjective creation and validation."""
    
    def test_objective_creation(self):
        """Test basic POETObjective creation."""
        objective = POETObjective(
            name="test_objective",
            description="Test objective",
            criteria={"timeout": 30},
            priority=1
        )
        
        assert objective.name == "test_objective"
        assert objective.description == "Test objective"
        assert objective.criteria == {"timeout": 30}
        assert objective.priority == 1
        assert objective.metadata == {}
        
    def test_objective_with_metadata(self):
        """Test POETObjective with metadata."""
        objective = POETObjective(
            name="test_objective",
            description="Test objective",
            criteria={},
            metadata={"tag": "test"}
        )
        
        assert objective.metadata == {"tag": "test"}


class TestPOETRuntimeEngine:
    """Test POETRuntimeEngine functionality."""
    
    def test_initialization(self):
        """Test engine initialization with default parameters."""
        engine = POETRuntimeEngine()
        
        assert engine.config is not None
        assert engine.context_engine is not None
        assert engine.safety_validator is not None
        assert engine.operate_phase is not None
        assert engine._objectives == []
        
    def test_add_objective(self):
        """Test adding objectives to the engine."""
        engine = POETRuntimeEngine()
        objective = POETObjective(name="test", description="Test", criteria={})
        
        engine.add_objective(objective)
        
        assert len(engine._objectives) == 1
        assert engine._objectives[0] == objective
        
    def test_infer_objectives_complex_workflow(self):
        """Test objective inference for complex workflows."""
        engine = POETRuntimeEngine()
        
        def test_func(x):
            return x + 1
            
        steps = [WorkflowStep(name=f"step_{i}", function=test_func) for i in range(15)]
        
        objectives = engine.infer_objectives(steps, {})
        
        # Should infer performance optimization due to complexity
        performance_obj = next((obj for obj in objectives if obj.name == "optimize_performance"), None)
        assert performance_obj is not None
        assert "complexity" in performance_obj.description.lower()
        
    def test_infer_objectives_security_detection(self):
        """Test objective inference for security-sensitive workflows."""
        engine = POETRuntimeEngine()
        
        def process_password(x):
            return x
            
        steps = [WorkflowStep(name="process_user_password", function=process_password)]
        
        objectives = engine.infer_objectives(steps, {})
        
        # Should infer security enhancement
        security_obj = next((obj for obj in objectives if obj.name == "enhance_security"), None)
        assert security_obj is not None
        assert "security" in security_obj.description.lower()
        
    def test_infer_objectives_business_critical(self):
        """Test objective inference for business-critical workflows."""
        engine = POETRuntimeEngine()
        
        def test_func(x):
            return x
            
        steps = [WorkflowStep(name="test", function=test_func)]
        context = {"business_critical": True}
        
        objectives = engine.infer_objectives(steps, context)
        
        # Should infer reliability guarantee
        reliability_obj = next((obj for obj in objectives if obj.name == "ensure_reliability"), None)
        assert reliability_obj is not None
        assert "business critical" in reliability_obj.description.lower()
        
    def test_create_validation_gate(self):
        """Test validation gate creation."""
        engine = POETRuntimeEngine()
        
        objective = POETObjective(
            name="optimize_performance",
            description="Test performance optimization",
            criteria={"timeout": 30}
        )
        
        gate = engine.create_validation_gate(objective)
        
        step = WorkflowStep(name="test_step", function=lambda x: x)
        result = gate(step, {})
        
        assert isinstance(result, bool)
        
    def test_enhance_step_with_objective(self):
        """Test step enhancement based on objectives."""
        engine = POETRuntimeEngine()
        
        def test_func(x):
            return x
            
        step = WorkflowStep(name="test", function=test_func)
        objective = POETObjective(
            name="ensure_reliability",
            description="Test reliability",
            criteria={"retry_count": 3}
        )
        
        enhanced_step = engine.enhance_step_with_objective(step, objective)
        
        assert enhanced_step.name == "test_enhanced"
        assert enhanced_step.metadata["retry_count"] == 3
        
    def test_execute_with_poet(self):
        """Test end-to-end execution with POET integration."""
        engine = POETRuntimeEngine()
        
        def add_ten(x):
            return x + 10
            
        def double(x):
            return x * 2
            
        steps = [
            WorkflowStep(name="add", function=add_ten),
            WorkflowStep(name="double", function=double)
        ]
        
        result = engine.execute_with_poet(steps, 5)
        
        assert result == 30  # (5 + 10) * 2


class TestPOETWorkflowEngine:
    """Test POETWorkflowEngine high-level interface."""
    
    def test_initialization(self):
        """Test POETWorkflowEngine initialization."""
        engine = POETWorkflowEngine()
        
        assert engine.runtime_engine is not None
        
    def test_add_objective_via_interface(self):
        """Test adding objectives via high-level interface."""
        engine = POETWorkflowEngine()
        
        engine.add_objective(
            name="test_objective",
            description="Test objective",
            criteria={"timeout": 30}
        )
        
        assert len(engine.runtime_engine._objectives) == 1
        assert engine.runtime_engine._objectives[0].name == "test_objective"
        
    def test_run_workflow(self):
        """Test running workflow through POET engine."""
        engine = POETWorkflowEngine()
        
        def test_func(x):
            return x + 1
            
        steps = [WorkflowStep(name="test", function=test_func)]
        
        result = engine.run(steps, 42)
        
        assert result == 43


class TestPOETIntegrationEdgeCases:
    """Test edge cases for POET integration."""
    
    def test_empty_objectives(self):
        """Test execution with no objectives."""
        engine = POETRuntimeEngine()
        
        def test_func(x):
            return x
            
        steps = [WorkflowStep(name="test", function=test_func)]
        
        result = engine.execute_with_poet(steps, 5, {})
        assert result == 5
        
    def test_empty_workflow(self):
        """Test execution with empty workflow."""
        engine = POETRuntimeEngine()
        
        with pytest.raises(RuntimeError):
            engine.execute_with_poet([], 5, {})
            
    def test_objective_with_complex_criteria(self):
        """Test objective with complex criteria."""
        engine = POETRuntimeEngine()
        
        objective = POETObjective(
            name="complex_test",
            description="Test complex criteria",
            criteria={
                "timeout": 30,
                "retry_count": 3,
                "fallback_enabled": True,
                "validation_level": "strict"
            }
        )
        
        gate = engine.create_validation_gate(objective)
        step = WorkflowStep(name="test", function=lambda x: x)
        
        # Should not raise exception
        result = gate(step, {})
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])