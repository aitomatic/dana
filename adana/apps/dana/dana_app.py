"""
Dana Conversational Agent Application

An interactive conversational interface where Dana agent manages
and orchestrates other agents, resources, and workflows.
"""

import logging
import os
import sys

import structlog

from adana.apps.dana.dana_agent import DanaAgent
from adana.apps.dana.thought_logger import ThoughtLogger


try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    PromptSession = None  # type: ignore
    FileHistory = None  # type: ignore
    Style = None  # type: ignore


class DanaApp:
    """Dana conversational agent application."""

    def __init__(self):
        """Initialize the Dana application."""
        # Handle Windows console environment issues
        if sys.platform == "win32":
            # Fix for Windows CI/CD environments that may have xterm-256color TERM
            # but expect Windows console behavior
            term = os.environ.get("TERM", "")
            if term in ["xterm-256color", "xterm-color"] and not os.environ.get("WT_SESSION"):
                # This is likely a CI/CD environment, disable prompt_toolkit console features
                os.environ["PROMPT_TOOLKIT_NO_CONSOLE"] = "1"

        # Configure logging to suppress debug messages
        logging.basicConfig(level=logging.WARNING, format="%(message)s")

        # Configure structlog to suppress debug logs
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
        )

        self.dana_agent = None
        self.thought_logger = None
        self.history = None
        self.session = None

        if PROMPT_TOOLKIT_AVAILABLE and FileHistory and PromptSession:
            # Use file-based history for persistence across sessions
            from pathlib import Path

            history_dir = Path.home() / ".adana"
            history_dir.mkdir(exist_ok=True)
            history_file = history_dir / "dana_history.txt"

            self.history = FileHistory(str(history_file))

            # Handle Windows console issues gracefully
            try:
                self.session = PromptSession(
                    history=self.history,
                    style=self._get_style(),
                )
            except Exception as e:
                # If prompt_toolkit fails to initialize (e.g., Windows console issues),
                # disable it and fall back to basic input()
                if "NoConsoleScreenBufferError" in str(e) or "console" in str(e).lower():
                    self.session = None
                    self.history = None
                else:
                    # Re-raise other exceptions
                    raise

    def _get_style(self):
        """Get the prompt_toolkit style.

        Returns:
            Style object for prompt formatting, or None if unavailable
        """
        if PROMPT_TOOLKIT_AVAILABLE and Style:
            return Style.from_dict(
                {
                    "prompt": "#00aa00 bold",
                    "dana": "#00aaaa bold",
                }
            )
        return None

    def _show_welcome(self):
        """Display welcome banner."""
        print("""
╔═══════════════════════════════════════════════════════════╗
║  Dana - Your AI Coordinator                               ║
║  Domain-Aware Neurosymbolic Agent                         ║
╚═══════════════════════════════════════════════════════════╝

Hi! I'm Dana, your conversational AI coordinator. I can help you:
  • Create and manage specialized agents
  • Execute workflows and access resources
  • Coordinate multi-agent operations
  • Answer questions and accomplish tasks

Commands:
  /help      - Show available commands
  /agents    - List all agents
  /resources - List all resources
  /workflows - List all workflows
  /thoughts  - Toggle thought process display
  /exit      - Exit Dana

Just tell me what you need, and I'll help you get it done!
""")

    def _initialize_dana(self):
        """Initialize Dana agent with access to all resources."""
        print("Initializing Dana...")

        # Create thought logger
        self.thought_logger = ThoughtLogger(verbose=True, show_tool_calls=True)

        # Create Dana agent
        self.dana_agent = DanaAgent(thought_logger=self.thought_logger)

        # Register Dana
        self.dana_agent.ensure_registered()

        print("Dana initialized and ready!\n")

    def run(self):
        """Run the Dana conversational interface with custom loop for command processing."""
        self._show_welcome()
        self._initialize_dana()

        # Custom loop with prompt_toolkit for better history and command control
        while True:
            try:
                # Get input with prompt_toolkit (has history) or fallback to input()
                if PROMPT_TOOLKIT_AVAILABLE and self.session:
                    user_input = self.session.prompt("You: ")
                else:
                    user_input = input("You: ")

                if not user_input.strip():
                    continue

                # Handle exit commands
                if user_input.strip().lower() in ["exit", "quit", "bye", "/exit"]:
                    print("\n👋 Dana: Goodbye! It was great working with you.")
                    break

                # Handle special commands
                if user_input.strip().startswith("/"):
                    if self._handle_command(user_input.strip()):
                        continue
                    else:
                        break

                # Converse with Dana using query()
                self._converse(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Dana: Goodbye! Have a great day.")
                break
            except EOFError:
                print("\n\n👋 Dana: Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Type /help for available commands or /exit to quit")

    def _handle_command(self, command: str) -> bool:
        """Handle special commands.

        Args:
            command: Command string starting with /

        Returns:
            True to continue, False to exit
        """
        cmd = command[1:].lower().strip()
        assert self.dana_agent is not None
        assert self.thought_logger is not None

        if cmd == "help":
            print("""
Dana Commands:
  /help      - Show this help message
  /agents    - List all available agents
  /resources - List all available resources
  /workflows - List all available workflows
  /thoughts  - Toggle thought process display
  /status    - Show Dana's current status
  /reset     - Reset conversation history
  /exit      - Exit Dana

You can also just talk to me naturally! Tell me what you need.
""")
            return True

        elif cmd == "agents":
            agents = self.dana_agent.available_agents
            print(f"\n📋 Available Agents ({len(agents)}):")
            for agent in agents:
                agent_type = getattr(agent, "agent_type", "unknown")
                agent_id = getattr(agent, "object_id", "no-id")
                print(f"  • {agent_type}: {agent_id}")
            print()
            return True

        elif cmd == "resources":
            resources = self.dana_agent.available_resources
            print(f"\n📦 Available Resources ({len(resources)}):")
            for resource in resources:
                resource_type = getattr(resource, "resource_type", "unknown")
                resource_id = getattr(resource, "object_id", "no-id")
                print(f"  • {resource_type}: {resource_id}")
            print()
            return True

        elif cmd == "workflows":
            workflows = self.dana_agent.available_workflows
            print(f"\n⚙️  Available Workflows ({len(workflows)}):")
            for workflow in workflows:
                workflow_type = getattr(workflow, "workflow_type", "unknown")
                workflow_id = getattr(workflow, "object_id", "no-id")
                print(f"  • {workflow_type}: {workflow_id}")
            print()
            return True

        elif cmd == "status":
            state = self.dana_agent.get_state()
            print("\n📊 Dana Status:")
            print(f"  Agent ID: {state.get('object_id', 'unknown')}")
            print(f"  Agent Type: {state.get('agent_type', 'unknown')}")
            print(f"  Timeline Entries: {state.get('timeline_entries', 0)}")
            print(f"  Available Agents: {len(self.dana_agent.available_agents)}")
            print(f"  Available Resources: {len(self.dana_agent.available_resources)}")
            print(f"  Available Workflows: {len(self.dana_agent.available_workflows)}")
            print()
            return True

        elif cmd == "reset":
            self.dana_agent._timeline.timeline.clear()
            print("\n🔄 Dana: Conversation history reset. Let's start fresh!")
            print()
            return True

        elif cmd == "thoughts":
            # Toggle verbose mode
            self.thought_logger.verbose = not self.thought_logger.verbose
            status = "enabled" if self.thought_logger.verbose else "disabled"
            print(f"\n💭 Thought process display {status}")
            print()
            return True

        else:
            print(f"\n❌ Unknown command: {command}")
            print("Type /help for available commands")
            print()
            return True

    def _converse(self, message: str):
        """Converse with Dana agent.

        Args:
            message: User's message to Dana
        """
        assert self.dana_agent is not None
        assert self.thought_logger is not None

        try:
            # Query Dana agent
            traces = self.dana_agent.query(message=message)
            response = traces.get("response", "I'm not sure how to respond to that. Could you rephrase?")

            # Clear any lingering thoughts before showing response
            if self.thought_logger:
                self.thought_logger._clear_thought()

            # Display response
            print("\n🤖 Dana: ", end="", flush=True)
            print(response)
            print()

        except Exception as e:
            # Clear thoughts on error too
            if self.thought_logger:
                self.thought_logger._clear_thought()

            print(f"\n❌ I encountered an error: {e}")
            print("Let's try something else.")
            print()
