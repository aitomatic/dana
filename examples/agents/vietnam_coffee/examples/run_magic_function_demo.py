"""
Example: Vietnam Coffee Research Agent with Magic Function.

This example demonstrates the new magic function that converts method calls
to natural language and calls converse() automatically.

Examples:
- agent.research_coffee_companies() -> converse("research coffee companies")
- agent.find_exporters_in_dak_lak() -> converse("find exporters in dak lak")
- agent.search_companies_in_province("Gia Lai") -> converse("search companies in province Gia Lai")
"""

from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def main():
    """Demonstrate the magic function."""

    print("=" * 80)
    print("Vietnam Coffee Research Agent - Magic Function Demo")
    print("=" * 80)
    print("\nThis demo showcases the new MAGIC FUNCTION:")
    print("\n🎯 Natural Method Calls:")
    print("   • agent.research_coffee_companies()")
    print("   • agent.find_exporters_in_dak_lak()")
    print("   • agent.search_companies_in_province('Gia Lai')")
    print("   • agent.hi_how_are_you()")
    print("\n🔧 How it works:")
    print("   • Underscores become spaces: research_coffee_companies -> 'research coffee companies'")
    print("   • Arguments are added: find_exporters_in('Đắk Lắk') -> 'find exporters in Đắk Lắk'")
    print("   • Keyword args are added: search(province='Gia Lai') -> 'search province=Gia Lai'")
    print("   • All converted to: converse('natural language message')")
    print("=" * 80)

    # Initialize agent
    agent = VietnamCoffeeResearchAgent()

    print("\n📍 Example 1: Simple Magic Function")
    print("🤖 Calling: agent.research_coffee_companies()")
    print("🔄 Converts to: converse('research coffee companies')")
    print("\n💡 This will start an interactive conversation...")
    print("💡 Type 'quit' to exit the conversation")
    print("\n" + "=" * 50)

    # This will trigger the magic function and start a conversation
    agent.research_coffee_companies()

    print("\n" + "=" * 80)
    print("✅ Magic Function Demo Complete!")
    print("=" * 80)
    print("\n🎯 Key Benefits:")
    print("   • Intuitive method names")
    print("   • Natural language conversion")
    print("   • Automatic conversation start")
    print("   • No need to remember exact method signatures")
    print("\n💡 Try these examples:")
    print("   • agent.hi_how_are_you()")
    print("   • agent.find_exporters_in_dak_lak()")
    print("   • agent.search_companies_in_province('Gia Lai')")
    print("   • agent.research_coffee_companies()")


if __name__ == "__main__":
    main()
