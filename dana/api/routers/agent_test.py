from pathlib import Path
from typing import Any
import os
import logging
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.api.utils.sandbox_context_with_notifier import SandboxContextWithNotifier
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-test", tags=["agent-test"])


# WebSocket Connection Manager for real-time variable updates
class VariableUpdateManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket_id] = websocket

    def disconnect(self, websocket_id: str):
        if websocket_id in self.active_connections:
            del self.active_connections[websocket_id]

    async def send_variable_update(
        self,
        websocket_id: str,
        scope: str,
        var_name: str,
        old_value: Any,
        new_value: Any,
    ):
        if websocket_id in self.active_connections:
            websocket = self.active_connections[websocket_id]
            try:
                message = {
                    "type": "variable_change",
                    "scope": scope,
                    "variable": var_name,
                    "old_value": str(old_value) if old_value is not None else None,
                    "new_value": str(new_value) if new_value is not None else None,
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send variable update via WebSocket: {e}")
                # Remove disconnected WebSocket
                self.disconnect(websocket_id)


variable_update_manager = VariableUpdateManager()


def create_websocket_notifier(websocket_id: str | None = None):
    """Create a variable change notifier that sends updates via WebSocket"""

    async def variable_change_notifier(scope: str, var_name: str, old_value: Any, new_value: Any) -> None:
        if old_value != new_value:  # Only notify on actual changes
            # Send via WebSocket if connection exists
            if websocket_id:
                await variable_update_manager.send_variable_update(websocket_id, scope, var_name, old_value, new_value)

    return variable_change_notifier


class AgentTestRequest(BaseModel):
    """Request model for agent testing"""

    agent_code: str
    message: str
    agent_name: str | None = "Georgia"
    agent_description: str | None = "A test agent"
    context: dict[str, Any] | None = None
    folder_path: str | None = None
    websocket_id: str | None = None  # Optional WebSocket ID for real-time updates


class AgentTestResponse(BaseModel):
    """Response model for agent testing"""

    success: bool
    agent_response: str
    error: str | None = None


async def _execute_folder_based_agent(request: AgentTestRequest, folder_path: str) -> AgentTestResponse:
    """Execute agent using folder-based approach with main.na file."""
    abs_folder_path = str(Path(folder_path).resolve())
    main_na_path = Path(abs_folder_path) / "main.na"

    if not main_na_path.exists():
        logger.info(f"main.na not found at {main_na_path}, using LLM fallback")
        print(f"main.na not found at {main_na_path}, using LLM fallback")

        llm_response = await _llm_fallback(request.agent_name, request.agent_description, request.message)

        print("--------------------------------")
        print(f"LLM fallback response: {llm_response}")
        print("--------------------------------")

        return AgentTestResponse(success=True, agent_response=llm_response, error=None)

    print(f"Running main.na from folder: {main_na_path}")

    # Create temporary file in the same folder
    import uuid

    temp_filename = f"temp_main_{uuid.uuid4().hex[:8]}.na"
    temp_file_path = Path(abs_folder_path) / temp_filename

    old_danapath = os.environ.get("DANAPATH")
    response_text = None

    try:
        # Read the original main.na content
        with open(main_na_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Add the response line at the end
        escaped_message = request.message.replace("\\", "\\\\").replace('"', '\\"')
        additional_code = (
            f'\n\n# Test execution\nuser_query = "{escaped_message}"\nresponse = this_agent.solve(user_query)\nprint(response)\n'
        )
        temp_content = original_content + additional_code

        # Write to temporary file
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(temp_content)

        print(f"Created temporary file: {temp_file_path}")

        # Execute the temporary file
        os.environ["DANAPATH"] = abs_folder_path
        print("os DANAPATH", os.environ.get("DANAPATH"))

        # Create a WebSocket-enabled notifier
        notifier = create_websocket_notifier(request.websocket_id)

        # Run all potentially blocking operations in a separate thread
        with ThreadPoolExecutor(max_workers=1) as executor:

            def run_agent_test():
                # Create a completely fresh sandbox context for each run
                sandbox_context = SandboxContextWithNotifier(notifier=notifier)

                # Set system variables for this specific run
                sandbox_context.set("system:user_id", str(request.context.get("user_id", "Lam")))
                sandbox_context.set("system:session_id", f"test-agent-creation-{uuid.uuid4().hex[:8]}")
                sandbox_context.set("system:agent_instance_id", str(Path(folder_path).stem))

                try:
                    result = DanaSandbox.quick_run(file_path=temp_file_path, context=sandbox_context)

                    if hasattr(result, "error"):
                        logger.error(f"Error: {result.error}")
                        logger.exception(result.error)

                    state = sandbox_context.get_state()
                    response_text = state.get("local", {}).get("response", "")

                    if not isinstance(response_text, str):
                        from dana.core.concurrency.eager_promise import EagerPromise

                        if isinstance(response_text, EagerPromise):
                            response_text = response_text._result

                    if not response_text and result.success and result.output:
                        response_text = result.output.strip()

                    return response_text
                except Exception as e:
                    logger.error(f"Error: {e}")
                    logger.exception(e)
                    return None

                finally:
                    # Clean up the context to prevent state leakage
                    sandbox_context.shutdown()

                    # Clear global registries to prevent struct/module conflicts between runs
                    from dana.core.lang.interpreter.struct_system import StructTypeRegistry
                    from dana.core.runtime.modules.core import reset_module_system

                    StructTypeRegistry.clear()
                    reset_module_system()

            result = await asyncio.get_event_loop().run_in_executor(executor, run_agent_test)

        print("--------------------------------")
        print(f"Result: {result}")
        print("--------------------------------")

        print("--------------------------------")
        print(f"Response text: {response_text}")
        print("--------------------------------")

        if response_text or result:
            return AgentTestResponse(success=True, agent_response=response_text or result, error=None)
        else:
            # Multi-file execution failed, use LLM fallback
            logger.warning(f"Multi-file agent execution failed: {result.error}, using LLM fallback")
            print(f"Multi-file agent execution failed: {result.error}, using LLM fallback")

            llm_response = await _llm_fallback(request.agent_name, request.agent_description, request.message)

            return AgentTestResponse(success=True, agent_response=llm_response, error=None)

    except Exception as e:
        # Exception during multi-file execution, use LLM fallback
        logger.exception(e)
        logger.warning(f"Exception during multi-file execution: {e}, using LLM fallback")
        print(f"Exception during multi-file execution: {e}, using LLM fallback")

        llm_response = await _llm_fallback(request.agent_name, request.agent_description, request.message)

        return AgentTestResponse(success=True, agent_response=llm_response, error=None)
    finally:
        # Restore environment
        if old_danapath is not None:
            os.environ["DANAPATH"] = old_danapath
        else:
            os.environ.pop("DANAPATH", None)

        # Clean up temporary file
        try:
            if temp_file_path.exists():
                temp_file_path.unlink()
                print(f"Cleaned up temporary file: {temp_file_path}")
        except Exception as cleanup_error:
            print(f"Warning: Failed to cleanup temporary file {temp_file_path}: {cleanup_error}")


async def _llm_fallback(agent_name: str, agent_description: str, message: str) -> str:
    """
    Fallback to LLM when agent execution fails or no Dana code available.

    Args:
        agent_name: Name of the agent
        agent_description: Description of the agent
        message: User message to process

    Returns:
        Agent response from LLM
    """
    try:
        logger.info(f"Using LLM fallback for agent '{agent_name}' with message: {message}")

        # Create LLM resource
        llm = LLMResource(
            name="agent_test_fallback_llm",
            description="LLM fallback for agent testing when Dana code is not available",
        )
        await llm.initialize()

        # Check if LLM is available
        if not hasattr(llm, "_is_available") or not llm._is_available:
            logger.warning("LLM resource is not available for fallback")
            return "I'm sorry, I'm currently unavailable. Please try again later or ensure the training code is generated."

        # Build system prompt based on agent description
        system_prompt = f"""You are {agent_name}, trained by Dana to be a helpful assistant.

{agent_description}

Please respond to the user's message in character, being helpful and following your description. Keep your response concise and relevant to the user's query."""

        # Create request
        request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
            }
        )

        # Query LLM
        response = await llm.query(request)
        if response.success:
            # Extract assistant message from response
            response_content = response.content
            if isinstance(response_content, dict):
                choices = response_content.get("choices", [])
                if choices:
                    assistant_message = choices[0].get("message", {}).get("content", "")
                    if assistant_message:
                        return assistant_message

                # Try alternative response formats
                if "content" in response_content:
                    return response_content["content"]
                elif "text" in response_content:
                    return response_content["text"]
            elif isinstance(response_content, str):
                return response_content

            return "I processed your request but couldn't generate a proper response."
        else:
            logger.error(f"LLM fallback failed: {response.error}")
            return f"I'm experiencing technical difficulties: {response.error}"

    except Exception as e:
        logger.error(f"Error in LLM fallback: {e}")
        return f"I encountered an error while processing your request: {str(e)}"


async def _execute_code_based_agent(request: AgentTestRequest) -> AgentTestResponse:
    """Execute agent using provided code string."""
    agent_code = request.agent_code.strip()
    message = request.message.strip()

    # Check if agent_code is empty or minimal
    if not agent_code or len(agent_code.strip()) < 50:
        logger.info("No substantial agent code provided, using LLM fallback")
        print("No substantial agent code provided, using LLM fallback")

        llm_response = await _llm_fallback(request.agent_name, request.agent_description, message)

        print("--------------------------------")
        print(f"LLM fallback response: {llm_response}")
        print("--------------------------------")

        return AgentTestResponse(success=True, agent_response=llm_response, error=None)

    # Create Dana code to run
    instance_var = request.agent_name[0].lower() + request.agent_name[1:]
    appended_code = f'\n{instance_var} = {request.agent_name}()\nresponse = {instance_var}.solve("{message.replace("\\", "\\\\").replace('"', '\\"')}")\nprint(response)\n'
    dana_code_to_run = agent_code + appended_code

    # Create temporary file
    temp_folder = Path("/tmp/dana_test")
    temp_folder.mkdir(parents=True, exist_ok=True)
    full_path = temp_folder / f"test_agent_{hash(agent_code) % 10000}.na"

    print(f"Dana code to run: {dana_code_to_run}")
    with open(full_path, "w") as f:
        f.write(dana_code_to_run)

    # Set up environment
    old_danapath = os.environ.get("DANAPATH")
    if request.folder_path:
        abs_folder_path = str(Path(request.folder_path).resolve())
        os.environ["DANAPATH"] = abs_folder_path

    print("--------------------------------")
    print(f"DANAPATH: {os.environ.get('DANAPATH')}")
    print("--------------------------------")

    try:
        # Create a WebSocket-enabled notifier
        notifier = create_websocket_notifier(request.websocket_id)

        # Run the blocking DanaSandbox.quick_run in a thread pool to avoid blocking the API
        loop = asyncio.get_event_loop()

        def run_code_based_agent():
            # Create a completely fresh sandbox context for each run
            sandbox_context = SandboxContextWithNotifier(notifier=notifier)

            # Set system variables for this specific run
            sandbox_context.set("system:user_id", str(request.context.get("user_id", "Lam") if request.context else "Lam"))
            sandbox_context.set("system:session_id", f"test-agent-creation-{uuid.uuid4().hex[:8]}")
            sandbox_context.set("system:agent_instance_id", request.agent_name or "Georgia")

            try:
                return DanaSandbox.quick_run(
                    file_path=full_path,
                    context=sandbox_context,
                )
            finally:
                # Clean up the context to prevent state leakage
                sandbox_context.shutdown()

                # Clear global registries to prevent struct/module conflicts between runs
                from dana.core.lang.interpreter.struct_system import StructTypeRegistry
                from dana.core.runtime.modules.core import reset_module_system

                StructTypeRegistry.clear()
                reset_module_system()

        result = await loop.run_in_executor(None, run_code_based_agent)

        if not result.success:
            # Dana execution failed, use LLM fallback
            logger.warning(f"Dana execution failed: {result.error}, using LLM fallback")
            print(f"Dana execution failed: {result.error}, using LLM fallback")

            llm_response = await _llm_fallback(request.agent_name, request.agent_description, message)

            print("--------------------------------")
            print(f"LLM fallback response: {llm_response}")
            print("--------------------------------")

            return AgentTestResponse(success=True, agent_response=llm_response, error=None)

        # Get response from result output
        response_text = result.output.strip() if result.output else "Agent executed successfully but returned no response."

        return AgentTestResponse(success=True, agent_response=response_text, error=None)

    except Exception as e:
        # Exception during execution, use LLM fallback
        logger.warning(f"Exception during Dana execution: {e}, using LLM fallback")
        print(f"Exception during Dana execution: {e}, using LLM fallback")

        llm_response = await _llm_fallback(request.agent_name, request.agent_description, message)

        print("--------------------------------")
        print(f"LLM fallback response: {llm_response}")
        print("--------------------------------")

        return AgentTestResponse(success=True, agent_response=llm_response, error=None)
    finally:
        # Restore environment
        if request.folder_path:
            if old_danapath is not None:
                os.environ["DANAPATH"] = old_danapath
            else:
                os.environ.pop("DANAPATH", None)

        # Clean up temporary file
        try:
            full_path.unlink()
        except Exception as cleanup_error:
            print(f"Warning: Failed to cleanup temporary file: {cleanup_error}")


async def _validate_request(request: AgentTestRequest) -> str | None:
    """Validate the test request and return error message if invalid."""
    message = request.message.strip()
    if not message:
        return "Message is required"
    return None


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
        # Validate request
        validation_error = await _validate_request(request)
        if validation_error:
            raise HTTPException(status_code=400, detail=validation_error)

        print(f"Testing agent with message: '{request.message.strip()}'")
        print(f"Using agent code: {request.agent_code[:200]}...")

        # If folder_path is provided, use folder-based execution
        if request.folder_path:
            return await _execute_folder_based_agent(request, request.folder_path)

        # Otherwise, use code-based execution
        return await _execute_code_based_agent(request)

    except HTTPException:
        raise
    except Exception as e:
        # Final fallback: if everything else fails, try LLM fallback
        logger.error(f"Unexpected error in agent test: {e}, attempting LLM fallback")
        try:
            llm_response = await _llm_fallback(request.agent_name, request.agent_description, request.message)
            print("--------------------------------")
            print(f"Final LLM fallback response: {llm_response}")
            print("--------------------------------")
            return AgentTestResponse(success=True, agent_response=llm_response, error=None)
        except Exception as llm_error:
            error_msg = f"Error testing agent: {str(e)}. LLM fallback also failed: {str(llm_error)}"
            print(error_msg)
            return AgentTestResponse(success=False, agent_response="", error=error_msg)


@router.websocket("/ws/{websocket_id}")
async def websocket_variable_updates(websocket: WebSocket, websocket_id: str):
    """
    WebSocket endpoint for receiving real-time variable updates during agent execution.

    Args:
        websocket: The WebSocket connection
        websocket_id: Unique identifier for this WebSocket connection
    """
    await variable_update_manager.connect(websocket_id, websocket)
    try:
        while True:
            # Keep the connection alive and listen for client messages
            data = await websocket.receive_text()
            # Echo back for debugging (optional)
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "echo",
                        "message": f"Connected to variable updates for ID: {websocket_id}",
                        "data": data,
                    }
                )
            )
    except WebSocketDisconnect:
        variable_update_manager.disconnect(websocket_id)
    except Exception as e:
        logger.error(f"WebSocket error for {websocket_id}: {e}")
        variable_update_manager.disconnect(websocket_id)
