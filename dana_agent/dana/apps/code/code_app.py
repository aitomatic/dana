"""Dana Code Application - Wires DanaCodingAgent with RichCLIRenderer."""

import logging
import os
import sys

from dotenv import find_dotenv, load_dotenv
import structlog


def _load_env():
    """Load environment variables from .env file (overrides existing env vars)."""
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path, override=True)
    else:
        load_dotenv(override=True)


_load_env()

from dana.cli.rich_cli_renderer import RichCLIRenderer
from dana.core.agent.builtin_agents.dana_coding_agent import DanaCodingAgent


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


class DanaCodeApp:
    """Dana Code - Interactive coding agent with rich CLI."""

    def __init__(self):
        """Initialize the Dana Code application."""
        if sys.platform == "win32":
            term = os.environ.get("TERM", "")
            if term in ["xterm-256color", "xterm-color"] and not os.environ.get("WT_SESSION"):
                os.environ["PROMPT_TOOLKIT_NO_CONSOLE"] = "1"

        # Suppress debug logging
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
        )

        self.agent = None
        self.renderer = None
        self.session = None

        if PROMPT_TOOLKIT_AVAILABLE and FileHistory and PromptSession:
            from pathlib import Path

            history_dir = Path.home() / ".adana"
            history_dir.mkdir(exist_ok=True)
            history_file = history_dir / "dana_code_history.txt"

            try:
                self.session = PromptSession(
                    history=FileHistory(str(history_file)),
                    style=self._get_style(),
                )
            except Exception as e:
                if "NoConsoleScreenBufferError" in str(e) or "console" in str(e).lower():
                    self.session = None
                else:
                    raise

    def _get_style(self):
        """Get the prompt_toolkit style."""
        if PROMPT_TOOLKIT_AVAILABLE and Style:
            return Style.from_dict(
                {
                    "prompt": "#00aa00 bold",
                }
            )
        return None

    def _initialize_agent(self):
        """Initialize DanaCodingAgent with RichCLIRenderer."""
        llm_provider = os.environ.get("DANA_LLM_PROVIDER", "openai")
        model = os.environ.get("DANA_MODEL", "gpt-5")

        self.agent = DanaCodingAgent(
            agent_id="dana-code",
            agent_type="dana_coding_agent",
            llm_provider=llm_provider,
            model=model,
        )

        self.renderer = RichCLIRenderer(verbose=True, show_tool_calls=True)
        self.agent.with_notifiable(self.renderer)

        print(f"Agent ready (provider={llm_provider}, model={model})\n")

    def run(self):
        """Run the interactive loop."""
        print("\nDana Code - Interactive Coding Agent")
        print("Type /help for commands, /exit to quit.\n")

        self._initialize_agent()

        while True:
            try:
                if PROMPT_TOOLKIT_AVAILABLE and self.session:
                    user_input = self.session.prompt("You: ")
                else:
                    user_input = input("You: ")

                if not user_input.strip():
                    continue

                if user_input.strip().lower() in ["exit", "quit", "bye", "/exit"]:
                    print("\nGoodbye!")
                    break

                if user_input.strip().startswith("/"):
                    if self._handle_command(user_input.strip()):
                        continue
                    else:
                        break

                self._converse(user_input)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Type /help for commands or /exit to quit.")

    def _handle_command(self, command: str) -> bool:
        """Handle slash commands. Returns True to continue, False to exit."""
        cmd = command[1:].lower().strip()
        assert self.agent is not None
        assert self.renderer is not None

        if cmd == "help":
            print("""
Commands:
  /help     - Show this help
  /compact  - Toggle verbose output
  /status   - Show agent and model info
  /reset    - Clear conversation history
  /exit     - Exit
""")
            return True

        elif cmd == "compact":
            self.renderer.verbose = not self.renderer.verbose
            mode = "verbose" if self.renderer.verbose else "compact"
            print(f"\nOutput mode: {mode}\n")
            return True

        elif cmd == "status":
            state = self.agent.get_state()
            print(f"\nAgent: {state.get('object_id', 'unknown')}")
            print(f"Type: {state.get('agent_type', 'unknown')}")
            print(f"Provider: {self.agent._llm_config.get('provider', 'unknown')}")
            print(f"Model: {self.agent._llm_config.get('model', 'unknown')}")
            print(f"Timeline entries: {state.get('timeline_entries', 0)}")
            print()
            return True

        elif cmd == "reset":
            self.agent._timeline.timeline.clear()
            print("\nConversation history reset.\n")
            return True

        else:
            print(f"\nUnknown command: {command}")
            print("Type /help for available commands.\n")
            return True

    def _converse(self, message: str):
        """Send a message to the agent and display the response."""
        assert self.agent is not None
        assert self.renderer is not None

        try:
            traces = self.agent.query(message=message)
            response = traces.get("response", "")

            # Only print response if renderer is not in verbose mode
            # (verbose renderer already prints the final response)
            if response and not self.renderer.verbose:
                print(f"\n{response}\n")

        except Exception as e:
            print(f"\nError: {e}\n")
