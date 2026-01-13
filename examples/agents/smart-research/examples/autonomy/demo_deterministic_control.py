#!/usr/bin/env python3
"""
Demonstration of deterministic workflow control across different query types.

This shows how SmartResearchAgent (with workflows) provides:
1. Consistent workflow execution (strategy-selection → research → synthesis)
2. Predictable strategy selection based on query type
3. Controlled execution flow with transparent reasoning
4. Structured output from workflow orchestration

Compare this to probabilistic where the LLM decides everything on its own.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agents.smart_research_agent import SmartResearchAgent


def demo_query(agent, query_type, query):
    """Run a query and highlight the deterministic workflow execution."""
    print("\n" + "=" * 80)
    print(f"QUERY TYPE: {query_type}")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print("-" * 80)

    result = agent.query(caller_message=query)

    print("\n📊 WORKFLOW EXECUTION:")
    print("-" * 80)

    # Show response
    if "response" in result:
        response = result["response"]
        print(f"\n✅ Response generated: {len(response)} characters")
        print(f"\nFirst 300 chars:\n{response[:300]}...")

    # Check timeline for workflow calls
    timeline = agent.get_timeline_summary()
    workflow_calls = [line for line in timeline.split("\n") if "Tool Call" in line or "Tool Response (Workflow)" in line]

    print(f"\n✅ Workflow calls made: {len([l for l in workflow_calls if 'Tool Call' in l])}")

    # Show what strategy was selected
    if "QUICK_FACT" in timeline:
        print("✅ Strategy selected: QUICK_FACT")
    elif "TECHNICAL_DEEP_DIVE" in timeline:
        print("✅ Strategy selected: TECHNICAL_DEEP_DIVE")
    elif "COMPARATIVE_ANALYSIS" in timeline:
        print("✅ Strategy selected: COMPARATIVE_ANALYSIS")
    elif "CURRENT_EVENTS" in timeline:
        print("✅ Strategy selected: CURRENT_EVENTS")

    print("\n💡 KEY INSIGHT:")
    print("   Workflows provide DETERMINISTIC control over execution flow")
    print("   Same query type → same strategy → same workflow sequence")


def main():
    """Demonstrate deterministic control across different query types."""
    print("=" * 80)
    print("DETERMINISTIC WORKFLOW CONTROL DEMONSTRATION")
    print("=" * 80)
    print()
    print("This demo shows how workflows provide consistent, controlled execution")
    print("across different query types. Each query triggers the workflow sequence:")
    print("  1. strategy-selection → analyzes query type")
    print("  2. research workflow → gathers information")
    print("  3. synthesis → combines results")
    print()
    print("The KEY DIFFERENCE from probabilistic:")
    print("  - Deterministic: Workflows CONTROL what happens")
    print("  - Probabilistic: LLM DECIDES what to do")
    print()

    # Create agent
    agent = SmartResearchAgent()

    # Demo different query types to show strategy selection
    queries = [
        ("QUICK FACT", "What is quantum computing?"),
        ("QUICK FACT - DIFFERENT TOPIC", "What is photosynthesis?"),
        ("COMPARISON", "Compare Python vs JavaScript"),
    ]

    print("\nRunning 3 queries to demonstrate consistency...")
    print()

    for query_type, query in queries:
        demo_query(agent, query_type, query)

        print("\n" + "─" * 80)
        user_input = input("\nPress Enter to continue (or 'q' to quit)...")
        if user_input.lower() == "q":
            break

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("  ✅ Workflows execute in predictable sequence")
    print("  ✅ Strategy selection is consistent for similar query types")
    print("  ✅ Execution flow is CONTROLLED, not probabilistic")
    print("  ✅ You can trace exactly what happened via workflows")
    print()
    print("Next: Try the comparison demo to see deterministic vs probabilistic")
    print("  python examples/autonomy/demo_comparison.py")
    print()


if __name__ == "__main__":
    main()
