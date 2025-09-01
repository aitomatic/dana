#!/usr/bin/env python3
"""
Simple test script for basic components.
"""

import os
import sys

# Add the dana directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "dana"))


def test_context_engineering():
    """Test the context engineering system."""
    print("Testing Context Engineering...")

    try:
        from dana.builtin_types.agent.context import ActionHistory, ComputableContext, ProblemContext

        # Test ProblemContext
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        print(f"✓ ProblemContext created: {context.problem_statement}")

        # Test sub-context creation
        sub_context = context.create_sub_context("Sub problem", "Sub objective")
        print(f"✓ Sub-context created: depth={sub_context.depth}")

        # Test ActionHistory
        history = ActionHistory()
        print(f"✓ ActionHistory created: {len(history.actions)} actions")

        # Test ComputableContext
        computable = ComputableContext()
        indicators = computable.get_complexity_indicators(context, history)
        print(f"✓ ComputableContext created: {indicators}")

        print("✓ Context Engineering tests passed!")
        return True

    except Exception as e:
        print(f"✗ Context Engineering test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_workflow_system():
    """Test the workflow system."""
    print("\nTesting Workflow System...")

    try:
        from dana.builtin_types.workflow.workflow_system import WorkflowInstance, WorkflowType

        # Test WorkflowType creation
        workflow_type = WorkflowType(
            name="TestWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Test workflow",
        )
        print(f"✓ WorkflowType created: {workflow_type.name}")

        # Test WorkflowInstance creation
        workflow = WorkflowInstance(struct_type=workflow_type, values={"test": "value"}, parent_workflow=None)
        print(f"✓ WorkflowInstance created: {workflow._problem_statement}")

        print("✓ Workflow System tests passed!")
        return True

    except Exception as e:
        print(f"✗ Workflow System test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_strategy_system():
    """Test the strategy system."""
    print("\nTesting Strategy System...")

    try:
        from dana.builtin_types.agent.context import ProblemContext
        from dana.builtin_types.agent.strategy.recursive.recursive_strategy import RecursiveStrategy

        # Test RecursiveStrategy creation
        strategy = RecursiveStrategy(max_depth=5)
        print(f"✓ RecursiveStrategy created: max_depth={strategy.max_depth}")

        # Test can_handle
        context = ProblemContext(problem_statement="Test problem", objective="Test objective", original_problem="Test problem", depth=0)
        can_handle = strategy.can_handle("Test problem", context)
        print(f"✓ can_handle test: {can_handle}")

        print("✓ Strategy System tests passed!")
        return True

    except Exception as e:
        print(f"✗ Strategy System test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("Running Simple Implementation Tests...")
    print("=" * 50)

    tests = [test_context_engineering, test_workflow_system, test_strategy_system]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Basic implementation is working.")
        return 0
    else:
        print("❌ Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
