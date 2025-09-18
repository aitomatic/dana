import importlib
import os
import sys
from pathlib import Path

# Add the project root to the path to avoid circular imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill

from dana import py2na

# Import Dana modules after setting up the path
try:
    from dana.core.lang.sandbox_context import SandboxContext

    # Create a sandbox context
    context = SandboxContext()
except ImportError as e:
    print(f"❌ Failed to import Dana modules: {e}")
    print("Make sure you're running this from the Dana project root with the correct environment")
    sys.exit(1)


def validate_agent_module(na_file_path: str, na_module):
    """
    Validate that the imported Dana module has the required agent structure.

    Args:
        na_file_path: Path to the .na file (for error messages)
        na_module: The imported Dana module to validate

    Returns:
        tuple: (agent_name, agent_instance) if valid, raises exception if invalid
    """
    try:
        # Find all agent instances in the module
        agents = []
        for attr in dir(na_module):
            attr_value = getattr(na_module, attr)

            # Skip built-in agents and system attributes
            if attr.startswith("_") or attr in ["BasicAgent", "DanaAgent"]:
                continue

            # Check if it's an agent instance (has name, description, and solve method)
            if (
                hasattr(attr_value, "name")
                and hasattr(attr_value, "description")
                and hasattr(attr_value, "solve")
                and callable(getattr(attr_value, "solve", None))
            ):
                agents.append(attr_value)

        if not agents:
            raise ValueError(f"No valid agents found in {na_file_path}")

        if len(agents) > 1:
            raise ValueError(f"Multiple agents found in {na_file_path}, only one agent is allowed")

        # Use the first agent found
        agent = agents[0]
        agent_name = str(agent.name)

        print("✅ Agent validation successful:")
        print(f"   Name: {agent_name}")
        print(f"   Description: {agent.description}")
        print("   Available methods: solve, reason, chat")

        return agent_name, agent

    except Exception as e:
        raise ValueError(f"Agent validation failed for {na_file_path}: {e}")


def make_agent_class(agent_name: str, agent_instance):
    """Create an A2A agent class from a validated Dana .na file.

    Args:
        agent_name: Name of the agent
        agent_instance: The agent instance with solve, reason, and chat methods
    """

    @agent(name=agent_name, description=agent_instance.description, version="1.0.0")
    class NAFileA2AAgent(A2AServer):
        def __init__(self):
            super().__init__()
            self.agent_name = agent_name
            self.agent_description = agent_instance.description
            self.agent_instance = agent_instance

        @skill(
            name="solve",
            description=f"Execute the {agent_name} agent's solve function with user query",
            tags=["dana", "agent", agent_name.lower(), "solve"],
        )
        def solve_query(self, query: str) -> str:
            """Execute the agent's solve function with the user query."""
            try:
                result = self.agent_instance.solve(problem=query, sandbox_context=context)
                print(f"🔍 Solve query: {query}")
                print(f"🔍 Solve result: {result}")
                return str(result)
            except Exception as e:
                return f"Error executing solve: {str(e)}"

        @skill(
            name="reason",
            description=f"Execute the {agent_name} agent's reason function with user query",
            tags=["dana", "agent", agent_name.lower(), "reason"],
        )
        def reason_query(self, query: str) -> str:
            """Execute the agent's reason function with the user query."""
            try:
                result = self.agent_instance.reason(premise=query, sandbox_context=context)
                print(f"🔍 Reason query: {query}")
                print(f"🔍 Reason result: {result}")
                return str(result)
            except Exception as e:
                return f"Error executing reason: {str(e)}"

        @skill(
            name="chat",
            description=f"Execute the {agent_name} agent's chat function with user query",
            tags=["dana", "agent", agent_name.lower(), "chat"],
        )
        def chat_query(self, query: str) -> str:
            """Execute the agent's chat function with the user query."""
            try:
                result = self.agent_instance.chat(message=query, sandbox_context=context)
                print(f"🔍 Chat query: {query}")
                print(f"🔍 Chat result: {result}")
                return str(result)
            except Exception as e:
                return f"Error executing chat: {str(e)}"

        def handle_task(self, task):
            """Handle incoming A2A tasks."""
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""

            # Default to solve method for task handling
            response = self.solve_query(text)
            task.artifacts = [{"parts": [{"type": "text", "text": response}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)

            print(f"Task completed: {task.status}")
            print(f"Task artifacts: {task.artifacts}")

            return task

    return NAFileA2AAgent


def color_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"


def print_a2a_server_banner(host, port, agent_name, agent_description):
    # Colors
    GREEN = "92"
    CYAN = "96"
    YELLOW = "93"
    BOLD = "1"
    # Banner
    print()
    print(color_text("🚀  ", YELLOW) + color_text("DANA A2A Server", f"{BOLD};{GREEN}"))
    print(color_text(" ──────────────────────────────", CYAN))
    print(color_text(" Host: ", CYAN) + color_text(f"{host}", BOLD))
    print(color_text(" Port: ", CYAN) + color_text(f"{port}", BOLD))
    print()
    print(color_text("  Deployed Agent", YELLOW))
    print(color_text("  ─────────────", CYAN))
    print(color_text(f"  Agent Name: {agent_name}", GREEN))
    print(color_text(f"  Description: {agent_description}", GREEN))
    print()
    print(color_text("  Available Skills:", YELLOW))
    print(color_text("  ─────────────────", CYAN))
    print(color_text("  solve  - Execute agent's solve function", GREEN))
    print(color_text("  reason - Execute agent's reason function", GREEN))
    print(color_text("  chat   - Execute agent's chat function", GREEN))
    print()
    print(color_text("Starting A2A server...", f"{BOLD};{CYAN}"))
    print()


def deploy_dana_agents_thru_a2a(na_file_path, host, port):
    """
    Setup and deploy a .na file as an A2A agent endpoint.

    Args:
        na_file_path (str): Path to the .na file to deploy
        host (str): Host address to bind the server to
        port (int): Port number to deploy on
    """
    if not os.path.exists(na_file_path) or not na_file_path.endswith(".na"):
        print("Invalid .na file path!")
        return

    try:
        # Add the directory containing the .na file to search paths
        file_dir = str(Path(na_file_path).parent)
        print(f"Adding {file_dir} to search paths")
        py2na.enable_module_imports(search_paths=[file_dir])

        # Import the Dana module (without .na extension)
        module_name = Path(na_file_path).stem
        na_module = importlib.import_module(module_name)

        # Validate and create agent
        agent_name, agent_instance = validate_agent_module(na_file_path, na_module)
        AgentClass = make_agent_class(agent_name, agent_instance)
        agent_a2a_instance = AgentClass()

        # Print banner
        print_a2a_server_banner(host, port, agent_name, agent_instance.description)

        # Run the A2A server
        run_server(agent_a2a_instance, host=host, port=port)

    except ImportError as e:
        print(f"❌ Failed to import Dana agent module {module_name}: {e}")
    except Exception as e:
        print(f"❌ Failed to deploy agent: {e}")
        print("Agent must have:")
        print("  - A valid agent instance")
        print("  - solve(query: str) -> str function")
        print("  - reason(query: str) -> str function")
        print("  - chat(query: str) -> str function")
    finally:
        py2na.close()
