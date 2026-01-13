"""
Interactive Semiconductor Yield Analysis Demo.

This demo provides a conversational interface for analyzing wafer test failures.
The agent uses STAR loop reasoning to autonomously choose workflows and provide
intelligent yield improvement guidance.

Usage:
    python run_interactive_demo.py

You can ask the agent questions like:
- "Analyze failures for wafer W12345"
- "What are the top failure bins?"
- "Is BIN_1 systematic or random?"
- "What's the ROI for fixing BIN_1?"
- "Help me improve yield"
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.yield_analysis_agent import YieldAnalysisAgent


def main():
    """Start interactive conversation with yield analysis agent."""

    print("=" * 80)
    print("Semiconductor Yield Analysis Agent - Interactive Demo")
    print("=" * 80)
    print("\n🎯 ULTIMATE Deterministic Autonomy Pattern")
    print("\nThis agent demonstrates:")
    print("\n🤖 Agent Capabilities:")
    print("   • Pareto analysis - identify top failure bins (80/20 rule)")
    print("   • Pattern classification - systematic vs random failures")
    print("   • Correlation analysis - link failures to process changes")
    print("   • ROI prioritization - rank fixes by revenue impact")
    print("   • Statistical analysis - spatial autocorrelation, hot spots")
    print("   • Historical matching - compare with known defect patterns")
    print("\n💬 Conversation Features:")
    print("   • Natural language interaction")
    print("   • STAR loop reasoning (SEE-THINK-ACT-REFLECT)")
    print("   • Autonomous workflow selection")
    print("   • Multi-source evidence synthesis")
    print("\n🛠️ ULTIMATE Pattern:")
    print("   • Agent decides which workflows to run")
    print("   • Workflows execute ALL steps (can't skip)")
    print("   • WorkflowStepAgent uses Resources + Workflows for intelligence")
    print("   • High-confidence, evidence-based decisions")
    print("\n🎯 Try asking:")
    print("   • 'Analyze failures for wafer W12345'")
    print("   • 'What are the top failure bins?'")
    print("   • 'Is BIN_1 systematic or random? Give me evidence.'")
    print("   • 'What's the ROI for fixing BIN_1 vs BIN_2?'")
    print("   • 'Help me prioritize which failure to fix first'")
    print("   • 'Explain the difference between systematic and random defects'")
    print("=" * 80)

    # Initialize agent
    print("\n🔧 Initializing YieldAnalysisAgent...")
    agent = YieldAnalysisAgent(agent_id="yield-analyst-001", llm_provider="anthropic", model="claude-3-5-sonnet-20241022")

    print(f"✅ Agent initialized: {agent.agent_type} (ID: {agent.object_id})")
    print(f"   📊 Resources: {len(agent.available_resources)}")
    print(f"   🔄 Workflows: {len(agent.available_workflows)}")

    # Start interactive conversation
    print("\n🚀 Starting interactive conversation...")
    print("💡 Type 'quit', 'exit', or 'bye' to end the conversation")
    print("💡 Type 'help' for available commands")
    print("\n" + "=" * 80)

    # Start conversation with helpful initial message
    initial_message = """Hello! I'm your semiconductor yield analysis specialist.

I can help you analyze wafer test failures and improve yield through:
• Pareto analysis to identify critical failure modes
• Statistical analysis to classify systematic vs random defects
• Root cause correlation with process changes
• ROI-based prioritization of improvement actions

I have access to:
• Test data for wafer W12345 (68.5% yield, 315 failures)
• Spatial defect maps and statistical analysis tools
• Historical defect pattern database
• Process correlation data

How can I help you improve your yield today?"""

    # This starts the interactive conversation loop
    agent.converse(initial_message=initial_message)

    print("\n" + "=" * 80)
    print("✅ Conversation ended. Thanks for using the Yield Analysis Agent!")
    print("=" * 80)


if __name__ == "__main__":
    main()
