"""
Adana REPL Application - Interactive Python Environment

A streamlined REPL that provides an enhanced Python environment with:
- Pre-imported Adana classes (BaseAgent, StarAgent, BaseWorkflow, etc.)
- Syntax highlighting and auto-completion via prompt_toolkit
- Command system (/help, /imports, /exit)
- Async/await support
- Clean error formatting
"""

import asyncio
import os
import sys
import traceback
from typing import Any


try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.lexers import PygmentsLexer
    from prompt_toolkit.styles import Style
    from pygments.lexers.python import PythonLexer

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    # Provide dummy types for type hints when prompt_toolkit is not available
    PromptSession = None  # type: ignore
    FileHistory = None  # type: ignore
    PygmentsLexer = None  # type: ignore
    Style = None  # type: ignore
    PythonLexer = None  # type: ignore


class AdanaREPLApp:
    """Adana interactive REPL application."""

    def __init__(self):
        """Initialize the Adana REPL."""
        # Handle Windows console environment issues
        if sys.platform == "win32":
            # Fix for Windows CI/CD environments that may have xterm-256color TERM
            # but expect Windows console behavior
            term = os.environ.get("TERM", "")
            if term in ["xterm-256color", "xterm-color"] and not os.environ.get("WT_SESSION"):
                # This is likely a CI/CD environment, disable prompt_toolkit console features
                os.environ["PROMPT_TOOLKIT_NO_CONSOLE"] = "1"

        self.namespace = self._setup_namespace()
        self.history = None
        self.session = None
        self._multiline_buffer = []

        if PROMPT_TOOLKIT_AVAILABLE:
            # Use file-based history for persistence across sessions
            from pathlib import Path

            history_dir = Path.home() / ".adana"
            history_dir.mkdir(exist_ok=True)
            history_file = history_dir / "repl_history.txt"

            self.history = FileHistory(str(history_file)) if FileHistory else None

            # Handle Windows console issues gracefully
            try:
                self.session = (
                    PromptSession(
                        history=self.history,
                        lexer=PygmentsLexer(PythonLexer) if PygmentsLexer and PythonLexer else None,
                        style=self._get_style(),
                    )
                    if PromptSession
                    else None
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

    def _setup_namespace(self) -> dict[str, Any]:
        """Set up the execution namespace with pre-imported modules.

        Returns:
            Dictionary containing pre-imported classes and modules
        """
        namespace = {
            "__name__": "__main__",
            "__builtins__": __builtins__,
        }

        # Import Adana core classes
        try:
            from adana.core.agent import BaseAgent, BaseSTARAgent, STARAgent

            namespace.update(
                {
                    "BaseAgent": BaseAgent,
                    "BaseSTARAgent": BaseSTARAgent,
                    "STARAgent": STARAgent,
                }
            )
        except ImportError as e:
            print(f"Warning: Could not import agent classes: {e}")

        try:
            from adana.core.workflow import BaseWorkflow

            namespace["BaseWorkflow"] = BaseWorkflow
        except ImportError as e:
            print(f"Warning: Could not import workflow classes: {e}")

        try:
            from adana.core.resource import BaseResource

            namespace["BaseResource"] = BaseResource
        except ImportError as e:
            print(f"Warning: Could not import resource classes: {e}")

        # Import example agents from multi-agent demo
        try:
            from pathlib import Path
            import sys

            # Add examples directory to path
            examples_path = Path(__file__).parent.parent.parent.parent / "examples"
            if examples_path.exists() and str(examples_path) not in sys.path:
                sys.path.insert(0, str(examples_path))

            # from agent.star_multi_agent_example import (
            #    AnalysisAgent,
            #    CoordinatorAgent,
            #    ResearchAgent,
            #    VerifierAgent,
            # )

            # namespace.update(
            #    {
            #        "ResearchAgent": ResearchAgent,
            #        "AnalysisAgent": AnalysisAgent,
            #        "VerifierAgent": VerifierAgent,
            #        "CoordinatorAgent": CoordinatorAgent,
            #    }
            # )
        except ImportError as e:
            print(f"Warning: Could not import example agents: {e}")

        # Import example resources
        # try:
        #    from adana.lib.resources.todo_resource import ToDoResource

        #    namespace["ToDoResource"] = ToDoResource
        # except ImportError as e:
        #    print(f"Warning: Could not import ToDoResource: {e}")

        # Import example workflows
        # try:
        # from adana.lib.workflows.example_workflow import ExampleWorkflow

        #    namespace["ExampleWorkflow"] = ExampleWorkflow
        # except ImportError as e:
        #    print(f"Warning: Could not import ExampleWorkflow: {e}")

        # Add common libraries
        import logging

        namespace["logging"] = logging

        return namespace

    def _get_style(self):
        """Get the prompt_toolkit style for syntax highlighting.

        Returns:
            Style object for prompt formatting, or None if prompt_toolkit unavailable
        """
        if PROMPT_TOOLKIT_AVAILABLE and Style:
            return Style.from_dict(
                {
                    "prompt": "#00aa00 bold",
                    "continuation": "#00aa00",
                }
            )
        return None

    def run(self):
        """Run the interactive REPL session."""
        self._show_welcome()

        while True:
            try:
                # Get input
                if PROMPT_TOOLKIT_AVAILABLE and self.session:
                    line = self.session.prompt(">>> " if not self._multiline_buffer else "... ")
                else:
                    prompt = ">>> " if not self._multiline_buffer else "... "
                    line = input(prompt)

                # Handle empty lines
                if not line.strip():
                    if self._multiline_buffer:
                        # Execute multiline buffer
                        code = "\n".join(self._multiline_buffer)
                        self._multiline_buffer = []
                        self._execute(code)
                    continue

                # Handle commands
                if line.strip().startswith("/"):
                    if self._handle_command(line.strip()):
                        continue
                    else:
                        break  # Exit command

                # Check for multiline input
                if line.rstrip().endswith(":") or line.rstrip().endswith("\\"):
                    self._multiline_buffer.append(line)
                    continue

                # Add to multiline buffer if we're in multiline mode
                if self._multiline_buffer:
                    self._multiline_buffer.append(line)
                    # Don't execute yet, wait for empty line
                    continue

                # Execute single line
                self._execute(line)

            except KeyboardInterrupt:
                print("\nKeyboardInterrupt")
                self._multiline_buffer = []
                continue
            except EOFError:
                print("\nGoodbye!")
                break

    def _show_welcome(self):
        """Display welcome banner."""
        version = sys.version.split()[0]
        imports = [name for name in self.namespace.keys() if not name.startswith("_") and name not in ["logging"]]

        print(f"""
╔═══════════════════════════════════════════════════════════╗
║  Adana Interactive REPL                                   ║
║  Python {version} + Adana Framework                       ║
╚═══════════════════════════════════════════════════════════╝

Pre-imported: {", ".join(imports) if imports else "None"}

Commands:
  /help      - Show help and available commands
  /imports   - Show all pre-imported modules
  /exit      - Exit the REPL
  Ctrl+D     - Exit the REPL

Type Python code to execute it.
""")

    def _handle_command(self, line: str) -> bool:
        """Handle special REPL commands.

        Args:
            line: Command line starting with /

        Returns:
            True to continue REPL loop, False to exit
        """
        cmd = line[1:].lower().strip()

        if cmd == "help":
            self._show_help()
            return True

        elif cmd == "imports":
            self._show_imports()
            return True

        elif cmd in ("exit", "quit"):
            return False

        else:
            print(f"Unknown command: {line}")
            print("Type /help for available commands")
            return True

    def _show_help(self):
        """Show help information."""
        print("""
Adana REPL Commands:
  /help      - Show this help message
  /imports   - Show all pre-imported modules and classes
  /exit      - Exit the REPL

Python Features:
  - Full Python syntax support
  - Async/await support (use 'await' directly)
  - Multi-line input (end line with : or \\, then blank line to execute)
  - Standard Python built-ins (help(), dir(), etc.)

Examples:
  >>> agent = BaseAgent(name="MyAgent")
  >>> await some_async_function()
  >>> for i in range(5):
  ...     print(i)
  ...
""")

    def _show_imports(self):
        """Show all pre-imported modules."""
        print("\nPre-imported modules and classes:")
        items = sorted([(name, type(obj).__name__) for name, obj in self.namespace.items() if not name.startswith("_")])

        if items:
            max_name_len = max(len(name) for name, _ in items)
            for name, type_name in items:
                print(f"  {name:<{max_name_len}}  ({type_name})")
        else:
            print("  None")
        print()

    def _execute(self, code: str):
        """Execute Python code in the REPL namespace.

        Args:
            code: Python code to execute
        """
        try:
            # Try to compile as eval first (for expressions)
            try:
                compiled = compile(code, "<stdin>", "eval")
                result = eval(compiled, self.namespace)

                # Handle async results
                if asyncio.iscoroutine(result):
                    result = asyncio.run(result)

                # Print non-None results
                if result is not None:
                    print(repr(result))
                    self.namespace["_"] = result

            except SyntaxError:
                # Fall back to exec (for statements)
                compiled = compile(code, "<stdin>", "exec")
                exec(compiled, self.namespace)

        except Exception as e:
            self._format_error(e)

    def _format_error(self, error: Exception):
        """Format and display error messages.

        Args:
            error: Exception to format
        """
        # Get traceback without REPL internal frames
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)

        # Filter out REPL internal frames
        filtered_lines = []
        skip_next = False
        for line in tb_lines:
            if "<stdin>" in line or "_execute" not in line:
                if not skip_next:
                    filtered_lines.append(line)
            else:
                skip_next = True

        # Print formatted error
        print("".join(filtered_lines), end="")
