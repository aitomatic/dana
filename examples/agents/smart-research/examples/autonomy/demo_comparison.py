#!/usr/bin/env python3
"""
Side-by-side comparison: Deterministic (workflows) vs Probabilistic (LLM-only)

Shows the key difference: workflows provide CONTROL and CONSISTENCY
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agents.smart_research_agent import SmartResearchAgent
from agents.probabilistic_research_agent import ProbabilisticResearchAgent


def analyze_response(agent, result):
    """Analyze response structure and workflow usage."""
    response = result.get("response", "")

    # Check timeline for workflow calls
    timeline = agent.get_timeline_summary()
    workflow_calls = len([line for line in timeline.split("\n") if "Tool Call" in line and "workflow" in line])

    return {
        "length": len(response),
        "workflow_calls": workflow_calls,
        "has_confidence": "confidence" in response.lower(),
        "has_sources": "source" in response.lower(),
        "used_workflows": workflow_calls > 0,
    }


def compare_query(query):
    """Run same query through both agents and compare."""
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    # Run deterministic
    print("\n🔧 DETERMINISTIC (with workflows):")
    print("-" * 80)
    det_agent = SmartResearchAgent()
    det_result = det_agent.query(caller_message=query)
    det_analysis = analyze_response(det_agent, det_result)

    print(f"\nResponse length: {det_analysis['length']} chars")
    print(f"✅ Workflow calls: {det_analysis['workflow_calls']}")
    print(f"✅ Used workflows: {'Yes' if det_analysis['used_workflows'] else 'No'}")
    print(f"✅ Confidence scores: {'Yes' if det_analysis['has_confidence'] else 'No'}")
    print(f"✅ Source tracking: {'Yes' if det_analysis['has_sources'] else 'No'}")

    print(f"\nResponse preview:\n{det_result.get('response', '')[:200]}...")

    # Run probabilistic
    print("\n\n🎲 PROBABILISTIC (LLM-only, no workflows):")
    print("-" * 80)
    prob_agent = ProbabilisticResearchAgent()
    prob_result = prob_agent.query(caller_message=query)
    prob_analysis = analyze_response(prob_agent, prob_result)

    print(f"\nResponse length: {prob_analysis['length']} chars")
    print(f"✅ Workflow calls: {prob_analysis['workflow_calls']}")
    print(f"✅ Used workflows: {'Yes' if prob_analysis['used_workflows'] else 'No'}")
    print(f"✅ Confidence scores: {'Yes' if prob_analysis['has_confidence'] else 'No'}")
    print(f"✅ Source tracking: {'Yes' if prob_analysis['has_sources'] else 'No'}")

    print(f"\nResponse preview:\n{prob_result.get('response', '')[:200]}...")

    # Comparison
    print("\n\n📊 KEY DIFFERENCE:")
    print("-" * 80)

    if det_analysis["used_workflows"] and not prob_analysis["used_workflows"]:
        print("✅ DETERMINISTIC: Executed workflows as designed")
        print("❌ PROBABILISTIC: Did NOT use workflows (LLM chose to answer directly)")
        print("\n💡 This shows workflow orchestration gives you CONTROL")
        print("   - Deterministic: workflows execute regardless of LLM reasoning")
        print("   - Probabilistic: LLM decides whether to use tools")
    elif det_analysis["used_workflows"] and prob_analysis["used_workflows"]:
        print("⚠️  Both used workflows this time")
        print("   (But probabilistic is inconsistent - try running multiple times)")
    else:
        print("⚠️  Unexpected pattern - check implementation")


def main():
    """Run comparison demo."""
    print("=" * 80)
    print("DETERMINISTIC vs PROBABILISTIC COMPARISON")
    print("=" * 80)
    print()
    print("This demo runs the SAME query through both agents to highlight the")
    print("fundamental difference in autonomy patterns:")
    print()
    print("🔧 DETERMINISTIC (SmartResearchAgent with workflows):")
    print("  • Workflows CONTROL execution flow")
    print("  • Guaranteed to use workflow sequence")
    print("  • Consistent behavior across runs")
    print("  • You orchestrate WHEN and HOW tools are used")
    print()
    print("🎲 PROBABILISTIC (ProbabilisticResearchAgent, LLM-only):")
    print("  • LLM DECIDES what to do")
    print("  • MAY or MAY NOT use available tools")
    print("  • Behavior varies each run")
    print("  • LLM autonomously chooses actions")
    print()
    print("The key insight: With workflows, YOU control the execution.")
    print("Without workflows, the LLM decides - and it might choose differently!")
    print()

    queries = [
        "What is quantum computing?",
    ]

    for query in queries:
        compare_query(query)
        print("\n" + "─" * 80)
        user_input = input("\nPress Enter for next query (or 'q' to quit)...")
        if user_input.lower() == "q":
            break

    print("\n" + "=" * 80)
    print("EXPERIMENT: Run the probabilistic agent 3 times with same query")
    print("You'll likely see different behavior each time!")
    print("  python examples/autonomy/run_probabilistic.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
