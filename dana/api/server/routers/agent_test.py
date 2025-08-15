import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.types import BaseRequest
from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.sandbox_context import SandboxContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-test", tags=["agent-test"])


class AgentTestRequest(BaseModel):
    """Request model for agent testing"""

    agent_code: str
    message: str
    agent_name: str | None = "Georgia"
    agent_description: str | None = "A test agent"
    context: dict[str, Any] | None = None
    folder_path: str | None = None


class AgentTestResponse(BaseModel):
    """Response model for agent testing"""

    success: bool
    agent_response: str
    error: str | None = None


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
        llm = LegacyLLMResource(
            name="agent_test_fallback_llm", description="LLM fallback for agent testing when Dana code is not available"
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
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
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

        # If folder_path is provided, check if main.na exists
        if request.folder_path:
            abs_folder_path = str(Path(request.folder_path).resolve())
            main_na_path = Path(abs_folder_path) / "main.na"
            if main_na_path.exists():
                print(f"Running main.na from folder: {main_na_path}")

                # Create temporary file in the same folder
                import uuid

                temp_filename = f"temp_main_{uuid.uuid4().hex[:8]}.na"
                temp_file_path = Path(abs_folder_path) / temp_filename

                try:
                    # Read the original main.na content
                    with open(main_na_path, encoding="utf-8") as f:
                        original_content = f.read()

                    # Add the response line at the end
                    escaped_message = message.replace("\\", "\\\\").replace('"', '\\"')
                    additional_code = f'\n\n# Test execution\nuser_query = "{escaped_message}"\nresponse = this_agent.solve(user_query)\nprint(response)\n'
                    temp_content = original_content + additional_code

                    # Write to temporary file
                    with open(temp_file_path, "w", encoding="utf-8") as f:
                        f.write(temp_content)

                    print(f"Created temporary file: {temp_file_path}")

                    # Execute the temporary file
                    old_danapath = os.environ.get("DANAPATH")
                    os.environ["DANAPATH"] = abs_folder_path
                    print("os DANAPATH", os.environ.get("DANAPATH"))
                    try:
                        print("os DANAPATH", os.environ.get("DANAPATH"))
                        sandbox_context = SandboxContext()
                        sandbox_context.set("system:user_id", str(request.context.get("user_id", "Lam")))
                        sandbox_context.set("system:session_id", "test-agent-creation")
                        sandbox_context.set("system:agent_instance_id", str(Path(request.folder_path).stem))
                        print(f"sandbox_context: {sandbox_context.get_scope('system')}")
                        result = DanaSandbox.execute_file_once(file_path=temp_file_path, context=sandbox_context)

                        # Get the response from the execution
                        if result.success and result.output:
                            response_text = result.output.strip()
                        else:
                            # Multi-file execution failed, use LLM fallback
                            logger.warning(f"Multi-file agent execution failed: {result.error}, using LLM fallback")
                            print(f"Multi-file agent execution failed: {result.error}, using LLM fallback")

                            llm_response = await _llm_fallback(agent_name, request.agent_description, message)

                            print("--------------------------------")
                            print(f"LLM fallback response: {llm_response}")
                            print("--------------------------------")

                            return AgentTestResponse(success=True, agent_response=llm_response, error=None)

                    except Exception as e:
                        # Exception during multi-file execution, use LLM fallback
                        logger.warning(f"Exception during multi-file execution: {e}, using LLM fallback")
                        print(f"Exception during multi-file execution: {e}, using LLM fallback")

                        llm_response = await _llm_fallback(agent_name, request.agent_description, message)

                        print("--------------------------------")
                        print(f"LLM fallback response: {llm_response}")
                        print("--------------------------------")

                        return AgentTestResponse(success=True, agent_response=llm_response, error=None)
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
            else:
                # main.na doesn't exist, use LLM fallback
                logger.info(f"main.na not found at {main_na_path}, using LLM fallback")
                print(f"main.na not found at {main_na_path}, using LLM fallback")

                llm_response = await _llm_fallback(agent_name, request.agent_description, message)

                print("--------------------------------")
                print(f"LLM fallback response: {llm_response}")
                print("--------------------------------")

                return AgentTestResponse(success=True, agent_response=llm_response, error=None)

        # If no folder_path provided, check if agent_code is empty or minimal
        if not agent_code or agent_code.strip() == "" or len(agent_code.strip()) < 50:
            logger.info("No substantial agent code provided, using LLM fallback")
            print("No substantial agent code provided, using LLM fallback")

            llm_response = await _llm_fallback(agent_name, request.agent_description, message)

            print("--------------------------------")
            print(f"LLM fallback response: {llm_response}")
            print("--------------------------------")

            return AgentTestResponse(success=True, agent_response=llm_response, error=None)

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
            result = DanaSandbox.execute_file_once(file_path=full_path, context=sandbox_context)

            if not result.success:
                # Dana execution failed, use LLM fallback
                logger.warning(f"Dana execution failed: {result.error}, using LLM fallback")
                print(f"Dana execution failed: {result.error}, using LLM fallback")

                llm_response = await _llm_fallback(agent_name, request.agent_description, message)

                print("--------------------------------")
                print(f"LLM fallback response: {llm_response}")
                print("--------------------------------")

                return AgentTestResponse(success=True, agent_response=llm_response, error=None)

        except Exception as e:
            # Exception during execution, use LLM fallback
            logger.warning(f"Exception during Dana execution: {e}, using LLM fallback")
            print(f"Exception during Dana execution: {e}, using LLM fallback")

            llm_response = await _llm_fallback(agent_name, request.agent_description, message)

            print("--------------------------------")
            print(f"LLM fallback response: {llm_response}")
            print("--------------------------------")

            return AgentTestResponse(success=True, agent_response=llm_response, error=None)
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
        # Final fallback: if everything else fails, try LLM fallback
        logger.error(f"Unexpected error in agent test: {e}, attempting LLM fallback")
        try:
            llm_response = await _llm_fallback(agent_name, request.agent_description, message)
            print("--------------------------------")
            print(f"Final LLM fallback response: {llm_response}")
            print("--------------------------------")
            return AgentTestResponse(success=True, agent_response=llm_response, error=None)
        except Exception as llm_error:
            error_msg = f"Error testing agent: {str(e)}. LLM fallback also failed: {str(llm_error)}"
            print(error_msg)
            return AgentTestResponse(success=False, agent_response="", error=error_msg)
