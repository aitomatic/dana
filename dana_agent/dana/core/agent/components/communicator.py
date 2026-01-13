"""
Communicator: Handles LLM integration and agent communication.

This component provides functionality for:
- LLM integration and communication
- Interactive conversation interface
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING
from uuid import uuid4


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent


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

    def converse(self, initial_message: str | None = None, session_id: str | None = None) -> None:
        """
        Interactive conversation loop with a human user.

        Args:
            initial_message: Optional initial message to start the conversation
            session_id: Optional session identifier. If None, generates UUID.
        """
        # Generate session_id if not provided
        if session_id is None:
            session_id = str(uuid4())

        agent_type = self._agent.agent_type
        print(f"\n=== {agent_type.upper()} AGENT CONVERSATION ===")
        print("Type '/quit', '/exit', or '/bye' to end the conversation")
        print("Type '/help' for available commands")
        print("=" * 50)

        # Track if we should use initial_message on first iteration
        first_iteration = True

        while True:
            try:
                # Get user input (use initial_message on first iteration if provided)
                if first_iteration and initial_message:
                    user_input = initial_message
                    print(f"\nYou: {user_input}")
                    first_iteration = False
                else:
                    user_input = input("\nYou: ").strip()
                    # Save events if EventLog exists
                    if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                        self._agent._event_log.save(session_id)
                    # Save timeline (agent, codec, storage_config already set in __init__)
                    if hasattr(self._agent, "_timeline") and self._agent._timeline is not None:
                        self._agent._timeline.save(session_id)

                # Check for exit commands
                if user_input.lower() in ["/quit", "/exit", "/bye", "/q"]:
                    print("\nAgent: Goodbye! Thanks for the conversation.")
                    break

                # Check for help command
                if user_input.lower() == "/help":
                    print("\n=== AVAILABLE COMMANDS ===")
                    print("• /quit, /exit, /bye, /q - End conversation")
                    print("• /help - Show this help")
                    print("• /timeline - Show conversation timeline")
                    print("• /state - Show agent state")
                    print("• /resources - List available resources")
                    print("• /workflows - List available workflows")
                    print("• /agents - List available agents")
                    print("• @agent_name/@agent_id message - Send direct message to specific agent")
                    print("• Any other text - Send message to agent")
                    continue

                # Check for special commands
                if user_input.lower() == "/timeline":
                    print("\n=== CONVERSATION TIMELINE ===")
                    print(self._agent._state.get_timeline_summary())
                    continue

                if user_input.lower() == "/state":
                    print("\n=== AGENT STATE ===")
                    state = self._agent._state.get_state()
                    for key, value in state.items():
                        print(f"{key}: {value}")
                    continue

                if user_input.lower() == "/resources":
                    resources = self._agent.available_resources
                    print("\n=== AVAILABLE RESOURCES ===")
                    if resources:
                        for resource in resources:
                            print(f"• {resource.resource_type} (ID: {resource.resource_id})")
                    else:
                        print("No resources available")
                    continue

                if user_input.lower() == "/workflows":
                    workflows = self._agent.available_workflows
                    print("\n=== AVAILABLE WORKFLOWS ===")
                    if workflows:
                        for workflow in workflows:
                            print(f"• {workflow.workflow_type} (ID: {workflow.workflow_id})")
                    else:
                        print("No workflows available")
                    continue

                if user_input.lower() == "/agents":
                    agents = self._agent.available_agents
                    print("\n=== AVAILABLE AGENTS ===")
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
                        print(f"\nInvalid format: {user_input}")
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
                        print(f"\nAgent '{target_agent_name}' not found")
                        print("Type '/agents' to see available agents and their IDs")
                        continue

                    # Send message to target agent
                    print(f"\nSending to {target_agent.agent_type}: ", end="", flush=True)
                    traces = target_agent.query(message=message, session_id=session_id)
                    response = traces.get("response", "No response generated")
                    print(response)
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
                    print(f"\nCommand not supported: {user_input}")
                    print("Type '/help' for available commands")
                    continue

                # Skip empty input
                if not user_input:
                    continue

                # Process the message through the agent
                print("\nAgent: ", end="", flush=True)
                traces = self._agent.query(message=user_input, session_id=session_id)
                response = traces.get("response", "No response generated")
                print(response)

            except KeyboardInterrupt:
                print("\n\nAgent: Conversation interrupted. Goodbye!")
                # Save events if EventLog exists
                if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                    self._agent._event_log.save(session_id)
                # Save timeline (agent, codec, storage_config already set in __init__)
                if hasattr(self._agent, "_timeline") and self._agent._timeline is not None:
                    self._agent._timeline.save(session_id)
                break
            except EOFError:
                print("\n\nAgent: Input ended. Goodbye!")
                # Save events if EventLog exists
                if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                    self._agent._event_log.save(session_id)
                # Save timeline (agent, codec, storage_config already set in __init__)
                if hasattr(self._agent, "_timeline") and self._agent._timeline is not None:
                    self._agent._timeline.save(session_id)
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Type '/help' for available commands or '/quit' to exit")

        # Save events if EventLog exists
        if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
            self._agent._event_log.save(session_id)
        # Save timeline (agent, codec, storage_config already set in __init__)
        if hasattr(self._agent, "_timeline") and self._agent._timeline is not None:
            self._agent._timeline.save(session_id)

    # ============================================================================
    # ASYNC INTERACTIVE CONVERSATION INTERFACE
    # ============================================================================

    async def aconverse(
        self,
        initial_message: str | None = None,
        session_id: str | None = None,
        input_handler: Callable[[], Awaitable[str]] | None = None,
    ) -> None:
        """
        Async interactive conversation loop with pluggable input handler.

        Args:
            initial_message: Optional initial message to start the conversation
            session_id: Optional session identifier. If None, generates UUID.
            input_handler: Async callable that returns user input string.
                          If None, uses default blocking input() wrapped in executor.
        """
        # Default input handler wraps blocking input() in executor
        if input_handler is None:

            async def _default_input_handler() -> str:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, lambda: input("\nYou: ").strip())

            input_handler = _default_input_handler

        # Generate session_id if not provided
        if session_id is None:
            session_id = str(uuid4())

        agent_type = self._agent.agent_type
        print(f"\n=== {agent_type.upper()} AGENT CONVERSATION (ASYNC) ===")
        print("Type '/quit', '/exit', or '/bye' to end the conversation")
        print("Type '/help' for available commands")
        print("=" * 50)

        # Track if we should use initial_message on first iteration
        first_iteration = True

        while True:
            try:
                # Get user input (use initial_message on first iteration if provided)
                if first_iteration and initial_message:
                    user_input = initial_message
                    print(f"\nYou: {user_input}")
                    first_iteration = False
                else:
                    user_input = await input_handler()
                    # Save events if EventLog exists
                    if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                        self._agent._event_log.save(session_id)
                    # Save timeline (agent, codec, storage_config already set in __init__)
                    if hasattr(self._agent, "_timeline") and self._agent._timeline is not None:
                        self._agent._timeline.save(session_id)

                # Check for exit commands
                if user_input.lower() in ["/quit", "/exit", "/bye", "/q"]:
                    print("\nAgent: Goodbye! Thanks for the conversation.")
                    break

                # Check for help command
                if user_input.lower() == "/help":
                    print("\n=== AVAILABLE COMMANDS ===")
                    print("• /quit, /exit, /bye, /q - End conversation")
                    print("• /help - Show this help")
                    print("• /timeline - Show conversation timeline")
                    print("• /state - Show agent state")
                    print("• /resources - List available resources")
                    print("• /workflows - List available workflows")
                    print("• /agents - List available agents")
                    print("• @agent_name/@agent_id message - Send direct message to specific agent")
                    print("• Any other text - Send message to agent")
                    continue

                # Check for special commands
                if user_input.lower() == "/timeline":
                    print("\n=== CONVERSATION TIMELINE ===")
                    print(self._agent._state.get_timeline_summary())
                    continue

                if user_input.lower() == "/state":
                    print("\n=== AGENT STATE ===")
                    state = self._agent._state.get_state()
                    for key, value in state.items():
                        print(f"{key}: {value}")
                    continue

                if user_input.lower() == "/resources":
                    resources = self._agent.available_resources
                    print("\n=== AVAILABLE RESOURCES ===")
                    if resources:
                        for resource in resources:
                            print(f"• {resource.resource_type} (ID: {resource.resource_id})")
                    else:
                        print("No resources available")
                    continue

                if user_input.lower() == "/workflows":
                    workflows = self._agent.available_workflows
                    print("\n=== AVAILABLE WORKFLOWS ===")
                    if workflows:
                        for workflow in workflows:
                            print(f"• {workflow.workflow_type} (ID: {workflow.workflow_id})")
                    else:
                        print("No workflows available")
                    continue

                if user_input.lower() == "/agents":
                    agents = self._agent.available_agents
                    print("\n=== AVAILABLE AGENTS ===")
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
                        print(f"\nInvalid format: {user_input}")
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
                        print(f"\nAgent '{target_agent_name}' not found")
                        print("Type '/agents' to see available agents and their IDs")
                        continue

                    # Send message to target agent (async)
                    print(f"\nSending to {target_agent.agent_type}: ", end="", flush=True)
                    traces = await target_agent.aquery(message=message, session_id=session_id)
                    response = traces.get("response", "No response generated")
                    print(response)
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
                    print(f"\nCommand not supported: {user_input}")
                    print("Type '/help' for available commands")
                    continue

                # Skip empty input
                if not user_input:
                    continue

                # Process the message through the agent (async)
                print("\nAgent: ", end="", flush=True)
                traces = await self._agent.aquery(message=user_input, session_id=session_id)
                response = traces.get("response", "No response generated")
                print(response)

            except KeyboardInterrupt:
                print("\n\nAgent: Conversation interrupted. Goodbye!")
                # Save events if EventLog exists
                if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                    self._agent._event_log.save(session_id)
                # Save timeline (agent, codec, storage_config already set in __init__)
                if hasattr(self._agent, "_timeline") and self._agent._timeline is not None:
                    self._agent._timeline.save(session_id)
                break
            except EOFError:
                print("\n\nAgent: Input ended. Goodbye!")
                # Save events if EventLog exists
                if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                    self._agent._event_log.save(session_id)
                # Save timeline (agent, codec, storage_config already set in __init__)
                if hasattr(self._agent, "_timeline") and self._agent._timeline is not None:
                    self._agent._timeline.save(session_id)
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Type '/help' for available commands or '/quit' to exit")

        # Save events if EventLog exists
        if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
            self._agent._event_log.save(session_id)
        # Save timeline (agent, codec, storage_config already set in __init__)
        if hasattr(self._agent, "_timeline") and self._agent._timeline is not None:
            self._agent._timeline.save(session_id)
