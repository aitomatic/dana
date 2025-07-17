"""
Simple Phase 1 tests - Core functionality verification
"""

import pytest
from dana.frameworks.workflow.core import WorkflowEngine, WorkflowStep, ContextEngine, SafetyValidator


def test_basic_workflow():
    """Test basic workflow functionality."""
    engine = WorkflowEngine()
    
    def add_ten(x):
        return x + 10
    
    def double(x):
        return x * 2
    
    steps = [
        WorkflowStep(name="add", function=add_ten),
        WorkflowStep(name="double", function=double)
    ]
    
    result = engine.execute(steps, 5)
    assert result == 30  # (5 + 10) * 2


def test_single_step():
    """Test single step workflow."""
    engine = WorkflowEngine()
    
    def simple_func(x):
        return x + 1
    
    step = WorkflowStep(name="simple", function=simple_func)
    result = engine.execute([step], 42)
    assert result == 43


def test_context_engine_basic():
    """Test ContextEngine basic functionality."""
    context = ContextEngine()
    
    kp_id = context.add_knowledge("Test knowledge", "test_source")
    assert kp_id is not None
    
    kp = context.get_knowledge(kp_id)
    assert kp.content == "Test knowledge"
    assert kp.source == "test_source"


def test_safety_validator_basic():
    """Test SafetyValidator basic functionality."""
    validator = SafetyValidator()
    
    def safe_func(x):
        return x + 1
    
    step = WorkflowStep(name="safe", function=safe_func)
    result = validator.validate_step(step)
    assert result.is_safe is True


def test_workflow_with_error_handler():
    """Test workflow with error handling."""
    engine = WorkflowEngine()
    
    def failing_func(x):
        if x < 0:
            raise ValueError("Negative input")
        return x * 2
    
    def error_handler(error, input_data, context):
        return abs(input_data) * 3
    
    step = WorkflowStep(
        name="error_handled",
        function=failing_func,
        error_handler=error_handler
    )
    
    # Test valid input
    result1 = engine.execute([step], 5)
    assert result1 == 10
    
    # Test error input
    result2 = engine.execute([step], -5)
    assert result2 == 15


def test_decorator_pattern():
    """Test decorator pattern."""
    
    @WorkflowStep.from_function(name="decorated")
    def decorated_calc(x):
        return x ** 2
    
    engine = WorkflowEngine()
    result = engine.execute([decorated_calc], 4)
    assert result == 16


def test_empty_workflow_error():
    """Test empty workflow error handling."""
    engine = WorkflowEngine()
    
    with pytest.raises(RuntimeError, match="Empty workflow"):
        engine.execute([], 5)


def test_context_engine_search():
    """Test ContextEngine search functionality."""
    context = ContextEngine()
    
    context.add_knowledge("Python guide", "docs")
    context.add_knowledge("Java tutorial", "docs")
    
    results = context.search_knowledge("python")
    assert len(results) == 1
    assert results[0].content == "Python guide"


def test_safety_validator_workflow():
    """Test safety validator with workflow."""
    validator = SafetyValidator()
    
    def safe_func(x):
        return x + 1
    
    steps = [WorkflowStep(name="step1", function=safe_func)]
    result = validator.validate_workflow(steps)
    assert result.is_safe is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])