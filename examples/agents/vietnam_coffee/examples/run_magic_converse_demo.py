"""
Example: Vietnam Coffee Research Agent with Magic Function + Converse.

This example demonstrates the magic function that converts method calls to
natural language and then starts an interactive conversation.

Examples:
- agent.research_coffee_companies() -> converse("research coffee companies")
- agent.find_exporters_in_dak_lak() -> converse("find exporters in dak lak")
- agent.hi_how_are_you() -> converse("hi how are you")

The magic function makes the agent incredibly intuitive to use!
"""

from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def main():
    """Demonstrate the magic function with converse()."""

    print("=" * 80)
    print("Vietnam Coffee Research Agent - Magic Function + Converse Demo")
    print("=" * 80)
    print("\nThis demo showcases the MAGIC FUNCTION with INTERACTIVE CONVERSATION:")
    print("\n🎯 Magic Function Examples:")
    print("   • agent.research_coffee_companies()")
    print("   • agent.find_exporters_in_dak_lak()")
    print("   • agent.search_companies_in_province('Gia Lai')")
    print("   • agent.hi_how_are_you()")
    print("\n🔧 How it works:")
    print("   • Method name → Natural language")
    print("   • Arguments → Additional context")
    print("   • Calls converse() → Interactive conversation")
    print("\n💡 This makes the agent incredibly intuitive to use!")
    print("=" * 80)

    # Initialize agent
    agent = VietnamCoffeeResearchAgent()
    print(f"\n✅ Agent initialized: {agent.agent_type}")

    print("\n📍 Example 1: Simple Magic Function")
    print("🤖 Calling: agent.hi_how_are_you()")
    print("🔄 Converts to: converse('hi how are you')")
    print("\n💡 This will start an interactive conversation...")
    print("💡 Type 'quit' to exit the conversation")
    print("\n" + "=" * 50)

    # This will trigger the magic function and start a conversation
    agent.hi_how_are_you()

    print("\n" + "=" * 80)
    print("✅ Magic Function + Converse Demo Complete!")
    print("=" * 80)
    print("\n🎯 Key Benefits:")
    print("   • Intuitive method names")
    print("   • Natural language conversion")
    print("   • Interactive conversation")
    print("   • Autonomous agent reasoning")
    print("\n💡 Try these examples:")
    print("   • agent.research_coffee_companies()")
    print("   • agent.find_exporters_in_dak_lak()")
    print("   • agent.search_companies_in_province('Gia Lai')")
    print("   • agent.hi_how_are_you()")


if __name__ == "__main__":
    main()
