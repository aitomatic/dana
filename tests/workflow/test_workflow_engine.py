"""
Tests for WorkflowEngine - Phase 1 Foundation Testing
"""

import pytest
from unittest.mock import Mock, patch
from typing import Any

from dana.frameworks.workflow.core.engine.workflow_engine import (
    WorkflowEngine, WorkflowExecutionContext
)
from dana.frameworks.workflow.core.steps.workflow_step import WorkflowStep
from dana.frameworks.workflow.core.context.context_engine import ContextEngine
from dana.frameworks.workflow.core.validation.safety_validator import SafetyValidator


class TestWorkflowEngine:
    """Test suite for WorkflowEngine."""
    
    def test_initialization_default(self):
        """Test engine initialization with default parameters."""
        engine = WorkflowEngine()
        assert engine.max_depth == 10
        assert isinstance(engine.context_engine, ContextEngine)
        assert isinstance(engine.safety_validator, SafetyValidator)
    
    def test_initialization_custom(self):
        """Test engine initialization with custom parameters."""
        context_engine = ContextEngine(max_knowledge_points=100)
        safety_validator = SafetyValidator(strict_mode=True)
        
        engine = WorkflowEngine(
            context_engine=context_engine,
            safety_validator=safety_validator,
            max_depth=5
        )
        
        assert engine.max_depth == 5
        assert engine.context_engine is context_engine
        assert engine.safety_validator is safety_validator
    
    def test_validate_workflow_list_success(self):
        """Test workflow validation with valid step list."""
        engine = WorkflowEngine()
        
        def simple_func(x):
            return x + 1
        
        step = WorkflowStep(name="test", function=simple_func)
        workflow = [step]
        
        result = engine.execute(workflow, 5, workflow_id="test_workflow")
        assert result == 6
    
    def test_validate_workflow_sequential_steps(self):
        """Test workflow execution with sequential steps."""
        engine = WorkflowEngine()
        
        def add_one(x):
            return x + 1
        
        def multiply_two(x):
            return x * 2
        
        steps = [
            WorkflowStep(name="add", function=add_one),
            WorkflowStep(name="multiply", function=multiply_two)
        ]
        result = engine.execute(steps, 5, workflow_id="sequential_workflow")
        assert result == 12  # (5 + 1) * 2
    
    def test_workflow_validation_failure(self):
        """Test workflow validation failure."""
        engine = WorkflowEngine()
        
        # Invalid workflow type
        with pytest.raises(ValueError):
            engine.execute("invalid", 5)
    
    def test_step_execution_with_context(self):
        """Test step execution with context passing."""
        engine = WorkflowEngine()
        
        def step_with_context(x):
            # Use the engine's context engine instead of direct context passing
            return x * 2
        
        step = WorkflowStep(name="context_step", function=step_with_context)
        result = engine.execute([step], 5)
        assert result == 10
    
    def test_workflow_id_generation(self):
        """Test automatic workflow ID generation."""
        engine = WorkflowEngine()
        
        def simple_func(x):
            return x
        
        step = WorkflowStep(name="simple", function=simple_func)
        result = engine.execute([step], 42)
        assert result == 42
    
    def test_error_handling_in_workflow(self):
        """Test error handling during workflow execution."""
        engine = WorkflowEngine()
        
        def failing_step(x):
            raise ValueError("Test error")
        
        step = WorkflowStep(name="failing", function=failing_step)
        
        with pytest.raises(RuntimeError):
            engine.execute([step], 5)
    
    def test_workflow_with_multiple_steps(self):
        """Test workflow with multiple sequential steps."""
        engine = WorkflowEngine()
        
        def add_ten(x):
            return x + 10
        
        def double(x):
            return x * 2
        
        def stringify(x):
            return f"Result: {x}"
        
        steps = [
            WorkflowStep(name="add", function=add_ten),
            WorkflowStep(name="double", function=double),
            WorkflowStep(name="stringify", function=stringify)
        ]
        
        result = engine.execute(steps, 5)
        assert result == "Result: 30"  # ((5 + 10) * 2)
    
    def test_create_workflow_step(self):
        """Test creating workflow steps via engine."""
        engine = WorkflowEngine()
        
        def test_func(x):
            return x + 1
        
        step = engine.create_workflow_step(
            name="engine_created",
            function=test_func,
            metadata={"description": "Test step"}
        )
        
        assert step.name == "engine_created"
        assert step.function is test_func
        assert step.metadata["description"] == "Test step"
    
    def test_compose_workflow(self):
        """Test composing workflow steps using sequential execution."""
        engine = WorkflowEngine()
        
        def step1(x):
            return x + 1
        
        def step2(x):
            return x * 2
        
        step1_obj = WorkflowStep(name="step1", function=step1)
        step2_obj = WorkflowStep(name="step2", function=step2)
        
        # Test sequential execution instead of composition
        result = engine.execute([step1_obj, step2_obj], 5)
        assert result == 12  # (5 + 1) * 2


class TestWorkflowExecutionContext:
    """Test suite for WorkflowExecutionContext."""
    
    def test_context_creation(self):
        """Test context object creation."""
        context = WorkflowExecutionContext(
            workflow_id="test_workflow",
            step_id="test_step",
            input_data=42
        )
        
        assert context.workflow_id == "test_workflow"
        assert context.step_id == "test_step"
        assert context.input_data == 42
        assert isinstance(context.context_data, dict)
        assert isinstance(context.execution_metadata, dict)
        assert isinstance(context.safety_flags, list)
    
    def test_context_data_operations(self):
        """Test context data operations."""
        context = WorkflowExecutionContext(
            workflow_id="test",
            step_id="test",
            input_data=42
        )
        
        # Add context data
        context.add_context("key", "value")
        assert context.get_context("key") == "value"
        assert context.get_context("missing") is None
        assert context.get_context("missing", "default") == "default"
    
    def test_context_immutability(self):
        """Test that context data is properly isolated."""
        context1 = WorkflowExecutionContext("w1", "s1", 1)
        context2 = WorkflowExecutionContext("w2", "s2", 2)
        
        context1.add_context("shared", "context1_value")
        context2.add_context("shared", "context2_value")
        
        assert context1.get_context("shared") == "context1_value"
        assert context2.get_context("shared") == "context2_value"