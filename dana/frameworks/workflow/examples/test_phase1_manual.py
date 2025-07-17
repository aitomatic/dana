#!/usr/bin/env python3
"""
Manual test for Phase 1 - Basic workflow functionality
"""

import sys
import os

# Add the project root to path
sys.path.insert(0, '/Users/ctn/src/aitomatic/dana')

from dana.frameworks.workflow.core import WorkflowEngine, WorkflowStep, ContextEngine, SafetyValidator


def test_phase1_basic():
    """Test basic Phase 1 functionality."""
    print("🔍 Testing Phase 1 Basic Workflow Components")
    print("=" * 50)
    
    # Test 1: Basic Workflow Engine
    print("1. Testing WorkflowEngine...")
    engine = WorkflowEngine()
    print("   ✅ WorkflowEngine initialized")
    
    # Test 2: Basic WorkflowStep
    print("2. Testing WorkflowStep...")
    
    def add_ten(x):
        return x + 10
    
    def double(x):
        return x * 2
    
    step1 = WorkflowStep(name="add_ten", function=add_ten)
    step2 = WorkflowStep(name="double", function=double)
    print("   ✅ WorkflowStep created successfully")
    
    # Test 3: Simple workflow execution
    print("3. Testing basic workflow execution...")
    steps = [step1, step2]
    try:
        result = engine.execute(steps, 5, workflow_id="test_workflow")
        expected = 30  # (5 + 10) * 2
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"   ✅ Workflow executed: 5 → {result}")
    except Exception as e:
        print(f"   ❌ Workflow failed: {e}")
        return False
    
    # Test 4: ContextEngine
    print("4. Testing ContextEngine...")
    context = ContextEngine(max_knowledge_points=100)
    
    # Add knowledge
    kp_id = context.add_knowledge(
        content="Test knowledge point",
        source="test_source",
        tags=["test", "demo"]
    )
    
    assert kp_id is not None, "Knowledge point ID should not be None"
    
    # Retrieve knowledge
    kp = context.get_knowledge(kp_id)
    assert kp is not None, "Knowledge point should be retrievable"
    assert kp.content == "Test knowledge point"
    print("   ✅ ContextEngine working correctly")
    
    # Test 5: SafetyValidator
    print("5. Testing SafetyValidator...")
    validator = SafetyValidator()
    
    # Validate a safe step
    safe_step = WorkflowStep(name="safe", function=add_ten)
    validation_result = validator.validate_step(safe_step)
    assert validation_result.is_safe, "Safe step should pass validation"
    print("   ✅ SafetyValidator working correctly")
    
    # Test 6: Error handling
    print("6. Testing error handling...")
    
    def failing_step(x):
        if x < 0:
            raise ValueError("Negative input")
        return x * 2
    
    def error_handler(error, input_data, context):
        return abs(input_data) * 3
    
    error_step = WorkflowStep(
        name="error_handled",
        function=failing_step,
        error_handler=error_handler
    )
    
    # Test error handling
    result = engine.execute([error_step], -5)
    assert result == 15  # abs(-5) * 3
    print("   ✅ Error handling working correctly")
    
    # Test 7: ContextEngine search
    print("7. Testing ContextEngine search...")
    context.add_knowledge("Python programming", "docs")
    context.add_knowledge("Java programming", "docs")
    
    results = context.search_knowledge("python")
    assert len(results) == 1
    assert results[0].content == "Python programming"
    print("   ✅ ContextEngine search working correctly")
    
    # Test 8: Statistics
    print("8. Testing statistics...")
    stats = context.get_stats()
    assert stats["total_knowledge_points"] == 3
    assert stats["unique_tags"] >= 2
    print("   ✅ Statistics working correctly")
    
    print("\n🎉 All Phase 1 tests passed!")
    print("Phase 1 Foundation is complete and working correctly.")
    return True


def test_phase1_examples():
    """Test the Phase 1 examples."""
    print("\n🔍 Testing Phase 1 Examples")
    print("=" * 40)
    
    engine = WorkflowEngine()
    
    # Example 1: Data processing pipeline
    def extract_data(input_data):
        return {"raw": input_data, "length": len(str(input_data))}
    
    def transform_data(data):
        return {
            "processed": data["raw"],
            "processed_length": data["length"] * 2
        }
    
    def format_output(data):
        return f"Processed: {data['processed']} (length: {data['processed_length']})"
    
    steps = [
        WorkflowStep(name="extract", function=extract_data),
        WorkflowStep(name="transform", function=transform_data),
        WorkflowStep(name="format", function=format_output)
    ]
    
    result = engine.execute(steps, "HelloWorld")
    print(f"Data pipeline result: {result}")
    assert "HelloWorld" in result
    assert "20" in result  # len("HelloWorld") * 2 = 20
    
    print("✅ Data pipeline example working correctly")
    
    # Example 2: Simple math workflow
    def increment(x):
        return x + 1
    
    def square(x):
        return x * x
    
    math_steps = [
        WorkflowStep(name="increment", function=increment),
        WorkflowStep(name="square", function=square)
    ]
    
    result = engine.execute(math_steps, 3)
    print(f"Math workflow result: 3 → {result}")
    assert result == 16  # (3 + 1) ** 2
    
    print("✅ Math workflow example working correctly")
    
    return True


if __name__ == "__main__":
    print("🚀 Phase 1 Manual Testing")
    print("=" * 50)
    
    try:
        success1 = test_phase1_basic()
        success2 = test_phase1_examples()
        
        if success1 and success2:
            print("\n🎉 ALL PHASE 1 TESTS PASSED!")
            print("\nPhase 1 Summary:")
            print("- ✅ WorkflowEngine: Basic orchestration working")
            print("- ✅ WorkflowStep: Step abstraction complete")
            print("- ✅ ContextEngine: Knowledge curation functional")
            print("- ✅ SafetyValidator: Basic validation operational")
            print("- ✅ Error handling: Graceful error recovery")
            print("- ✅ Integration: All components working together")
            
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)