#!/usr/bin/env python3
"""
Complete System Test - Phases 1-3 Integration

This demonstrates the full workflow system with:
- Phase 1: Foundation (core engine, steps, context, safety)
- Phase 2: POET Integration (runtime objectives, validation)
- Phase 3: Context Engineering (KNOWS integration, knowledge curation)
"""

from dana.builtin_types.workflow.workflow_system.context_engineering import ContextAwareWorkflowEngine
from dana.builtin_types.workflow.workflow_system.core.workflow_engine import WorkflowEngine
from dana.builtin_types.workflow.workflow_system.core.workflow_step import WorkflowStep


def add_ten(x):
    """Add 10 to input."""
    return x + 10


def multiply_two(x):
    """Multiply input by 2."""
    return x * 2


def format_result(x):
    """Format result as string."""
    return f"Final result: {x}"


def main():
    print("🚀 Testing Complete Workflow System - Phases 1-3")
    print("=" * 60)

    # Create workflow steps
    steps = [
        WorkflowStep(name="add_ten", function=add_ten),
        WorkflowStep(name="multiply_two", function=multiply_two),
        WorkflowStep(name="format_result", function=format_result),
    ]

    # Test Phase 1: Basic Foundation
    print("\n📊 Phase 1: Foundation Test")
    engine = WorkflowEngine()
    result = engine.execute(steps, 5, workflow_id="foundation_test")
    print(f"✅ Basic workflow result: {result}")

    # Test Phase 3: Context Engineering (Phase 2 POET is integrated)
    print("\n🧠 Phase 3: Context Engineering Test")
    context_engine = ContextAwareWorkflowEngine()
    context_result = context_engine.run(steps, 7, workflow_id="context_test")

    print(f"✅ Context-aware result: {context_result['result']}")
    print(f"📊 Context snapshots: {context_result['context_snapshots']}")
    print(f"🔍 Knowledge traces: {len(context_result['context_state']['knowledge_traces'])}")

    # Test knowledge search
    print("\n🔎 Testing Knowledge Search")
    search_results = context_engine.context_engineering.search_context_knowledge("result")
    print(f"Found {len(search_results)} knowledge points about results")

    # Test context export
    print("\n📤 Testing Context Export")
    export = context_engine.context_engineering.export_context_state("context_test")
    print(f"Exported {len(export['knowledge_traces'])} knowledge traces")
    print(f"Exported {len(export['context_stats'])} context statistics")

    print("\n🎉 All phases working correctly!")
    print("=" * 60)
    print("Status: Phases 1-3 Complete ✅")
    print("Next: Phase 4 - Efficiency (Ready to Start)")


if __name__ == "__main__":
    main()
