"""
Example: Vietnam Coffee Research Agent with Interactive Conversation.

This example demonstrates using the agent's converse() method for interactive
conversation with the agent. The agent will use its STAR loop to reason about
user requests and autonomously choose which tools to use.

Usage:
    python run_converse_demo.py

The agent will start an interactive conversation where you can:
- Ask questions about Vietnamese coffee companies
- Request research on specific provinces
- Ask for data analysis
- Have natural conversations with the agent
"""

from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vietnam_coffee_research import VietnamCoffeeResearchAgent


def main():
    """Start an interactive conversation with the agent."""

    print("=" * 80)
    print("Vietnam Coffee Research Agent - Interactive Conversation Demo")
    print("=" * 80)
    print("\nThis demo showcases INTERACTIVE CONVERSATION with the agent:")
    print("\n🤖 Agent Capabilities:")
    print("   • Research coffee companies in Vietnamese provinces")
    print("   • Find exporters and their details")
    print("   • Analyze company data and trends")
    print("   • Answer questions about the Vietnamese coffee industry")
    print("   • Use autonomous reasoning to choose appropriate tools")
    print("\n💬 Conversation Features:")
    print("   • Natural language interaction")
    print("   • STAR loop reasoning (SEE-THINK-ACT-REFLECT)")
    print("   • Autonomous tool selection")
    print("   • Context-aware responses")
    print("\n🎯 Try asking:")
    print("   • 'Research coffee companies in Đắk Lắk'")
    print("   • 'Find exporters in Gia Lai province'")
    print("   • 'What are the main coffee regions in Vietnam?'")
    print("   • 'Help me understand the Vietnamese coffee industry'")
    print("=" * 80)

    # Initialize agent
    agent = VietnamCoffeeResearchAgent()
    print(f"\n✅ Agent initialized: {agent.agent_type}")

    # Start interactive conversation
    print("\n🚀 Starting interactive conversation...")
    print("💡 Type 'quit', 'exit', or 'bye' to end the conversation")
    print("💡 Type 'help' for available commands")
    print("\n" + "=" * 50)

    # This starts the interactive conversation loop
    agent.converse(initial_message="Hello! I'm your Vietnamese coffee research specialist. How can I help you today?")

    print("\n" + "=" * 80)
    print("✅ Conversation ended. Thanks for using the Vietnam Coffee Research Agent!")
    print("=" * 80)


if __name__ == "__main__":
    main()
