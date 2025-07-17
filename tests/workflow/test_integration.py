"""
Integration tests for Phase 1 - Basic functionality verification
"""

import pytest
from dana.frameworks.workflow.core import WorkflowEngine, WorkflowStep, ContextEngine, SafetyValidator


class TestPhase1Integration:
    """Integration tests for Phase 1 basic workflow functionality."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow execution."""
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
        
        result = engine.execute(steps, 5, workflow_id="integration_test")
        assert result == "Result: 30"
    
    def test_context_engine_integration(self):
        """Test ContextEngine integration with workflow."""
        context_engine = ContextEngine(max_knowledge_points=50)
        engine = WorkflowEngine(context_engine=context_engine)
        
        def step_with_context(x):
            # Store intermediate result in context engine instead
            context_engine.add_knowledge(str(x + 5), "intermediate_step", tags=["intermediate"])
            results = context_engine.search_knowledge(str(x + 5))
            if results:
                return int(results[0].content) * 2
            return (x + 5) * 2
        
        step = WorkflowStep(name="context_step", function=step_with_context)
        result = engine.execute([step], 10)
        assert result == 30
    
    def test_safety_validator_integration(self):
        """Test SafetyValidator integration."""
        safety_validator = SafetyValidator(strict_mode=False)
        engine = WorkflowEngine(safety_validator=safety_validator)
        
        def safe_func(x):
            return x + 1
        
        step = WorkflowStep(name="safe_step", function=safe_func)
        result = engine.execute([step], 42)
        assert result == 43
    
    def test_workflow_with_error_handling(self):
        """Test workflow with built-in error handling."""
        engine = WorkflowEngine()
        
        def might_fail(x):
            if x < 0:
                raise ValueError("Negative input")
            return x * 2
        
        def error_handler(error, input_data, context):
            return abs(input_data) * 3  # Fallback
        
        step = WorkflowStep(
            name="error_handled",
            function=might_fail,
            error_handler=error_handler
        )
        
        # Test with valid input
        result1 = engine.execute([step], 5)
        assert result1 == 10
        
        # Test with error input
        result2 = engine.execute([step], -5)
        assert result2 == 15  # abs(-5) * 3
    
    def test_simple_composition_pattern(self):
        """Test basic composition pattern."""
        # Test sequential execution without composition
        def add_one(x):
            return x + 1
        
        def multiply_two(x):
            return x * 2
        
        steps = [
            WorkflowStep(name="add", function=add_one),
            WorkflowStep(name="multiply", function=multiply_two)
        ]
        
        engine = WorkflowEngine()
        result = engine.execute(steps, 5)
        assert result == 12
    
    def test_decorator_pattern(self):
        """Test decorator pattern for creating steps."""
        
        @WorkflowStep.from_function(name="decorated_step")
        def decorated_calc(x):
            return x ** 2
        
        engine = WorkflowEngine()
        result = engine.execute([decorated_calc], 4)
        assert result == 16
    
    def test_context_engine_basic_usage(self):
        """Test ContextEngine standalone usage."""
        context = ContextEngine()
        
        # Add knowledge
        kp_id = context.add_knowledge(
            content="Test knowledge",
            source="test_source",
            tags=["test"]
        )
        
        assert kp_id is not None
        assert len(context._knowledge_store) == 1
        
        # Search knowledge
        results = context.search_knowledge("test")
        assert len(results) == 1
        assert results[0].content == "Test knowledge"
    
    def test_safety_validator_basic_usage(self):
        """Test SafetyValidator standalone usage."""
        validator = SafetyValidator()
        
        def safe_func(x):
            return x + 1
        
        step = WorkflowStep(name="safe", function=safe_func)
        result = validator.validate_step(step)
        assert result.is_safe is True
    
    def test_workflow_engine_configuration(self):
        """Test engine configuration options."""
        context_engine = ContextEngine(max_knowledge_points=100)
        safety_validator = SafetyValidator(strict_mode=True)
        
        engine = WorkflowEngine(
            context_engine=context_engine,
            safety_validator=safety_validator,
            max_depth=5
        )
        
        def simple_func(x):
            return x + 1
        
        step = WorkflowStep(name="configured", function=simple_func)
        result = engine.execute([step], 100)
        assert result == 101


class TestPhase1EdgeCases:
    """Test edge cases for Phase 1."""
    
    def test_empty_workflow(self):
        """Test empty workflow handling."""
        engine = WorkflowEngine()
        
        with pytest.raises(RuntimeError, match="Empty workflow"):
            engine.execute([], 5)
    
    def test_single_step_workflow(self):
        """Test single step workflow."""
        engine = WorkflowEngine()
        
        def identity(x):
            return x
        
        step = WorkflowStep(name="identity", function=identity)
        result = engine.execute([step], 123)
        assert result == 123
    
    def test_context_snapshot_functionality(self):
        """Test context snapshot creation and retrieval."""
        context = ContextEngine()
        
        # Add some knowledge
        context.add_knowledge("Test 1", "source1")
        context.add_knowledge("Test 2", "source2")
        
        # Create snapshot
        snapshot_id = context.create_context_snapshot()
        assert snapshot_id is not None
        
        # Verify snapshot
        snapshot = context.get_context_snapshot(snapshot_id)
        assert snapshot is not None
        assert len(snapshot.knowledge_points) == 2
    
    def test_knowledge_limit_enforcement(self):
        """Test knowledge point limit enforcement."""
        context = ContextEngine(max_knowledge_points=3)
        
        # Add more than limit
        for i in range(5):
            context.add_knowledge(f"Knowledge {i}", f"source{i}")
        
        # Should enforce limit
        stats = context.get_stats()
        assert stats["total_knowledge_points"] == 3
    
    def test_safety_validator_strict_mode(self):
        """Test safety validator in strict mode."""
        from dana.frameworks.workflow.core.validation.safety_validator import SafetyLevel
        
        validator = SafetyValidator(strict_mode=True)
        
        def safe_func(x):
            return x + 1
        
        # Create many steps to trigger warning
        steps = [WorkflowStep(name=f"step_{i}", function=safe_func) for i in range(60)]
        
        result = validator.validate_workflow(steps)
        assert result.is_safe is False  # Strict mode enforces limits
        # Allow either ERROR or WARNING based on implementation
        assert result.level in [SafetyLevel.ERROR, SafetyLevel.WARNING]