from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..services import get_agent
from .. import db
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.lang.dana_sandbox import DanaSandbox
from pathlib import Path
import re

router = APIRouter(prefix="/agent-test", tags=["agent-test"])

class AgentTestRequest(BaseModel):
    """Request model for agent testing"""
    agent_code: str
    message: str
    agent_name: Optional[str] = "Test Agent"
    agent_description: Optional[str] = "A test agent"
    context: Optional[Dict[str, Any]] = None

class AgentTestResponse(BaseModel):
    """Response model for agent testing"""
    success: bool
    agent_response: str
    error: Optional[str] = None

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

@router.post("/", response_model=AgentTestResponse)
async def test_agent(request: AgentTestRequest):
    """
    Test an agent with code and message without creating database records
    
    This endpoint allows you to test agent behavior by providing the agent code
    and a message. It executes the agent code in a sandbox environment and
    returns the response without creating any database records.
    
    Args:
        request: AgentTestRequest containing agent code, message, and optional metadata
        
    Returns:
        AgentTestResponse with agent response or error
    """
    try:
        agent_code = request.agent_code.strip()
        message = request.message.strip()
        
        if not agent_code:
            raise HTTPException(status_code=400, detail="Agent code is required")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        print(f"Testing agent with message: '{message}'")
        print(f"Using agent code: {agent_code[:200]}...")
        
        # Parse agent name from Dana code
        agent_name_match = re.search(r'^\s*agent\s+([A-Za-z_][A-Za-z0-9_]*)\s*:', agent_code, re.MULTILINE)
        if not agent_name_match:
            raise HTTPException(status_code=400, detail="Could not find agent name in Dana code. Please ensure your agent code starts with 'agent AgentName:'")
        
        agent_name = agent_name_match.group(1)
        instance_var = agent_name[0].lower() + agent_name[1:]  # e.g., WeatherAgent -> weatherAgent
        
        # Append code to instantiate and solve using method call
        appended_code = f"\n{instance_var} = {agent_name}()\nresponse = {instance_var}.solve(\"{message.replace('\\', '\\\\').replace('"', '\\"')}\")\nprint(response)\n"
        dana_code_to_run = agent_code + appended_code
        
        # Create a temporary file for the Dana code
        temp_folder = Path("/tmp/dana_test")
        temp_folder.mkdir(parents=True, exist_ok=True)
        full_path = temp_folder / f"test_agent_{hash(agent_code) % 10000}.na"
        
        print(f"Dana code to run: {dana_code_to_run}")
        
        # Write the Dana code to the temporary file
        with open(full_path, "w") as f:
            f.write(dana_code_to_run)
        
        # Execute the Dana code using DanaSandbox
        sandbox_context = SandboxContext()
        
        # Execute the code
        DanaSandbox.quick_run(file_path=full_path, context=sandbox_context)
        
        print("--------------------------------")
        print(sandbox_context.get_state())
        
        state = sandbox_context.get_state()
        response_text = state.get("local", {}).get("response", "")
        
        if not response_text:
            response_text = "Agent executed successfully but returned no response."
        
        # Clean up temporary file
        try:
            full_path.unlink()
        except Exception as cleanup_error:
            print(f"Warning: Failed to cleanup temporary file: {cleanup_error}")
        
        return AgentTestResponse(
            success=True,
            agent_response=response_text,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error testing agent: {str(e)}"
        print(error_msg)
        return AgentTestResponse(
            success=False,
            agent_response="",
            error=error_msg
        ) 