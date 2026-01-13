#!/usr/bin/env python3
"""
STAR Agent Example - Using the New STARAgent Implementation

This example demonstrates how to create and use a STARAgent with the Adana framework
using the STAR (See-Think-Act-Reflect) pattern for decision making.

Usage:
    python star_agent_example.py                    # Run with simulated conversation
    python star_agent_example.py --live             # Run with actual LLM calls
    python star_agent_example.py --live --provider openai  # Use specific provider
"""

import argparse

from dana.core.agent.star_agent import STARAgent


class DemoSTARAgent(STARAgent):
    """Demo STARAgent for demonstrating the STAR pattern capabilities.

    <PUBLIC_DESCRIPTION>
    Demo agent that showcases the STAR (See-Think-Act-Reflect) decision-making framework.
    This agent is designed for demonstration and educational purposes, showing how to
    implement intelligent assistance through structured observation, reasoning, action,
    and reflection. Perfect for learning how to build STAR-based agents.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are a demonstration agent built to showcase the STAR pattern. Your primary role
    is to help users understand how the See-Think-Act-Reflect framework works in practice.

    Be educational and explanatory in your responses. When users interact with you,
    explain your thought process and decision-making steps clearly. Show how you observe
    the situation (SEE), analyze and plan (THINK), take action (ACT), and learn from
    the results (REFLECT).

    Be friendly, helpful, and pedagogical. Your goal is to demonstrate best practices
    for STAR-based decision making while being genuinely useful to the user.
    </PRIVATE_IDENTITY>
    """

    def __init__(self, **kwargs):
        super().__init__(agent_type="demo_star", **kwargs)


def main(live_mode=False, provider=None, model=None):
    """Main example function."""
    print("🤖 Adana STARAgent Example - STAR Pattern")
    print("=" * 50)

    # Create a STARAgent
    print("\n1. Creating STARAgent...")

    agent = DemoSTARAgent(
        llm_provider=provider,
        model=model,
    )

    print(f"   Agent created: {agent}")
    print(f"   Agent ID: {agent.object_id}")
    print(f"   Agent Type: {agent.agent_type}")

    # Show available resources and agents
    print("\n2. Available Resources and Agents...")
    print(f"   Resources: {agent.available_resources}")
    print(f"   Agents: {agent.available_agents}")

    # State management
    print("\n3. State Management...")
    state = agent.get_state()
    print(f"   Agent State: {state}")

    # Handle conversation based on mode
    if live_mode:
        print("\n4. Live LLM Conversation with STAR Pattern...")
        print("   🚀 Running with actual LLM calls!")
        print(f"   Provider: {provider}, Model: {model}")

        try:
            # Test basic query using STAR pattern
            print("\n   Testing STAR pattern query...")
            print("   📝 User: Hello! Can you help me understand the OODA loop?")

            # Use the query method which implements the full STAR pattern
            traces = agent.query(message="Hello! Can you help me understand the OODA loop?")
            response = traces.get("response", "No response generated")
            print(f"   🤖 Agent: {response}")

            # Test follow-up question
            print("\n   Testing follow-up with STAR pattern...")
            print("   📝 User: What are the four phases of OODA?")

            traces2 = agent.query(message="What are the four phases of OODA?")
            response2 = traces2.get("response", "No response generated")
            print(f"   🤖 Agent: {response2}")

            # Test tool calling (if any resources are available)
            print("\n   Testing tool calling capabilities...")
            try:
                # This would trigger the STAR pattern with tool calls if resources were available
                traces3 = agent.query(message="Can you show me what resources you have access to?")
                response3 = traces3.get("response", "No response generated")
                print(f"   🤖 Agent: {response3}")
            except Exception as e:
                print(f"   Tool call test: {str(e)[:100]}...")

        except Exception as e:
            print(f"   ❌ Error during live chat: {e}")
            print("   This is expected if API keys are not configured.")
            print("   Falling back to simulated conversation...")
            live_mode = False

    if not live_mode:
        print("\n4. Simulating STAR Pattern Conversation...")
        print("   📝 Using simulated conversation (no API calls)")

        # Add some timeline entries manually for demo
        from datetime import datetime

        from adana.core.agent.timeline import TimelineEntry

        agent._timeline.add_entry(
            TimelineEntry(timestamp=datetime.now(), entry_type="user_input", content="Hello! Can you help me understand the OODA loop?")
        )
        agent._timeline.add_entry(
            TimelineEntry(
                timestamp=datetime.now(),
                entry_type="my_response",
                content="Hello! The OODA loop has four phases: Observe (analyze input), Orient (consider context), Decide (choose action), and Act (execute decision).",
            )
        )

    print("\n   Timeline:")
    print(agent.get_timeline_summary())

    # Show agent state
    print("\n5. STARAgent State Summary...")
    state = agent.get_state()
    print(f"   Agent Type: {state['agent_type']}")
    print(f"   Created: {state['created_at']}")
    print(f"   Last Updated: {state['last_updated']}")
    print(f"   Timeline Entries: {state['timeline_entries']}")
    print(f"   Session Metadata: {len(state['session_metadata'])}")

    # Demonstrate STAR pattern components
    print("\n6. STAR Pattern Components...")
    print("   ✓ SEE: Observe input and gather context")
    print("   ✓ THINK: Use LLM to reason about context and decide actions")
    print("   ✓ ACT: Execute tool calls and return results")
    print("   ✓ REFLECT: Reflect on actions and determine next steps")

    # Show system prompt structure
    print("\n7. System Prompt Structure...")
    print("   The STARAgent uses a direct system prompt with:")
    print("   - Agent type identification")
    print("   - Available resources listing")
    print("   - Available agents listing")
    print("   - XML tool call format instructions")

    # Test the system prompt generation
    print("\n8. System Prompt Demo...")
    try:
        # Access the system prompt generation method
        timeline = agent._timeline
        messages = agent._build_llm_request(timeline)

        system_message = None
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
                break

        if system_message:
            print(f"   System prompt length: {len(system_message)} characters")
            print(f"   Contains agent type: {agent.agent_type in system_message}")
            print(f"   Contains XML format: {'<tool_call>' in system_message}")
            print(f"   Preview: {system_message[:200]}...")
        else:
            print("   No system message found in generated messages")
    except Exception as e:
        print(f"   System prompt demo: {str(e)[:100]}...")

    print("\n✅ STARAgent Example completed successfully!")

    if not live_mode:
        print("\n💡 To test with actual LLM calls, run:")
        print("   python star_agent_example.py --live")
        print("   python star_agent_example.py --live --provider openai")
    else:
        print("\n🎉 Live LLM conversation with STAR pattern completed!")

    print("\n🔧 STARAgent Features Demonstrated:")
    print("   ✓ STAR (See-Think-Act-Reflect) decision pattern")
    print("   ✓ Direct system prompt generation")
    print("   ✓ XML tool call format")
    print("   ✓ Timeline-based conversation management")
    print("   ✓ Interactive conversation mode")
    print("   ✓ Resource and agent discovery")
    print("   ✓ Context management")

    return agent  # Return the agent for interactive use


def interactive_chat(agent, live_mode=False):
    """Start an interactive chat session with the STARAgent."""
    print("\n" + "=" * 60)
    print("🤖 STARAgent Interactive Chat Mode")
    print("=" * 60)
    print("Commands:")
    print("  'quit', 'exit', 'bye' - End the conversation")
    print("  'help' - Show available commands")
    print("  'timeline' - Show conversation timeline")
    print("  'state' - Show agent state")
    print("  'prompt' - Show system prompt")
    print("  'reset' - Reset conversation history")

    if not live_mode:
        print("\n⚠️  SIMULATION MODE - No actual LLM calls will be made")
        print("   Responses will be simulated for demonstration purposes")
    else:
        print("\n🚀 LIVE MODE - Real LLM conversations")

    print("\nType your message and press Enter to chat with the agent...")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n💬 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye", "q"]:
                print("\n👋 Agent: Goodbye! Thanks for the conversation.")
                break

            elif user_input.lower() == "help":
                print("\n🔧 Available Commands:")
                print("  quit/exit/bye - End conversation")
                print("  help - Show this help")
                print("  timeline - Show conversation timeline")
                print("  state - Show agent state")
                print("  prompt - Show system prompt")
                print("  reset - Reset conversation history")
                print("  Any other text - Send message to agent")
                continue

            elif user_input.lower() == "timeline":
                print("\n📅 Conversation Timeline:")
                timeline_summary = agent.get_timeline_summary()
                print(timeline_summary if timeline_summary else "No conversation history yet")
                continue

            elif user_input.lower() == "state":
                print("\n📊 Agent State:")
                state = agent.get_state()
                for key, value in state.items():
                    print(f"  {key}: {value}")
                continue

            elif user_input.lower() == "prompt":
                print("\n📝 System Prompt:")
                print("-" * 40)
                print(agent._get_system_prompt())
                print("-" * 40)
                continue

            elif user_input.lower() == "reset":
                # Reset timeline
                agent._timeline.timeline.clear()
                print("\n🔄 Conversation history reset")
                continue

            # Process user message through the agent
            print("\n🤖 Agent: ", end="", flush=True)

            if live_mode:
                # Real LLM conversation
                traces = agent.query(message=user_input)
                response = traces.get("response", "No response generated")

                # Debug: Print response details
                print(f"[DEBUG] Response type: {type(response)}")
                print(f"[DEBUG] Response length: {len(response)} characters")
                print(f"[DEBUG] First 100 chars: {repr(response[:100])}")
                print(f"[DEBUG] Last 100 chars: {repr(response[-100:])}")
                print("[DEBUG] Full response:")
                print("-" * 60)
                print(response)
                print("-" * 60)
                print("[DEBUG] End of response")
            else:
                # Simulated response for demo
                print(
                    f"[SIMULATED] I understand you said: '{user_input}'. In live mode, I would process this through the STAR pattern and provide a real response using LLM capabilities."
                )

        except KeyboardInterrupt:
            print("\n\n👋 Agent: Conversation interrupted. Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Agent: Input ended. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Type 'help' for available commands or 'quit' to exit")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Adana STARAgent Example - STAR Pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python star_agent_example.py                    # Run examples with simulated conversation
  python star_agent_example.py --live             # Run examples with actual LLM calls
  python star_agent_example.py --interactive      # Run examples then start interactive chat
  python star_agent_example.py --chat-only        # Skip examples, go directly to chat mode
  python star_agent_example.py --chat-only --live # Direct to live chat mode
  python star_agent_example.py --live --provider openai  # Override .env provider
  python star_agent_example.py --live --model claude-3-haiku  # Override .env model
        """,
    )

    parser.add_argument("--live", action="store_true", help="Run with actual LLM calls (requires API keys)")

    parser.add_argument("--interactive", action="store_true", help="Start interactive chat mode after running examples")

    parser.add_argument("--chat-only", action="store_true", help="Skip examples and go directly to interactive chat mode")

    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai", "azure", "ollama", "groq"],
        default=None,
        help="LLM provider to use (defaults to .env configuration)",
    )

    parser.add_argument("--model", help="Specific model to use (defaults to .env configuration)")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.chat_only:
        # Skip examples, go directly to chat
        print("🚀 Starting STARAgent in chat-only mode...")

        try:
            # Create agent using the same approach as main()
            if args.live:
                # Live mode - use LLM provider from .env or args
                agent = DemoSTARAgent(llm_provider=args.provider, model=args.model)
            else:
                # Simulation mode - create a basic agent for demo purposes
                print("⚠️  SIMULATION MODE - Creating agent without LLM provider")
                print("   In simulation mode, responses will be simulated")

                # Create a minimal agent for demonstration
                from adana.common.protocols import DictParams
                from adana.common.protocols.types import LearningPhase
                from adana.core.agent.base_star_agent import BaseSTARAgent

                class SimulationSTARAgent(BaseSTARAgent):
                    def _see(self, **kwargs) -> DictParams:
                        return {"timeline": None}

                    def _think(self, **kwargs) -> DictParams:
                        return {"response": "[SIMULATED RESPONSE]", "tool_calls": []}

                    def _act(self, **kwargs) -> DictParams:
                        return {"tool_results": []}

                    def _reflect(self, phase: LearningPhase, **kwargs) -> DictParams:
                        return {"_EXIT_STAR_LOOP_FLAG": True}

                    def get_state(self):
                        """Get current agent state."""
                        return {"agent_type": self.agent_type, "mode": "simulation", "resources": [], "agents": [], "workflows": []}

                    def get_timeline_summary(self):
                        """Get timeline summary."""
                        return "No conversation history in simulation mode"

                agent = SimulationSTARAgent(agent_type="demo_simulation")

            interactive_chat(agent, live_mode=args.live)
        except Exception as e:
            print(f"❌ Error creating agent: {e}")
            print("\n💡 For simulation mode, try:")
            print("   python star_agent_example.py --chat-only")
            print("\nFor live mode with your .env configuration:")
            print("   python star_agent_example.py --chat-only --live")
    else:
        # Run examples first
        agent = main(live_mode=args.live, provider=args.provider, model=args.model)

        # Start interactive mode if requested
        if args.interactive:
            interactive_chat(agent, live_mode=args.live)
