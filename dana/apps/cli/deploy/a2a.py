import importlib
import os
from collections.abc import Callable
from pathlib import Path

from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill

from dana import py2na


def validate_agent_module(na_file_path: str, na_module):
    """
    Validate that the imported Dana module has the required agent structure.

    Args:
        na_file_path: Path to the .na file (for error messages)
        na_module: The imported Dana module to validate

    Returns:
        tuple: (agent_name, agent_description, solve_function) if valid, raises exception if invalid
    """
    try:
        # Find all agent classes in the module
        agents = []
        for attr in dir(na_module):
            attr_value = getattr(na_module, attr)
            if callable(attr_value):
                try:
                    agent = attr_value()
                    # Check if it has the required agent attributes
                    if hasattr(agent, "name") and hasattr(agent, "description") and hasattr(agent, "solve"):
                        agents.append(agent)
                except Exception:
                    continue

        if not agents:
            raise ValueError(f"No valid agents found in {na_file_path}")

        if len(agents) > 1:
            raise ValueError(f"Multiple agents found in {na_file_path}, only one agent is allowed")

        # Use the first agent found
        agent = agents[0]
        agent_name = str(agent.name)
        agent_description = str(agent.description)
        solve_function = agent.solve

        print("✅ Agent validation successful:")
        print(f"   Name: {agent_name}")
        print(f"   Description: {agent_description}")
        print("   Entry function: solve")

        return agent_name, agent_description, solve_function

    except Exception as e:
        raise ValueError(f"Agent validation failed for {na_file_path}: {e}")


def make_agent_class(agent_name: str, agent_description: str, entry_func: Callable):
    """Create an A2A agent class from a validated Dana .na file.

    Args:
        agent_name: Name of the agent
        agent_description: Description of the agent
        entry_func: Callable entry function for the agent
    """

    @agent(name=agent_name, description=agent_description, version="1.0.0")
    class NAFileA2AAgent(A2AServer):
        def __init__(self):
            super().__init__()
            self.agent_name = agent_name
            self.agent_description = agent_description
            self.entry_func = entry_func

        @skill(name="solve", description=f"Execute the {agent_name} agent with user query", tags=["dana", "agent", agent_name.lower()])
        def solve_query(self, query: str) -> str:
            """Execute the agent's solve function with the user query."""
            try:
                result = self.entry_func(query)
                return str(result)
            except Exception as e:
                return f"Error executing agent {self.agent_name}: {str(e)}"

        def handle_task(self, task):
            """Handle incoming A2A tasks."""
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""

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
    print(color_text(f"  {'Agent Name':<20} {'Description':<40}", f"{BOLD};{CYAN}"))
    print(color_text(f"  {agent_name:<20} {agent_description[:40]}", GREEN))
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
        py2na.enable_module_imports(search_paths=[file_dir])

        # Import the Dana module (without .na extension)
        module_name = Path(na_file_path).stem
        na_module = importlib.import_module(module_name)

        # Validate and create agent
        agent_name, agent_description, solve_function = validate_agent_module(na_file_path, na_module)
        AgentClass = make_agent_class(agent_name, agent_description, solve_function)
        agent_instance = AgentClass()

        # Print banner
        print_a2a_server_banner(host, port, agent_name, agent_description)

        # Run the A2A server
        run_server(agent_instance, host=host, port=port)

    except ImportError as e:
        print(f"❌ Failed to import Dana agent module {module_name}: {e}")
    except Exception as e:
        print(f"❌ Failed to deploy agent: {e}")
        print("Agent must have:")
        print("  - system:agent_name variable")
        print("  - system:agent_description variable")
        print("  - solve(query: str) -> str function")
    finally:
        py2na.close()
