"""
Tests for WorkflowStep - Phase 1 Foundation Testing
"""

import pytest
from unittest.mock import Mock
from typing import Any

from dana.frameworks.workflow.core.steps.workflow_step import (
    WorkflowStep, StepResult, StepExecutionContext
)
from dana.frameworks.workflow.core.engine.workflow_engine import WorkflowEngine


class TestWorkflowStep:
    """Test suite for WorkflowStep."""
    
    def test_initialization_basic(self):
        """Test basic step initialization."""
        def test_func(x):
            return x + 1
        
        step = WorkflowStep(name="test_step", function=test_func)
        
        assert step.name == "test_step"
        assert step.function is test_func
        assert step.pre_conditions == []
        assert step.post_conditions == []
        assert step.error_handler is None
        assert step.metadata == {}
        assert step.timeout is None
    
    def test_initialization_full(self):
        """Test full step initialization with all parameters."""
        def test_func(x):
            return x + 1
        
        def pre_cond(x, ctx):
            return x > 0
        
        def post_cond(result, ctx):
            return result > 0
        
        def error_handler(error, input_data, context):
            return 0
        
        step = WorkflowStep(
            name="full_step",
            function=test_func,
            pre_conditions=[pre_cond],
            post_conditions=[post_cond],
            error_handler=error_handler,
            metadata={"description": "Test step"},
            timeout=30.0
        )
        
        assert step.name == "full_step"
        assert step.function is test_func
        assert len(step.pre_conditions) == 1
        assert len(step.post_conditions) == 1
        assert step.error_handler is error_handler
        assert step.metadata["description"] == "Test step"
        assert step.timeout == 30.0
    
    def test_basic_execution(self):
        """Test basic step execution."""
        def simple_func(x):
            return x * 2
        
        step = WorkflowStep(name="simple", function=simple_func)
        result = step.execute(5)
        assert result == 10
    
    
    def test_pre_condition_success(self):
        """Test successful pre-condition validation."""
        def test_func(x):
            return x + 1
        
        def pre_condition(x, context):
            return x > 0
        
        step = WorkflowStep(
            name="pre_success",
            function=test_func,
            pre_conditions=[pre_condition]
        )
        
        result = step.execute(5)
        assert result == 6
    
    def test_pre_condition_failure(self):
        """Test pre-condition validation failure."""
        def test_func(x):
            return x + 1
        
        def pre_condition(x, context):
            return x > 10
        
        step = WorkflowStep(
            name="pre_fail",
            function=test_func,
            pre_conditions=[pre_condition]
        )
        
        with pytest.raises(RuntimeError, match="Pre-condition failed"):
            step.execute(5)
    
    def test_post_condition_success(self):
        """Test successful post-condition validation."""
        def test_func(x):
            return x + 1
        
        def post_condition(result, context):
            return result > 0
        
        step = WorkflowStep(
            name="post_success",
            function=test_func,
            post_conditions=[post_condition]
        )
        
        result = step.execute(5)
        assert result == 6
    
    def test_post_condition_failure(self):
        """Test post-condition validation failure."""
        def test_func(x):
            return x - 10
        
        def post_condition(result, context):
            return result > 0
        
        step = WorkflowStep(
            name="post_fail",
            function=test_func,
            post_conditions=[post_condition]
        )
        
        with pytest.raises(RuntimeError, match="Post-condition failed"):
            step.execute(5)
    
    def test_error_handler_with_exception(self):
        """Test error handler with exception."""
        def failing_func(x):
            raise ValueError("Test error")
        
        def error_handler(error, input_data, context):
            return f"Handled: {str(error)}"
        
        step = WorkflowStep(
            name="error_test",
            function=failing_func,
            error_handler=error_handler
        )
        
        result = step.execute(5)
        assert result == "Handled: Test error"
    
    def test_error_handler_without_handler(self):
        """Test exception without error handler."""
        def failing_func(x):
            raise ValueError("Test error")
        
        step = WorkflowStep(name="no_handler", function=failing_func)
        
        with pytest.raises(RuntimeError, match="Step no_handler failed"):
            step.execute(5)
    
    def test_step_composition(self):
        """Test step composition using | operator."""
        def add_one(x):
            return x + 1
        
        def multiply_two(x):
            return x * 2
        
        step1 = WorkflowStep(name="add", function=add_one)
        step2 = WorkflowStep(name="multiply", function=multiply_two)
        
        composed = step1 | step2
        result = composed(5)
        assert result == 12  # (5 + 1) * 2
    
    def test_step_sequential_execution(self):
        """Test sequential execution of multiple workflow steps."""
        def step1(x):
            return x + 1
        
        def step2(x):
            return x * 2
        
        def step3(x):
            return str(x)
        
        s1 = WorkflowStep(name="add", function=step1)
        s2 = WorkflowStep(name="multiply", function=step2)
        s3 = WorkflowStep(name="stringify", function=step3)
        
        # Test sequential execution via workflow engine
        engine = WorkflowEngine()
        result = engine.execute([s1, s2, s3], 5)
        assert result == "12"  # str((5 + 1) * 2)
    
    def test_step_clone(self):
        """Test cloning a workflow step."""
        def test_func(x):
            return x + 1
        
        original = WorkflowStep(
            name="original",
            function=test_func,
            metadata={"version": "1.0"}
        )
        
        cloned = original.clone(name="cloned")
        
        assert cloned.name == "cloned"
        assert cloned.function is test_func
        assert cloned.metadata["version"] == "1.0"
    
    def test_from_function_decorator(self):
        """Test the from_function decorator."""
        
        @WorkflowStep.from_function(name="decorated")
        def decorated_func(x):
            return x + 100
        
        assert isinstance(decorated_func, WorkflowStep)
        assert decorated_func.name == "decorated"
        result = decorated_func.execute(5)
        assert result == 105
    
    def test_from_function_with_conditions(self):
        """Test decorator with conditions."""
        
        def pre_cond(x, context):
            return x > 0
        
        @WorkflowStep.from_function(pre_conditions=[pre_cond])
        def conditional_func(x):
            return x * 2
        
        assert len(conditional_func.pre_conditions) == 1
        result = conditional_func.execute(5)
        assert result == 10
    
    def test_string_representation(self):
        """Test string representation of WorkflowStep."""
        def test_func(x):
            return x
        
        step = WorkflowStep(
            name="test_step",
            function=test_func,
            metadata={"key": "value"}
        )
        
        str_repr = str(step)
        assert "test_step" in str_repr
        assert "metadata" in str_repr


class TestStepExecutionContext:
    """Test suite for StepExecutionContext."""
    
    def test_context_creation(self):
        """Test context creation."""
        context = StepExecutionContext(
            step_id="test_step",
            workflow_id="test_workflow",
            input_data=42
        )
        
        assert context.step_id == "test_step"
        assert context.workflow_id == "test_workflow"
        assert context.input_data == 42
        assert isinstance(context.previous_steps, dict)
        assert isinstance(context.global_context, dict)
        assert isinstance(context.metadata, dict)
    
    def test_context_data_access(self):
        """Test context data access."""
        context = StepExecutionContext(
            step_id="test",
            workflow_id="test",
            input_data=1
        )
        
        context.previous_steps["prev"] = "value"
        context.global_context["global"] = "data"
        context.metadata["meta"] = "info"
        
        assert context.previous_steps["prev"] == "value"
        assert context.global_context["global"] == "data"
        assert context.metadata["meta"] == "info"