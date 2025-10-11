"""
Communicator: Handles LLM integration and agent communication.

This component provides functionality for:
- LLM integration and communication
- Interactive conversation interface
"""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from adana.core.agent.star_agent import STARAgent


class Communicator:
    """Component providing LLM integration and communication capabilities."""

    def __init__(
        self,
        agent: "STARAgent",
    ):
        """
        Initialize the component with a reference to the agent.

        Args:
            agent: The agent instance this component belongs to
        """
        self._agent = agent

    # ============================================================================
    # INTERACTIVE CONVERSATION INTERFACE
    # ============================================================================

    def converse(self, initial_message: str | None = None) -> None:
        """
        Interactive conversation loop with a human user.

        Args:
            initial_message: Optional initial message to start the conversation
        """
        agent_type = self._agent.agent_type
        print(f"\n=== {agent_type.upper()} AGENT CONVERSATION ===")
        print("Type 'quit', 'exit', or 'bye' to end the conversation")
        print("Type 'help' for available commands")
        print("=" * 50)

        # Send initial message if provided
        if initial_message:
            print(f"\nAgent: {initial_message}")

        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()

                # Check for exit commands
                if user_input.lower() in ["quit", "exit", "bye", "q"]:
                    print("\nAgent: Goodbye! Thanks for the conversation.")
                    break

                # Check for help command
                if user_input.lower() == "help":
                    print("\n=== AVAILABLE COMMANDS ===")
                    print("• quit/exit/bye/q - End conversation")
                    print("• help - Show this help")
                    print("• timeline - Show conversation timeline")
                    print("• state - Show agent state")
                    print("• resources - List available resources")
                    print("• agents - List available agents")
                    print("• Any other text - Send message to agent")
                    continue

                # Check for special commands
                if user_input.lower() == "timeline":
                    print("\n=== CONVERSATION TIMELINE ===")
                    print(self._agent._state.get_timeline_summary())
                    continue

                if user_input.lower() == "state":
                    print("\n=== AGENT STATE ===")
                    state = self._agent._state.get_state()
                    for key, value in state.items():
                        print(f"{key}: {value}")
                    continue

                if user_input.lower() == "resources":
                    resources = self._agent.available_resources
                    print("\n=== AVAILABLE RESOURCES ===")
                    if resources:
                        for resource in resources:
                            print(f"• {resource}")
                    else:
                        print("No resources available")
                    continue

                if user_input.lower() == "agents":
                    agents = self._agent.available_agents
                    print("\n=== AVAILABLE AGENTS ===")
                    if agents:
                        for agent in agents:
                            print(f"• {agent.agent_type} (ID: {agent.object_id})")
                    else:
                        print("No other agents available")
                    continue

                # Skip empty input
                if not user_input:
                    continue

                # Process the message through the agent
                print("\nAgent: ", end="", flush=True)
                traces = self._agent.query(message=user_input)
                response = traces.get("response", "No response generated")
                print(response)

            except KeyboardInterrupt:
                print("\n\nAgent: Conversation interrupted. Goodbye!")
                break
            except EOFError:
                print("\n\nAgent: Input ended. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Type 'help' for available commands or 'quit' to exit")
