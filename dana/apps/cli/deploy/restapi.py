#!/usr/bin/env python3
"""
Dana Agent REST API Server
Deploys a Dana agent as a REST API using FastAPI.
"""

import importlib
import os
import sys
from pathlib import Path

# Add the project root to the path to avoid circular imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as e:
    print(f"❌ Missing required dependencies: {e}")
    print("Please install: pip install fastapi uvicorn")
    sys.exit(1)

# Import Dana modules after setting up the path
try:
    from dana import py2na
    from dana.core.lang.sandbox_context import SandboxContext

    # Create a sandbox context
    context = SandboxContext()
except ImportError as e:
    print(f"❌ Failed to import Dana modules: {e}")
    print("Make sure you're running this from the Dana project root with the correct environment")
    sys.exit(1)


class AgentRequest(BaseModel):
    query: str


class AgentResponse(BaseModel):
    result: str
    agent_name: str
    method: str


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


def create_fastapi_app(na_file_path: str, host: str = "0.0.0.0", port: int = 8000):
    """
    Create a FastAPI app for deploying a Dana agent.

    Args:
        na_file_path: Path to the .na file to deploy
        host: Host address to bind the server to
        port: Port number to deploy on

    Returns:
        FastAPI app instance
    """
    if not os.path.exists(na_file_path) or not na_file_path.endswith(".na"):
        raise ValueError("Invalid .na file path!")

    try:
        # Add the directory containing the .na file to search paths
        file_dir = str(Path(na_file_path).parent)
        print(f"Adding {file_dir} to search paths")
        py2na.enable_module_imports(search_paths=[file_dir])

        # Import the Dana module (without .na extension)
        module_name = Path(na_file_path).stem
        na_module = importlib.import_module(module_name)

        # Validate and get agent
        agent_name, agent_instance = validate_agent_module(na_file_path, na_module)

        # Create FastAPI app
        app = FastAPI(title=f"Dana Agent API - {agent_name}", description=f"REST API for Dana agent: {agent_name}", version="1.0.0")

        @app.get("/")
        async def root():
            return {
                "agent_name": agent_name,
                "description": agent_instance.description,
                "endpoints": ["/solve", "/reason", "/chat"],
                "status": "ready",
            }

        @app.post("/solve", response_model=AgentResponse)
        async def solve_problem(request: AgentRequest):
            """Execute the agent's solve function with the user query."""
            try:
                result = agent_instance.solve(problem=request.query, sandbox_context=context)
                return AgentResponse(result=str(result), agent_name=agent_name, method="solve")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error executing solve: {str(e)}")

        @app.post("/reason", response_model=AgentResponse)
        async def reason_about(request: AgentRequest):
            """Execute the agent's reason function with the user query."""
            try:
                result = agent_instance.reason(premise=request.query, sandbox_context=context)
                return AgentResponse(result=str(result), agent_name=agent_name, method="reason")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error executing reason: {str(e)}")

        @app.post("/chat", response_model=AgentResponse)
        async def chat_with(request: AgentRequest):
            """Execute the agent's chat function with the user query."""
            try:
                result = agent_instance.chat(message=request.query, sandbox_context=context)
                return AgentResponse(result=str(result), agent_name=agent_name, method="chat")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error executing chat: {str(e)}")

        return app, agent_name

    except ImportError as e:
        raise ValueError(f"Failed to import Dana agent module {module_name}: {e}")
    except Exception as e:
        raise ValueError(f"FastAPI app creation failed for {na_file_path}: {e}")


def print_rest_api_banner(host: str, port: int, agent_name: str):
    """Print a banner with server information."""
    print()
    print("🚀  Dana Agent REST API Server")
    print(" ──────────────────────────────")
    print(f" Host: {host}")
    print(f" Port: {port}")
    print()
    print("  Deployed Agent")
    print("  ─────────────")
    print(f"  Agent Name: {agent_name}")
    print()
    print("  Available Endpoints:")
    print("  ───────────────────")
    print("  POST /solve  - Execute agent's solve function")
    print("  POST /reason - Execute agent's reason function")
    print("  POST /chat   - Execute agent's chat function")
    print("  GET  /       - Server status and info")
    print()
    print("Starting REST API server...")
    print()


def deploy_dana_agent_rest_api(na_file_path: str, host: str = "0.0.0.0", port: int = 8000):
    """
    Deploy a Dana agent as a REST API server.

    Args:
        na_file_path: Path to the .na file to deploy
        host: Host address to bind the server to
        port: Port number to deploy on
    """
    try:
        # Create FastAPI app
        app, agent_name = create_fastapi_app(na_file_path, host, port)

        # Print banner
        print_rest_api_banner(host, port, agent_name)

        # Run the server
        uvicorn.run(app, host=host, port=port)

    except Exception as e:
        print(f"❌ Failed to deploy agent: {e}")
        print("Agent must have:")
        print("  - A valid agent instance")
        print("  - solve(query: str) -> str function")
        print("  - reason(query: str) -> str function")
        print("  - chat(query: str) -> str function")
    finally:
        py2na.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restapi.py <na_file_path> [host] [port]")
        print("Example: python restapi.py simple_agent.na 0.0.0.0 8000")
        sys.exit(1)

    na_file = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000

    deploy_dana_agent_rest_api(na_file, host, port)
