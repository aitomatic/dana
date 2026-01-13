"""
Example: Run Vietnam Coffee Research Agent with interactive approval gates.

This example demonstrates:
1. Human-in-loop approval at 3 gates
2. Gate 1: Approve discovered companies before enrichment
3. Gate 2: Review enrichment progress every 5 batches
4. Gate 3: Final approval before delivery
5. Ability to abort at any gate
"""

import json
from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def main():
    """Run the agent with interactive approval gates."""

    print("=" * 80)
    print("Vietnam Coffee Research Agent - Interactive Gates Demo")
    print("=" * 80)
    print("\nThis demo showcases RICH INTERACTIVE GATES with multiple commands:")
    print("\n📍 Gate 1 (Discovery):")
    print("   • proceed, show more, limit <N>, filter <keyword>, add province, redo, abort")
    print("\n📍 Gate 2 (Enrichment Progress):")
    print("   • continue, show batch, show stats, show low quality, pause, abort")
    print("\n📍 Gate 3 (Final Approval):")
    print("   • approve, export csv, show low quality, re-enrich low quality, redo, abort")
    print("\n💡 TIP: Try commands like 'limit 15', 'show more', 'show stats' at each gate!")
    print("=" * 80)

    # Initialize agent
    agent = VietnamCoffeeResearchAgent()

    # Run research with autonomous agent (STAR loop)
    print("\n📍 Starting autonomous research in Đắk Lắk province...")
    print("🤖 Agent will use STAR loop to reason and choose tools")
    print("🎯 Max companies: 20 (for demo)")
    print("\n🔄 Agent reasoning and tool selection...")

    # Use autonomous entry point - agent will reason about which tools to use
    result = agent.query(caller_message="Research coffee companies in Đắk Lắk province. Limit to 20 companies for demo purposes.")

    # Handle autonomous agent result
    print("\n" + "=" * 80)
    print("🤖 AUTONOMOUS AGENT RESULT")
    print("=" * 80)

    # The autonomous agent returns different structure
    if result.get("error"):
        print(f"\n❌ Agent Error: {result.get('error')}")
        return

    # Show agent's reasoning and actions
    print("\n📋 Agent Response:")
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   Content: {result.get('content', 'No content')}")

    # Show tool calls made by agent
    tool_calls = result.get("tool_calls", [])
    if tool_calls:
        print("\n🔧 Agent Tool Usage:")
        for i, call in enumerate(tool_calls, 1):
            target_type = call.get("target_type", "unknown")
            target_id = call.get("target_id", "unknown")
            function = call.get("function", "unknown")
            print(f"   {i}. {target_type}:{target_id}.{function}()")

    # Export results
    output_file = "vietnam_coffee_autonomous_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results exported to: {output_file}")

    print("\n" + "=" * 80)
    print("✅ Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
