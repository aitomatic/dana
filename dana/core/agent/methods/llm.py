from dana.common.types import BaseRequest, BaseResponse
from dana.core.lang.sandbox_context import SandboxContext


class LLMMixin:
    def llm_sync(self, request: str | dict | BaseRequest, sandbox_context: SandboxContext | None = None, **kwargs) -> str | BaseResponse:
        """Synchronous agent LLM method."""
        if not sandbox_context:
            return "Sandbox context required for LLM calls"

        # Get LLM resource
        llm_resource = self.llm_resource
        if llm_resource is None:
            return "LLM resource not available - please configure an LLM resource for this agent"

        try:
            # Import py_llm
            from dana.libs.corelib.py_wrappers.py_llm import py_llm

            # Prepare the prompt
            if isinstance(request, str):
                prompt = request
            elif isinstance(request, dict):
                if "prompt" in request:
                    prompt = request["prompt"]
                elif "messages" in request:
                    # Extract user message from messages
                    messages = request["messages"]
                    if messages and isinstance(messages, list):
                        # Find the last user message
                        for msg in reversed(messages):
                            if isinstance(msg, dict) and msg.get("role") == "user":
                                prompt = msg.get("content", "")
                                break
                        else:
                            prompt = str(messages[-1]) if messages else ""
                    else:
                        prompt = str(messages)
                else:
                    prompt = str(request)
            elif isinstance(request, BaseRequest):
                # Extract prompt from BaseRequest arguments
                args = request.arguments
                if isinstance(args, dict):
                    if "prompt" in args:
                        prompt = args["prompt"]
                    elif "messages" in args:
                        messages = args["messages"]
                        if messages and isinstance(messages, list):
                            for msg in reversed(messages):
                                if isinstance(msg, dict) and msg.get("role") == "user":
                                    prompt = msg.get("content", "")
                                    break
                            else:
                                prompt = str(messages[-1]) if messages else ""
                        else:
                            prompt = str(messages)
                    else:
                        prompt = str(args)
                else:
                    prompt = str(args)
            else:
                raise ValueError(f"Invalid request type: {type(request)}")

            # Prepare options
            options = {}
            if isinstance(request, dict) and "system" in request:
                options["system_message"] = request["system"]

            # Call py_llm with the agent's LLM resource directly, synchronously
            result = py_llm(context=sandbox_context, prompt=prompt, options=options, llm_resource=llm_resource, is_sync=True)

            # Return the result directly (no Promise handling needed)
            return result

        except Exception as e:
            return f"Error calling LLM: {str(e)}"
