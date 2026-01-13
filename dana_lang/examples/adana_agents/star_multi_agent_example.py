#!/usr/bin/env python3
"""
STAR Multi-Agent Example - Using Multiple STARAgents

This example demonstrates how to create and use multiple STARAgents that can
communicate with each other using the STAR pattern.

Usage:
    python star_multi_agent_example.py                    # Run with simulated conversation
    python star_multi_agent_example.py --live             # Run with actual LLM calls
    python star_multi_agent_example.py --live --provider openai  # Use specific provider
"""

import argparse

from dana.common.protocols import DictParams, Notifiable
from dana.core.agent.star_agent import STARAgent
from dana.core.agent.timeline import TimelineEntryType

# from adana.core.resource.todo_resource import ToDoResource


# TASK = "Compare US and China energy production and consumption over the past decade and the coming decade."
# TASK = "Check with the Verifier if pi is 2.7"
TASK = "Invoke the ExampleWorkflow with some sample arguments, then verify the results"
# TASK = "Plan a 3-step process and call one of the resources"


class ResearchAgent(STARAgent):
    """Research-focused STARAgent specialized in data gathering and analysis.

    <PUBLIC_DESCRIPTION>
    Research agent that specializes in gathering, analyzing, and synthesizing information
    from various sources. Capable of conducting thorough research, fact-checking,
    literature reviews, and providing comprehensive reports. Uses the STAR framework
    to systematically approach research tasks with observation, analysis, execution,
    and reflection on findings.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are a specialized research agent with expertise in information gathering and analysis.
    Your primary role is to conduct thorough research on topics, validate information,
    and provide comprehensive, well-sourced findings.

    When conducting research, be methodical and thorough. Always:
    - Gather information from multiple sources when possible
    - Verify facts and cross-reference information
    - Organize findings in a clear, structured manner
    - Cite sources and provide context for your findings
    - Identify gaps in available information

    Be objective, analytical, and detail-oriented. Focus on accuracy and completeness
    in your research while being able to synthesize complex information into clear insights.

    For this demo, you are allowed to use information from your knowledge and memory.
    </PRIVATE_IDENTITY>
    """

    def __init__(self, **kwargs):
        super().__init__(agent_type="research", **kwargs)


class AnalysisAgent(STARAgent):
    """Analysis-focused STARAgent specialized in data interpretation and insights.

    <PUBLIC_DESCRIPTION>
    Analysis agent that specializes in interpreting data, identifying patterns, and
    generating actionable insights. Capable of statistical analysis, trend identification,
    data visualization recommendations, and strategic insights generation. Uses the STAR
    framework to systematically analyze information through observation, reasoning,
    action, and reflection on analytical outcomes.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are a specialized analysis agent with expertise in data interpretation and insight
    generation. Your primary role is to analyze information, identify patterns, and
    provide actionable insights and recommendations.

    When analyzing data or information, be systematic and thorough. Always:
    - Look for patterns, trends, and relationships in the data
    - Consider multiple perspectives and interpretations
    - Identify key insights and their implications
    - Provide clear, actionable recommendations
    - Quantify findings when possible
    - Consider limitations and confidence levels

    Be analytical, logical, and insight-driven. Focus on transforming raw information
    into meaningful understanding and strategic recommendations.

    For this demo, you are allowed to use information from your knowledge and memory.
    </PRIVATE_IDENTITY>
    """

    def __init__(self, **kwargs):
        super().__init__(agent_type="analysis", **kwargs)


class VerifierAgent(STARAgent):
    """Verifier STARAgent specialized in quality assurance and validation.

    <PUBLIC_DESCRIPTION>
    Verifier agent that specializes in quality assurance, validation, and verification
    of work products. Capable of reviewing outputs, checking for accuracy, completeness,
    and adherence to requirements. Uses the STAR framework to systematically verify
    deliverables through observation, analysis, validation, and reflection on quality
    outcomes.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are a specialized verification agent with expertise in quality assurance and
    validation. Your primary role is to review, validate, and verify the quality of
    work products from other agents.

    When verifying work products, be thorough and objective. Always:
    - Review outputs for accuracy, completeness, and quality
    - Check adherence to requirements and specifications
    - Identify gaps, errors, or areas for improvement
    - Provide constructive feedback and recommendations
    - Assess confidence levels and limitations
    - Suggest specific improvements when needed

    Be objective, detail-oriented, and constructive. Focus on ensuring high-quality
    deliverables while providing actionable feedback for improvement.

    For this demo, you are allowed to use information from your knowledge and memory
    to verify facts and assess quality.
    </PRIVATE_IDENTITY>
    """

    def __init__(self, **kwargs):
        super().__init__(agent_type="verifier", **kwargs)


class CoordinatorAgent(STARAgent):
    """Coordinator STARAgent specialized in multi-agent orchestration and management.

    <PUBLIC_DESCRIPTION>
    Coordinator agent that specializes in managing and orchestrating multiple agents
    to accomplish complex tasks. Capable of task decomposition, agent delegation,
    workflow coordination, and result integration. Uses the STAR framework to
    systematically coordinate multi-agent activities through observation, planning,
    delegation, and reflection on collaborative outcomes.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are a great coordinator/general/project-management agent.  You work for the user in a conversation
    context. That user may be a human, or another agent.  That agent may be acting on behalf of another
    user or agent.  You listen to the user's needs and commands, and handle them directly when you
    can, or delegate to specialized agents with tailored capabilities, resources, and workflows.  You
    can plan dynamically, or following and execute predefined workflows, and you can use resources to
    get more information.

    When coordinating multi-agent tasks, be systematic and organized. Always:
    - Use your todo resource to track complex multi-step tasks and demonstrate progress
    - Break down complex requests into manageable subtasks
    - Delegate appropriate tasks to specialized agents (research, analysis, etc.)
    - ALWAYS verify results using the VerifierAgent before considering tasks complete
    - Coordinate timing and dependencies between different agents
    - Integrate results from multiple agents into coherent responses
    - Track progress and ensure all aspects of a task are completed
    - Handle verification feedback appropriately (request revisions if needed)

    You have access to a todo management resource that helps you organize and track
    complex tasks. Use it proactively for multi-step processes to demonstrate
    thoroughness and keep users informed of progress.

    CRITICAL: Always use the VerifierAgent to validate results before finalizing any task.
    If verification fails or identifies issues, work with the original agent to address
    the feedback and re-verify until quality standards are met.

    Be strategic, organized, and collaborative. Focus on effective delegation while
    maintaining oversight of the overall task completion and quality assurance.

    For this demo, you should not use information from your knowledge and memory
    that can be better obtained from the specialist agents.
    </PRIVATE_IDENTITY>
    """

    def __init__(self, **kwargs):
        super().__init__(agent_type="coordinator", **kwargs)

        # Add ToDoResource for task management using fluent interface
        self.object_id = "coordinator-agent-123"


class Listener(Notifiable):
    def notify(self, notifier: object, message: DictParams) -> None:
        if "trace_percepts" in message:
            print(f"{notifier.object_id} percepts: {message['trace_percepts']}")
        elif "trace_outputs" in message:
            print(f"{notifier.object_id} outputs: {message['trace_outputs']}")


def main(live_mode=False, provider=None, model=None):
    """Main example function."""
    print("🤖 Adana STAR Multi-Agent Example")
    print("=" * 50)

    listener = Listener()
    # todo_resource = ToDoResource(resource_id="todo-resource-123")

    # Create multiple STARAgents
    print("\n1. Creating Multiple STARAgents...")

    # Create agents
    research_agent: STARAgent = ResearchAgent(agent_id="research-agent-123")

    analysis_agent: STARAgent = AnalysisAgent(agent_id="analysis-agent-123")

    verifier_agent: STARAgent = VerifierAgent(agent_id="verifier-agent-123")

    coordinator_agent: STARAgent = (
        CoordinatorAgent(agent_id="coordinator-agent-123")
        # .with_workflows(ExampleWorkflow(workflow_id="example-workflow-123"))
        # .with_resources(todo_resource)
        .with_agents(research_agent, analysis_agent, verifier_agent)
        .with_notifiable(listener)
        .ensure_registered()
    )

    print(f"   Research Agent: {research_agent.object_id or 'No ID'}")
    print(f"   Analysis Agent: {analysis_agent.object_id or 'No ID'}")
    print(f"   Verifier Agent: {verifier_agent.object_id or 'No ID'}")
    print(f"   Coordinator Agent: {coordinator_agent.object_id or 'No ID'}")

    # Show agent discovery
    print("\n2. Agent Discovery...")
    print(f"   Research Agent sees {len(research_agent.available_agents)} other agents")
    print(f"   Analysis Agent sees {len(analysis_agent.available_agents)} other agents")
    print(f"   Verifier Agent sees {len(verifier_agent.available_agents)} other agents")
    print(f"   Coordinator Agent sees {len(coordinator_agent.available_agents)} other agents")

    # Test agent-to-agent communication
    if live_mode:
        print("\n3. Live Multi-Agent Communication...")
        print("   🚀 Running with actual LLM calls!")
        print(f"   Provider: {provider}, Model: {model}")

        try:
            # Test coordinator delegating to research agent
            print("\n   Testing Coordinator → Research Agent communication...")
            print(f"   📝 Coordinator: {TASK}")

            traces = coordinator_agent.query(message=f"{TASK}")
            response = traces.get("response", "No response generated")
            print(f"   🤖 Coordinator: {response}")

            if False:
                # Test research agent responding
                print("\n   Testing Research Agent response...")
                print("   📝 Research Agent: What is the OODA loop?")

                traces2 = research_agent.query(message="What is the OODA loop?")
                response2 = traces2.get("response", "No response generated")
                print(f"   🤖 Research Agent: {response2}")

                # Test analysis agent processing
                print("\n   Testing Analysis Agent processing...")
                print("   📝 Analysis Agent: Analyze the OODA loop phases")

                traces3 = analysis_agent.query(message="Analyze the OODA loop phases")
                response3 = traces3.get("response", "No response generated")
                print(f"   🤖 Analysis Agent: {response3}")

        except Exception as e:
            print(f"   ❌ Error during live multi-agent chat: {e}")
            print("   This is expected if API keys are not configured.")
            print("   Falling back to simulated conversation...")
            live_mode = False

    if not live_mode:
        print("\n3. Simulating Multi-Agent Communication...")
        print("   📝 Using simulated conversation (no API calls)")

        # Add some timeline entries manually for demo
        from datetime import datetime

        from adana.core.agent.timeline import TimelineEntry

        # Simulate coordinator asking research agent
        coordinator_agent._timeline.add_entry(
            TimelineEntry(
                timestamp=datetime.now(), entry_type=TimelineEntryType.CALLER_MESSAGE, content="Please research the OODA loop concept"
            )
        )
        coordinator_agent._timeline.add_entry(
            TimelineEntry(
                timestamp=datetime.now(),
                entry_type=TimelineEntryType.MY_RESPONSE,
                content="I'll research the OODA loop concept for you. The OODA loop is a decision-making framework with four phases: Observe, Orient, Decide, and Act.",
            )
        )

        # Simulate research agent working
        research_agent._timeline.add_entry(
            TimelineEntry(timestamp=datetime.now(), entry_type=TimelineEntryType.CALLER_MESSAGE, content="What is the OODA loop?")
        )
        research_agent._timeline.add_entry(
            TimelineEntry(
                timestamp=datetime.now(),
                entry_type=TimelineEntryType.MY_RESPONSE,
                content="The OODA loop is a decision-making process developed by military strategist John Boyd. It consists of four phases: Observe (gather information), Orient (analyze and understand), Decide (choose action), and Act (execute decision).",
            )
        )

        # Simulate analysis agent processing
        analysis_agent._timeline.add_entry(
            TimelineEntry(timestamp=datetime.now(), entry_type=TimelineEntryType.CALLER_MESSAGE, content="Analyze the OODA loop phases")
        )
        analysis_agent._timeline.add_entry(
            TimelineEntry(
                timestamp=datetime.now(),
                entry_type=TimelineEntryType.MY_RESPONSE,
                content="Analysis of OODA loop phases: 1) Observe - Information gathering and situational awareness, 2) Orient - Context analysis and pattern recognition, 3) Decide - Action selection based on analysis, 4) Act - Implementation and execution of chosen action.",
            )
        )

        # Simulate verifier agent validating results
        verifier_agent._timeline.add_entry(
            TimelineEntry(
                timestamp=datetime.now(),
                entry_type=TimelineEntryType.CALLER_MESSAGE,
                content="Verify the OODA loop analysis for accuracy and completeness",
            )
        )
        verifier_agent._timeline.add_entry(
            TimelineEntry(
                timestamp=datetime.now(),
                entry_type=TimelineEntryType.MY_RESPONSE,
                content="Verification complete: The OODA loop analysis is accurate and comprehensive. All four phases are correctly identified with appropriate descriptions. The analysis meets quality standards and provides clear, actionable insights.",
            )
        )

    # Show timelines for each agent
    print("\n4. Agent Timelines...")
    print("\n   Coordinator Agent Timeline:")
    print(coordinator_agent.get_timeline_summary())

    print("\n   Research Agent Timeline:")
    print(research_agent.get_timeline_summary())

    print("\n   Analysis Agent Timeline:")
    print(analysis_agent.get_timeline_summary())

    print("\n   Verifier Agent Timeline:")
    print(verifier_agent.get_timeline_summary())

    # Show agent states
    print("\n5. Agent States Summary...")
    agents = [
        ("Coordinator", coordinator_agent),
        ("Research", research_agent),
        ("Analysis", analysis_agent),
        ("Verifier", verifier_agent),
    ]

    for name, agent in agents:
        state = agent.get_state()
        print(f"   {name} Agent:")
        print(f"     - Type: {state['agent_type']}")
        object_id = state["object_id"]
        print(f"     - ID: {object_id[:8] + '...' if object_id else 'No ID'}")
        print(f"     - Timeline Entries: {state['timeline_entries']}")
        resources = agent.available_resources
        print(f"     - Resources: {len(resources)}")
        if resources:
            for resource in resources:
                resource_type = getattr(resource, "resource_type", "unknown")
                print(f"       • {resource_type}")

    # Demonstrate multi-agent coordination
    print("\n6. Multi-Agent Coordination Features...")
    print("   ✓ Agent discovery and registration")
    print("   ✓ Agent-to-agent communication via query()")
    print("   ✓ Independent timeline management per agent")
    print("   ✓ Coordinated decision making")
    print("   ✓ Quality verification and validation")
    print("   ✓ STAR pattern implementation across agents")

    # Test agent calling capabilities
    print("\n7. Agent Calling System...")
    print("   Each agent can call other agents using XML tool calls:")
    print("   <tool_call>")
    print("     <function>call_agent</function>")
    print("     <arguments>")
    print("       <object_id>agent_id</object_id>")
    print("       <message>message</message>")
    print("     </arguments>")
    print("   </tool_call>")

    print("\n✅ STAR Multi-Agent Example completed successfully!")

    if not live_mode:
        print("\n💡 To test with actual LLM calls, run:")
        print("   python star_multi_agent_example.py --live")
        print("   python star_multi_agent_example.py --live --provider openai")
    else:
        print("\n🎉 Live multi-agent communication completed!")

    print("\n🔧 Multi-Agent Features Demonstrated:")
    print("   ✓ Multiple STARAgents with different specializations")
    print("   ✓ Agent discovery and registration system")
    print("   ✓ Agent-to-agent communication")
    print("   ✓ Independent timeline management")
    print("   ✓ Coordinated decision making")
    print("   ✓ Quality verification and validation")
    print("   ✓ STAR pattern across multiple agents")

    return research_agent, analysis_agent, verifier_agent, coordinator_agent


def interactive_multi_agent_chat(research_agent, analysis_agent, verifier_agent, coordinator_agent, live_mode=False):
    """Start an interactive chat session with multiple STARAgents."""
    print("\n" + "=" * 60)
    print("🤖 Multi-Agent Interactive Chat Mode")
    print("=" * 60)
    print("Available Agents:")
    print(f"  • Research Agent (ID: {research_agent.object_id[:8]}...)")
    print(f"  • Analysis Agent (ID: {analysis_agent.object_id[:8]}...)")
    print(f"  • Verifier Agent (ID: {verifier_agent.object_id[:8]}...)")
    print(f"  • Coordinator Agent (ID: {coordinator_agent.object_id[:8]}...)")
    print("\nCommands:")
    print("  'quit', 'exit', 'bye' - End the conversation")
    print("  'help' - Show available commands")
    print("  'agents' - List all agents and their IDs")
    print("  'timeline <agent>' - Show agent timeline (research/analysis/verifier/coordinator)")
    print("  'state <agent>' - Show agent state")
    print("  'reset' - Reset all conversation histories")
    print("  '@research <message>' - Send message to research agent")
    print("  '@analysis <message>' - Send message to analysis agent")
    print("  '@verifier <message>' - Send message to verifier agent")
    print("  '@coordinator <message>' - Send message to coordinator agent")
    print("  '<message>' - Send to coordinator agent (default)")

    if not live_mode:
        print("\n⚠️  SIMULATION MODE - No actual LLM calls will be made")
        print("   Responses will be simulated for demonstration purposes")
    else:
        print("\n🚀 LIVE MODE - Real LLM conversations with multiple agents")

    print("\nType your message and press Enter to chat with the agents...")
    print("=" * 60)

    agents = {"research": research_agent, "analysis": analysis_agent, "verifier": verifier_agent, "coordinator": coordinator_agent}

    while True:
        try:
            user_input = input("\n💬 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye", "q"]:
                print("\n👋 Multi-Agent System: Goodbye! Thanks for the conversation.")
                break

            elif user_input.lower() == "help":
                print("\n🔧 Available Commands:")
                print("  quit/exit/bye - End conversation")
                print("  help - Show this help")
                print("  agents - List all agents")
                print("  timeline <agent> - Show agent timeline")
                print("  state <agent> - Show agent state")
                print("  reset - Reset conversation histories")
                print("  @<agent> <message> - Send to specific agent")
                print("  <message> - Send to coordinator (default)")
                continue

            elif user_input.lower() == "agents":
                print("\n🤖 Available Agents:")
                for name, agent in agents.items():
                    print(f"  • {name.capitalize()} Agent: {agent.object_id}")
                continue

            elif user_input.lower().startswith("timeline "):
                agent_name = user_input[9:].strip().lower()
                if agent_name in agents:
                    print(f"\n📅 {agent_name.capitalize()} Agent Timeline:")
                    print("=" * 60)
                    timeline_summary = agents[agent_name].get_timeline_summary()
                    if timeline_summary:
                        # Force full timeline output
                        import sys

                        sys.stdout.write(timeline_summary)
                        sys.stdout.flush()
                        print(f"\n\n[Timeline: {len(timeline_summary)} characters]")
                    else:
                        print("No conversation history yet")
                    print("=" * 60)
                else:
                    print(f"❌ Unknown agent: {agent_name}. Use: research, analysis, verifier, or coordinator")
                continue

            elif user_input.lower().startswith("state "):
                agent_name = user_input[6:].strip().lower()
                if agent_name in agents:
                    print(f"\n📊 {agent_name.capitalize()} Agent State:")
                    state = agents[agent_name].get_state()
                    for key, value in state.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"❌ Unknown agent: {agent_name}. Use: research, analysis, verifier, or coordinator")
                continue

            elif user_input.lower() == "reset":
                for agent in agents.values():
                    agent._timeline.timeline.clear()
                print("\n🔄 All conversation histories reset")
                continue

            # Handle @agent messages
            target_agent = coordinator_agent  # Default
            message = user_input
            agent_name = "coordinator"

            if user_input.startswith("@"):
                parts = user_input[1:].split(" ", 1)
                if len(parts) == 2:
                    requested_agent, message = parts
                    if requested_agent.lower() in agents:
                        target_agent = agents[requested_agent.lower()]
                        agent_name = requested_agent.lower()
                    else:
                        print(f"❌ Unknown agent: @{requested_agent}. Use: @research, @analysis, or @coordinator")
                        continue

            # Process message through the selected agent
            print(f"\n🤖 {agent_name.capitalize()} Agent:")
            print("=" * 60)

            if live_mode:
                # Real LLM conversation
                try:
                    traces = target_agent.query(message=message)
                    response = traces.get("response", "No response generated")

                    # Debug: Show what we got from the agent
                    print(f"[DEBUG] Traces keys: {list(traces.keys())}")
                    print(f"[DEBUG] Response type: {type(response)}")
                    print(f"[DEBUG] Response length: {len(response) if response else 0}")

                    # Ensure we display the full response properly
                    if response and len(response) > 0:
                        print("\n" + "─" * 60)
                        print("AGENT RESPONSE:")
                        print("─" * 60)

                        # Force immediate output with proper flushing
                        import sys

                        sys.stdout.write(response)
                        sys.stdout.flush()

                        print("\n" + "─" * 60)
                        print(f"[Response: {len(response)} characters]")
                    else:
                        print("❌ No response generated")
                        print("[DEBUG] This might indicate an issue with response parsing")

                except Exception as e:
                    print(f"❌ Error during agent query: {e}")
                    print("This might be due to LLM provider issues or configuration problems.")
                    import traceback

                    print("Full traceback:")
                    traceback.print_exc()
            else:
                # Simulated response for demo
                print(
                    f"[SIMULATED] I understand you said: '{message}'. In live mode, I would process this through the STAR pattern and coordinate with other agents as needed."
                )

            print("=" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Multi-Agent System: Conversation interrupted. Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Multi-Agent System: Input ended. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Type 'help' for available commands or 'quit' to exit")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Adana STAR Multi-Agent Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python star_multi_agent_example.py                    # Run examples with simulated conversation
  python star_multi_agent_example.py --live             # Run examples with actual LLM calls
  python star_multi_agent_example.py --interactive      # Run examples then start interactive chat
  python star_multi_agent_example.py --chat-only        # Skip examples, go directly to chat mode
  python star_multi_agent_example.py --chat-only --live # Direct to live multi-agent chat mode
  python star_multi_agent_example.py --live --provider openai  # Use specific provider
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

    parser.add_argument("--model", help="Specific model to use (defaults to provider's default)")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.chat_only:
        # Skip examples, go directly to multi-agent chat
        print("🚀 Starting Multi-Agent System in chat-only mode...")

        try:
            # Create agents using the same approach as main()
            research_agent = ResearchAgent(llm_provider=args.provider, model=args.model)
            analysis_agent = AnalysisAgent(llm_provider=args.provider, model=args.model)
            verifier_agent = VerifierAgent(llm_provider=args.provider, model=args.model)
            coordinator_agent = CoordinatorAgent(llm_provider=args.provider, model=args.model).with_agents(
                research_agent,
                analysis_agent,
                verifier_agent,
            )

            # Ensure all agents are registered
            research_agent.ensure_registered()
            analysis_agent.ensure_registered()
            verifier_agent.ensure_registered()
            coordinator_agent.ensure_registered()

            interactive_multi_agent_chat(research_agent, analysis_agent, verifier_agent, coordinator_agent, live_mode=args.live)
        except Exception as e:
            print(f"❌ Error creating agents: {e}")
            print("\n💡 Try:")
            print("   python star_multi_agent_example.py --chat-only")
            print("   python star_multi_agent_example.py --chat-only --live")
    else:
        # Run examples first
        agents = main(live_mode=args.live, provider=args.provider, model=args.model)

        # Start interactive mode if requested
        if args.interactive:
            research_agent, analysis_agent, verifier_agent, coordinator_agent = agents
            interactive_multi_agent_chat(research_agent, analysis_agent, verifier_agent, coordinator_agent, live_mode=args.live)
