import importlib
import os
from pathlib import Path

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
        # Validate required components
        if not hasattr(na_module, "agent_name"):
            raise ValueError(f"Agent file {na_file_path} missing required 'system:agent_name' variable")

        if not hasattr(na_module, "agent_description"):
            raise ValueError(f"Agent file {na_file_path} missing required 'system:agent_description' variable")

        if not hasattr(na_module, "solve"):
            raise ValueError(f"Agent file {na_file_path} missing required 'solve(query: str) -> str' function")

        if not callable(na_module.solve):
            raise ValueError(f"Agent file {na_file_path} 'solve' is not a callable function")

        agent_name = str(na_module.agent_name)
        agent_description = str(na_module.agent_description)
        solve_function = na_module.solve

        print("✅ Agent validation successful:")
        print(f"   Name: {agent_name}")
        print(f"   Description: {agent_description}")
        print("   Entry function: solve")

        return agent_name, agent_description, solve_function

    except Exception as e:
        raise ValueError(f"Agent validation failed for {na_file_path}: {e}")


def create_mcp_server_for_file(na_file_path):
    """Create an MCP server for a validated Dana .na file."""
    from mcp.server.fastmcp import FastMCP

    try:
        # Add the directory containing the .na file to search paths
        file_dir = str(Path(na_file_path).parent)
        py2na.enable_module_imports(search_paths=[file_dir])

        # Import the Dana module (without .na extension)
        module_name = Path(na_file_path).stem
        na_module = importlib.import_module(module_name)

        # Validate and get agent components
        agent_name, agent_description, solve_function = validate_agent_module(na_file_path, na_module)

        # Create MCP server with agent name
        mcp = FastMCP(name=agent_name, stateless_http=True)

        @mcp.tool(description=f"{agent_description}")
        def solve(query: str) -> str:
            """Execute the agent's solve function with the user query."""
            try:
                result = solve_function(query)
                return str(result)
            except Exception as e:
                return f"Error executing agent {agent_name}: {str(e)}"

        return mcp, agent_name, agent_description

    except ImportError as e:
        raise ValueError(f"Failed to import Dana agent module {module_name}: {e}")
    except Exception as e:
        raise ValueError(f"MCP server creation failed for {na_file_path}: {e}")


def color_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"


def print_mcp_server_banner(host, port, agent_name):
    # Colors
    GREEN = "92"
    CYAN = "96"
    YELLOW = "93"
    BOLD = "1"
    # Banner
    print()
    print(color_text("🚀  ", YELLOW) + color_text("DANA MCP Server", f"{BOLD};{GREEN}"))
    print(color_text(" ──────────────────────────────", CYAN))
    print(color_text(" Host: ", CYAN) + color_text(f"{host}", BOLD))
    print(color_text(" Port: ", CYAN) + color_text(f"{port}", BOLD))
    print()
    print(color_text("  Agent Endpoint", YELLOW))
    print(color_text("  ─────────────", CYAN))
    print(color_text(f"  {'Agent Name':<20} {'Endpoint Path':<30}", f"{BOLD};{CYAN}"))
    print(color_text(f"  {agent_name:<20} /{agent_name.lower()}/mcp", GREEN))
    print()
    print(color_text("Starting MCP server...", f"{BOLD};{CYAN}"))
    print()


def deploy_dana_agents_thru_mcp(na_file_path, host, port):
    """
    Setup and deploy a single .na file as MCP agent endpoint.

    Args:
        na_file_path (str): Path to the .na file to deploy
        host (str): Host address to bind the server to
        port (int): Port number to deploy on
    """
    import contextlib

    import uvicorn
    from fastapi import FastAPI

    # Validate file exists and has .na extension
    if not os.path.exists(na_file_path) or not na_file_path.endswith(".na"):
        print("Invalid .na file path!")
        return

    try:
        # Create MCP server for the file
        mcp, agent_name, agent_description = create_mcp_server_for_file(na_file_path)
        print(f"✅ Created MCP server for agent: {agent_name}")
    except ValueError as e:
        print(f"❌ Failed to create MCP server: {e}")
        print("Agent must have:")
        print("  - system:agent_name variable")
        print("  - system:agent_description variable")
        print("  - solve(query: str) -> str function")
        return

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(lifespan=lifespan)
    app.mount(f"/{agent_name.lower()}", mcp.streamable_http_app())

    print_mcp_server_banner(host, port, agent_name)

    try:
        uvicorn.run(app, host=host, port=port)
    finally:
        py2na.close()
