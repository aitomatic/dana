"""
Example: Run Vietnam Coffee Research Agent with full autonomy (STAR loop).

This example demonstrates:
1. Autonomous agent using STAR loop (SEE-THINK-ACT-REFLECT)
2. LLM reasoning about which tools to use
3. Dynamic workflow and resource selection
4. Agent adaptation based on results
"""

import json
from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def main():
    """Run the agent with full autonomy using STAR loop."""

    print("=" * 80)
    print("Vietnam Coffee Research Agent - Autonomous Demo")
    print("=" * 80)
    print("\nThis demo showcases FULL AUTONOMY through STAR loop:")
    print("\n🤖 Agent will:")
    print("   • SEE: Understand your request")
    print("   • THINK: Reason about which tools to use")
    print("   • ACT: Execute workflows and resources autonomously")
    print("   • REFLECT: Learn and adapt from results")
    print("\n🔧 Available tools the agent can choose from:")
    print("   • Workflows: discover-companies, enrich-company, validate-mece, orchestrate-batches")
    print("   • Resources: web-search, company-structure, vietnamese-normalize, source-tracking")
    print("=" * 80)

    # Initialize agent
    agent = VietnamCoffeeResearchAgent()

    # Example 1: Simple request - agent will choose tools
    print("\n📍 Example 1: Simple Research Request")
    print("🤖 Request: 'Research coffee companies in Đắk Lắk'")
    print("\n🔄 Agent reasoning and tool selection...")

    result1 = agent.query(caller_message="Research coffee companies in Đắk Lắk province. Limit to 10 companies for demo.")

    print("\n📋 Agent Response:")
    print(f"   Status: {result1.get('status', 'unknown')}")
    print(f"   Content: {result1.get('content', 'No content')}")

    # Show tool calls made by agent
    tool_calls = result1.get("tool_calls", [])
    if tool_calls:
        print("\n🔧 Agent Tool Usage:")
        for i, call in enumerate(tool_calls, 1):
            target_type = call.get("target_type", "unknown")
            target_id = call.get("target_id", "unknown")
            function = call.get("function", "unknown")
            print(f"   {i}. {target_type}:{target_id}.{function}()")

    # Example 2: More complex request - agent will adapt strategy
    print("\n" + "=" * 80)
    print("📍 Example 2: Complex Research Request")
    print("🤖 Request: 'Find high-priority coffee exporters in multiple provinces'")
    print("\n🔄 Agent reasoning and adaptive tool selection...")

    result2 = agent.query(
        caller_message="Find high-priority coffee exporters in Đắk Lắk and Gia Lai provinces. Focus on companies with export certifications."
    )

    print("\n📋 Agent Response:")
    print(f"   Status: {result2.get('status', 'unknown')}")
    print(f"   Content: {result2.get('content', 'No content')}")

    # Show tool calls made by agent
    tool_calls2 = result2.get("tool_calls", [])
    if tool_calls2:
        print("\n🔧 Agent Tool Usage:")
        for i, call in enumerate(tool_calls2, 1):
            target_type = call.get("target_type", "unknown")
            target_id = call.get("target_id", "unknown")
            function = call.get("function", "unknown")
            print(f"   {i}. {target_type}:{target_id}.{function}()")

    # Example 3: Conversational interaction
    print("\n" + "=" * 80)
    print("📍 Example 3: Conversational Interaction")
    print("🤖 Starting conversation with agent...")
    print("\n🔄 Agent will handle the conversation autonomously...")

    # Start conversation
    agent.converse("I need help researching Vietnamese coffee companies. Can you help me find exporters in Đắk Lắk?")

    # Export results
    output_file = "vietnam_coffee_autonomous_demo.json"
    demo_results = {"example1": result1, "example2": result2, "note": "Example 3 uses converse() which is interactive"}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(demo_results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Demo results exported to: {output_file}")

    print("\n" + "=" * 80)
    print("✅ Autonomous Agent Demo Complete!")
    print("=" * 80)
    print("\n🎯 Key Differences from Hardcoded Approach:")
    print("   • Agent reasons about which tools to use")
    print("   • Can adapt strategy based on results")
    print("   • Can handle unexpected situations")
    print("   • Learns and improves over time")
    print("   • Full autonomy through STAR loop")


if __name__ == "__main__":
    main()
