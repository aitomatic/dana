import re
from pathlib import Path
from typing import Any
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.sandbox_context import SandboxContext

from .. import db

router = APIRouter(prefix="/agent-test", tags=["agent-test"])


class AgentTestRequest(BaseModel):
    """Request model for agent testing"""

    agent_code: str
    message: str
    agent_name: str | None = "Test Agent"
    agent_description: str | None = "A test agent"
    context: dict[str, Any] | None = None
    folder_path: str | None = None


class AgentTestResponse(BaseModel):
    """Response model for agent testing"""

    success: bool
    agent_response: str
    error: str | None = None


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
        agent_name = request.agent_name

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        print(f"Testing agent with message: '{message}'")
        print(f"Using agent code: {agent_code[:200]}...")

        # If folder_path is provided and main.na exists, run that file
        if request.folder_path:
            abs_folder_path = str(Path(request.folder_path).resolve())
            main_na_path = Path(abs_folder_path) / "main.na"
            if main_na_path.exists():
                print(f"Running main.na from folder: {main_na_path}")
                
                # Create temporary file in the same folder
                import tempfile
                import uuid
                temp_filename = f"temp_main_{uuid.uuid4().hex[:8]}.na"
                temp_file_path = Path(abs_folder_path) / temp_filename
                
                try:
                    # Read the original main.na content
                    with open(main_na_path, 'r', encoding='utf-8') as f:
                        original_content = f.read()
                    
                    # Add the response line at the end
                    escaped_message = message.replace("\\", "\\\\").replace('"', '\\"')
                    additional_code = f'\n\n# Test execution\nuser_query = "{escaped_message}"\nresponse = this_agent.solve(user_query)\nprint(response)\n'
                    temp_content = original_content + additional_code
                    
                    # Write to temporary file
                    with open(temp_file_path, 'w', encoding='utf-8') as f:
                        f.write(temp_content)
                    
                    print(f"Created temporary file: {temp_file_path}")
                    
                    # Execute the temporary file
                    old_danapath = os.environ.get("DANAPATH")
                    os.environ["DANAPATH"] = abs_folder_path
                    try:
                        print("os DANAPATH", os.environ.get("DANAPATH"))
                        result = DanaSandbox.quick_run(file_path=temp_file_path)
                        
                        # Get the response from the execution
                        if result.success and result.output:
                            response_text = result.output.strip()
                        else:
                            response_text = result.error if result.error else "Agent executed but returned no response."
                            
                    finally:
                        if old_danapath is not None:
                            os.environ["DANAPATH"] = old_danapath
                        else:
                            os.environ.pop("DANAPATH", None)
                    
                finally:
                    # Clean up temporary file
                    try:
                        if temp_file_path.exists():
                            temp_file_path.unlink()
                            print(f"Cleaned up temporary file: {temp_file_path}")
                    except Exception as cleanup_error:
                        print(f"Warning: Failed to cleanup temporary file {temp_file_path}: {cleanup_error}")
                
                print("--------------------------------")
                print(f"Agent response: {response_text}")
                print("--------------------------------")
                
                return AgentTestResponse(success=True, agent_response=response_text, error=None)
        # Otherwise, fall back to the current behavior
        instance_var = agent_name[0].lower() + agent_name[1:]
        appended_code = f'\n{instance_var} = {agent_name}()\nresponse = {instance_var}.solve("{message.replace("\\", "\\\\").replace('"', '\\"')}")\nprint(response)\n'
        dana_code_to_run = agent_code + appended_code
        temp_folder = Path("/tmp/dana_test")
        temp_folder.mkdir(parents=True, exist_ok=True)
        full_path = temp_folder / f"test_agent_{hash(agent_code) % 10000}.na"
        print(f"Dana code to run: {dana_code_to_run}")
        with open(full_path, "w") as f:
            f.write(dana_code_to_run)
        old_danapath = os.environ.get("DANAPATH")
        if request.folder_path:
            abs_folder_path = str(Path(request.folder_path).resolve())
            os.environ["DANAPATH"] = abs_folder_path
        print("--------------------------------")
        print(f"DANAPATH: {os.environ.get('DANAPATH')}")
        print("--------------------------------")
        try:
            sandbox_context = SandboxContext()
            DanaSandbox.quick_run(file_path=full_path, context=sandbox_context)
        finally:
            if request.folder_path:
                if old_danapath is not None:
                    os.environ["DANAPATH"] = old_danapath
                else:
                    os.environ.pop("DANAPATH", None)
        print("--------------------------------")
        print(sandbox_context.get_state())
        state = sandbox_context.get_state()
        response_text = state.get("local", {}).get("response", "")
        if not response_text:
            response_text = "Agent executed successfully but returned no response."
        try:
            full_path.unlink()
        except Exception as cleanup_error:
            print(f"Warning: Failed to cleanup temporary file: {cleanup_error}")
        return AgentTestResponse(success=True, agent_response=response_text, error=None)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error testing agent: {str(e)}"
        print(error_msg)
        return AgentTestResponse(success=False, agent_response="", error=error_msg)
