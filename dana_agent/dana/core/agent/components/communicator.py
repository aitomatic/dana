"""
Communicator: Handles LLM integration and agent communication.

This component provides functionality for:
- LLM integration and communication
- Interactive conversation interface
"""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent

# Color codes for terminal output
USER_COLOR = "\033[96m"  # Cyan
AGENT_COLOR = "\033[93m"  # Yellow
RESET_COLOR = "\033[0m"

# Set emoji for user and agent
USER_EMOJI = "👤"
AGENT_EMOJI = "🤖"


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
        print("Type '/quit', '/exit', or '/bye' to end the conversation")
        print("Type '/help' for available commands")
        print("For multi-line input: just start typing, end with empty line")
        print("=" * 50)

        # Track if we should use initial_message on first iteration
        first_iteration = True

        while True:
            try:
                # Get user input (use initial_message on first iteration if provided)
                if first_iteration and initial_message:
                    user_input = initial_message
                    print(f"\n{USER_COLOR}{USER_EMOJI} You: {user_input}{RESET_COLOR}")
                    first_iteration = False
                else:
                    # Get first line of input
                    user_input = input(f"\n{USER_COLOR}{USER_EMOJI} You: {RESET_COLOR}").strip()

                    # If first line is not empty and not a command, check for multi-line input
                    if user_input and not user_input.startswith("/") and not user_input.startswith("@"):
                        # Check if user wants to continue with more lines
                        additional_lines = []
                        while True:
                            next_line = input().strip()
                            if not next_line:  # Empty line terminates multi-line input
                                break
                            additional_lines.append(next_line)

                        # If we collected additional lines, join them
                        if additional_lines:
                            user_input = user_input + "\n" + "\n".join(additional_lines)

                # Check for exit commands
                if user_input.lower() in ["/quit", "/exit", "/bye", "/q"]:
                    print(f"\n{AGENT_COLOR}{AGENT_EMOJI} Agent: Goodbye! Thanks for the conversation.{RESET_COLOR}")
                    break

                # Check for help command
                if user_input.lower() == "/help":
                    print(f"\n{AGENT_COLOR}=== AVAILABLE COMMANDS ==={RESET_COLOR}")
                    print("• /quit, /exit, /bye, /q - End conversation")
                    print("• /help - Show this help")
                    print("• /timeline - Show conversation timeline")
                    print("• /state - Show agent state")
                    print("• /resources - List available resources")
                    print("• /workflows - List available workflows")
                    print("• /agents - List available agents")
                    print("• @agent_name/@agent_id message - Send direct message to specific agent")
                    print("• Any other text - Send message to agent")
                    print("• Multi-line input: just type, end with empty line")
                    continue

                # Check for special commands
                if user_input.lower() == "/timeline":
                    print(f"\n{AGENT_COLOR}=== CONVERSATION TIMELINE ==={RESET_COLOR}")
                    print(self._agent._state.get_timeline_summary())
                    continue

                if user_input.lower() == "/state":
                    print(f"\n{AGENT_COLOR}=== AGENT STATE ==={RESET_COLOR}")
                    state = self._agent._state.get_state()
                    for key, value in state.items():
                        print(f"{key}: {value}")
                    continue

                if user_input.lower() == "/resources":
                    resources = self._agent.available_resources
                    print(f"\n{AGENT_COLOR}=== AVAILABLE RESOURCES ==={RESET_COLOR}")
                    if resources:
                        for resource in resources:
                            print(f"• {resource.resource_type} (ID: {resource.resource_id})")
                    else:
                        print("No resources available")
                    continue

                if user_input.lower() == "/workflows":
                    workflows = self._agent.available_workflows
                    print(f"\n{AGENT_COLOR}=== AVAILABLE WORKFLOWS ==={RESET_COLOR}")
                    if workflows:
                        for workflow in workflows:
                            print(f"• {workflow.workflow_type} (ID: {workflow.workflow_id})")
                    else:
                        print("No workflows available")
                    continue

                if user_input.lower() == "/agents":
                    agents = self._agent.available_agents
                    print(f"\n{AGENT_COLOR}=== AVAILABLE AGENTS ==={RESET_COLOR}")
                    if agents:
                        for agent in agents:
                            print(f"• {agent.agent_type} (ID: {agent.object_id})")
                    else:
                        print("No other agents available")
                    continue

                # Check for direct agent messages (@agent_name message)
                if user_input.startswith("@"):
                    # Parse @agent_name and message
                    parts = user_input[1:].split(" ", 1)
                    if len(parts) < 2:
                        print(f"\n{AGENT_COLOR}Invalid format: {user_input}{RESET_COLOR}")
                        print("Use: @agent_name/@agent_id your message here")
                        continue

                    target_agent_name = parts[0]
                    message = parts[1]

                    # Find the target agent
                    target_agent = None
                    # Include current agent in the search list
                    all_agents = list(self._agent.available_agents) + [self._agent]
                    for agent in all_agents:
                        if agent.agent_type.lower() == target_agent_name.lower() or agent.object_id == target_agent_name:
                            target_agent = agent
                            break

                    if target_agent is None:
                        print(f"\n{AGENT_COLOR}Agent '{target_agent_name}' not found{RESET_COLOR}")
                        print("Type '/agents' to see available agents and their IDs")
                        continue

                    # Send message to target agent
                    print(f"\n{AGENT_COLOR}Sending to {target_agent.agent_type}:{RESET_COLOR} ", end="", flush=True)
                    traces = target_agent.query(message=message)
                    response = traces.get("response", "No response generated")
                    print(f"{AGENT_COLOR}{AGENT_EMOJI} {response}{RESET_COLOR}")
                    continue

                # Check for unrecognized commands (start with / but not recognized)
                if user_input.startswith("/") and user_input.lower() not in [
                    "/quit",
                    "/exit",
                    "/bye",
                    "/q",
                    "/help",
                    "/timeline",
                    "/state",
                    "/resources",
                    "/workflows",
                    "/agents",
                ]:
                    print(f"\n{AGENT_COLOR}Command not supported: {user_input}{RESET_COLOR}")
                    print("Type '/help' for available commands")
                    continue

                # Skip empty input
                if not user_input:
                    continue

                # Process the message through the agent
                print(f"\n{AGENT_COLOR}{AGENT_EMOJI} Agent: {RESET_COLOR}", end="", flush=True)
                traces = self._agent.query(message=user_input)
                response = traces.get("response", "No response generated")
                print(f"{AGENT_COLOR}{response}{RESET_COLOR}")

            except KeyboardInterrupt:
                print(f"\n\n{AGENT_COLOR}{AGENT_EMOJI} Agent: Conversation interrupted. Goodbye!{RESET_COLOR}")
                break
            except EOFError:
                print(f"\n\n{AGENT_COLOR}{AGENT_EMOJI} Agent: Input ended. Goodbye!{RESET_COLOR}")
                break
            except Exception as e:
                print(f"\n{AGENT_COLOR}Error: {e}{RESET_COLOR}")
                print("Type '/help' for available commands or '/quit' to exit")
