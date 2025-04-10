"""LLM resource implementation."""

import os
from typing import Any, Dict, Optional, Union, Callable, List
import json

import aisuite as ai
from ...common.exceptions import LLMError
from .base_resource import BaseResource
from .mcp import McpResource
from .base_resource import QueryStrategy

class LLMResource(BaseResource):
    """LLM resource implementation using AISuite."""

    _DEFAULT_MODEL = "deepseek:deepseek-chat"

    # ===== Core Resource Methods =====
    async def initialize(self) -> None:
        """Initialize the AISuite client."""
        if not self._client:
            # Handle backward compatibility for top-level api_key
            if "api_key" in self.config and "openai" not in self.provider_configs:
                self.provider_configs["openai"] = {"api_key": self.config["api_key"]}

            self._client = ai.Client(provider_configs=self.provider_configs)
            self.info("LLM client initialized successfully for model: %s", self.model)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            self._client = None

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request contains prompt."""
        return "prompt" in request

    # ===== Initialization and Configuration =====
    def _get_default_model(self) -> str:
        """Get the default model by checking the environment variable."""
        if "OPENDXA_DEFAULT_MODEL" in os.environ:
            return os.environ["OPENDXA_DEFAULT_MODEL"]
        elif "DEEPSEEK_API_KEY" in os.environ:
            return "deepseek:deepseek-chat"
        elif "ANTHROPIC_API_KEY" in os.environ:
            return "anthropic:claude-3-5-sonnet-20241022"
        elif "OPENAI_API_KEY" in os.environ:
            return "openai:gpt-4o"

        return self._DEFAULT_MODEL

    def __init__(self, name: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM resource.

        Args:
            name: Resource name.
            config: Configuration dictionary containing:
                - model: Model identifier in format "provider:model" (e.g. "openai:gpt-4").
                - providers: Dictionary of provider configurations.
                - temperature: Float between 0 and 1, controlling the randomness of the LLM's output.
                - api_key: Optional API key (will use environment variables if not provided).
                - mock_llm_call: Optional flag or function for mocking LLM responses.
                  If 'mock_llm_call' is a callable, it will be called with the request
                  and its return value will be used as the response.
                  If 'mock_llm_call' is set but not callable, the '_mock_llm_query' method
                  will be used, which returns a basic response echoing the prompt.
                - max_retries: Maximum number of retry attempts for LLM queries.
                - retry_delay: Delay in seconds between retry attempts.
                - additional provider-specific parameters.
        """
        if name is None:
            name = "default_llm_resource"

        super().__init__(name)
        self.config = config or {}
        self.model = self.config.get("model", self._get_default_model())
        self.provider_configs = self.config.get("providers", {})
        self._client: Optional[ai.Client] = None
        self.max_retries = int(self.config.get("max_retries", 3))
        self.retry_delay = float(self.config.get("retry_delay", 1.0))
        self._mock_llm_call = self.config.get("mock_llm_call", None)

    # ===== Query Methods =====
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the LLM with the given request.

        This method determines whether to use iterative or single-shot querying based on
        the request parameters and available resources.

        Args:
            request: Dictionary containing:
                - prompt: The user message
                - system_prompt: Optional system prompt
                - available_resources: Optional list of BaseResource objects to use as tools
                - max_iterations: Optional maximum number of resource calling iterations
                - max_tokens: Optional maximum tokens for response
                - temperature: Optional temperature for generation
                - additional parameters

        Returns:
            Dictionary with "content", "model", "usage".
        """
        # Use iterative querying if tools are provided, otherwise use single-shot
        response = await self._query_iterative(request)
        return response or {}

    async def _query_iterative(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the LLM with support for iterative resource calling.
        
        This method allows the LLM to request resources, receive their results, and then
        potentially request more resources based on those results, up to a maximum number
        of iterations.
        
        Note: The LLM API uses "tools" terminology for resources.

        Args:
            request: Dictionary containing:
                - prompt: The user message
                - system_prompt: Optional system prompt
                - available_resources: List of available BaseResource objects
                - max_iterations: Maximum number of resource calling iterations (default: 3)
                - max_tokens: Optional maximum tokens for response
                - temperature: Optional temperature for generation
                - additional parameters
            
        Returns:
            Final LLM response with all resource results incorporated
        """
        # Initialize variables for the loop
        if self.get_query_strategy() == QueryStrategy.ITERATIVE:
            max_iterations = self.get_query_max_iterations()
        else:
            max_iterations = 1

        # Add a system prompt that encourages resource use if not provided
        system_prompt = request.get("system_prompt", (
            "You are an assistant. Use tools when necessary to complete tasks. "
            "After receiving tool results, you can request additional tools if needed."
        ))
        
        # Main loop for iterative resource calling
        current_prompt = request["prompt"]
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            self.info(f"Resource calling iteration {iteration}/{max_iterations}")
            
            # Make the LLM query with available resources
            response = await self._query_once({
                "prompt": current_prompt,
                "system_prompt": system_prompt,
                "available_resources": request.get("available_resources", {}),
                "max_tokens": request.get("max_tokens"),
                "temperature": request.get("temperature", 0.7),
            })
            
            # Check if the underlying LLM requested tools
            requested_tools = response.get("requested_tools")
            if not requested_tools or len(requested_tools) == 0:
                self.info("No more tools requested, returning final response")
                return response
            
            # Format tool results for the next iteration
            tool_result_text = "\n".join(
                [f"Tool: {tool.function.name}\nResponse: {tool.function.arguments}" 
                 for tool in requested_tools]
            )

            # Enhance the prompt with tool results
            current_prompt = f"{current_prompt}\n\n" \
                           f"<tool_calling_results>\n{tool_result_text}\n</tool_calling_results>"
            
            # Add a specific instruction for the next iteration
            current_prompt += (
                "\n\nBased on these tool results, continue your reasoning. "
                "You can request additional tools if needed to complete your task."
            )
        
        # If we've reached the maximum iterations, return the final response
        self.info(f"Reached maximum iterations ({max_iterations}), returning final response")
        return response or {}

    async def _query_once(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the LLM with the given prompt and resources.

        Args:
            request: Dictionary containing:
                - prompt: The user message
                - system_prompt: Optional system prompt
                - available_resources: Optional list of BaseResource objects to use as tools
                - max_tokens: Optional maximum tokens for response
                - temperature: Optional temperature for generation
                - additional parameters

        Returns:
            Dictionary with "content", "model", "usage", and optionally "requested_tools" keys.
        """
        # Check for mock flag or function
        if callable(self._mock_llm_call):
            # If mock_llm_call is a callable, call it with the request
            return await self._mock_llm_call(request)
        elif self._mock_llm_call:
            # If mock_llm_call is a boolean, call our built-in mock function
            return await self._mock_llm_query(request)

        if not self._client:
            await self.initialize()

        messages = []
        if "system_prompt" in request:
            messages.append({"role": "system", "content": request["system_prompt"]})

        if "prompt" in request:
            messages.append({"role": "user", "content": request["prompt"]})
        else:
            raise ValueError("'Prompt' is required")

        # Log the prompt being sent to the LLM
        self.info(f"PROMPT TO {self.model}:\n{'-' * 80}\n{messages}\n{'-' * 80}")
        
        request_params = {
            "temperature": float(request.get("temperature", self.config.get("temperature", 0.7))),
            "top_p": float(self.config.get("top_p", 1.0)),
            "max_tokens": request.get("max_tokens", self.config.get("max_tokens")),
            "frequency_penalty": self.config.get("frequency_penalty"),
            "presence_penalty": self.config.get("presence_penalty"),
        }

        # Add tool strings for resources if provided in the request
        if "available_resources" in request and request["available_resources"]:
            assert isinstance(request["available_resources"], Dict), "available_resources must be a dictionary"
            request_params["tools"] = await self._get_tool_strings(request["available_resources"])

        # Filter out None values
        request_params = {k: v for k, v in request_params.items() if v is not None}

        try:
            assert self._client is not None
            # Let aisuite handle the provider-specific response processing
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                **request_params
            )

            # Use aisuite's standardized response format
            # handle tool calls
            reasoning = None
            requested_tools = None
            if hasattr(response, "choices") and hasattr(response.choices[0].message, "tool_calls"):
                requested_tools = response.choices[0].message.tool_calls
                reasoning = response.choices[0].finish_reason
            elif hasattr(response, "reasoning_content"):
                reasoning = response.reasoning_content
            elif hasattr(response, "choices") and hasattr(response.choices[0].message, "reasoning_content"):
                reasoning = response.choices[0].message.reasoning_content

            content = response.choices[0].message.content if hasattr(response, 'choices') else response.content
            
            if requested_tools:
                # Format tool calls into a readable list
                tool_list = []
                for tool in requested_tools:
                    tool_info = f"{tool.function.name}: {tool.function.arguments}"
                    tool_list.append(tool_info)

                content = f"{reasoning}:\n\n" + "\n".join(tool_list)

            # Log the response from the LLM
            self.info(f"RESPONSE FROM {self.model}:\n{'-' * 80}\n{content}\n{'-' * 80}")
            
            # Log usage statistics if available
            if hasattr(response, "usage"):
                usage = response.usage
                if hasattr(usage, 'prompt_tokens') and \
                    hasattr(usage, 'completion_tokens') and \
                        hasattr(usage, 'total_tokens'):
                    self.info(
                        f"USAGE: prompt_tokens={usage.prompt_tokens}, "
                        f"completion_tokens={usage.completion_tokens}, "
                        f"total_tokens={usage.total_tokens}"
                    )

            return {
                "content": content,
                "model": self.model,  # Use our model string since it's guaranteed to exist
                "usage": getattr(response, "usage", None),
                # Include any thinking content if present
                "reasoning": reasoning,
                "requested_tools": requested_tools,
            }

        except Exception as e:
            self.error("Error querying LLM: %s", str(e))
            raise LLMError(f"Error querying LLM: {str(e)}") from e

    async def _get_tool_strings(self, resources: Dict[str, BaseResource]) -> List[Dict[str, Any]]:
        """Get tool strings for the list of resources.

        Args:
            resources: Dictionary of available resources

        Returns:
            List of tool specifications for the underlying LLM to use
        """
        resource_strings: List[Dict[str, Any]] = []
        for resource_id, resource in resources.items():
            resource_strings.extend(await resource.get_tool_strings(resource_id))
        return resource_strings

    # ===== Resource Tool Handling =====
    def deprecated_get_resource_tools(self, resources: Dict[str, BaseResource]) -> List[Dict[str, Any]]:
        """Get tools from resources in the format expected by the LLM API.

        This method converts our internal resource representation into the format
        expected by the LLM API's tool calling interface.

        Args:
            resources: Dictionary of available resources

        Returns:
            List of tools in LLM API format
        """
        tools = []
        for resource_name, resource in resources.items():
            # Get the resource's schema
            schema = resource.get_schema()
            if not schema:
                continue

            # Convert the schema to the LLM API's tool format
            for tool_name, tool_schema in schema.items():
                # Create the function description
                function_desc = {
                    "name": f"{resource_name}__query__{tool_name}",
                    "description": tool_schema.get("description", ""),
                    "parameters": tool_schema.get("parameters", {})
                }

                # Add the tool to the list
                tools.append({
                    "type": "function",
                    "function": function_desc
                })

        return tools

    async def _query_one_resource(
        self,
        resource: BaseResource,
        tool_name: Optional[str],
        params: Dict[str, Any]
    ) -> Any:
        """Execute a resource with appropriate calling conventions.
        
        This method handles the execution of a resource's functionality (which the LLM API calls a "tool").
        We maintain the "resources" terminology internally for consistency.

        Handles different resource types (MCP, Agent, Base) with their specific
        calling patterns while maintaining a clean interface.

        Args:
            resource: Resource to call
            tool_name: Name of the tool to execute (from LLM's function name)
            params: Dictionary of parameters to pass to the resource

        Returns:
            Resource response
        """
        # For MCP resources, we need to use a specific format
        if isinstance(resource, McpResource):
            return await resource.query({"tool": tool_name, "arguments": params})

        # For other resources, we can pass the parameters directly
        return await resource.query(params)

    async def _query_requested_resources(
        self, 
        requested_resources: List[Any], 
        available_resources: Dict[str, BaseResource]
    ) -> List[Dict]:
        """Execute resources using provided resources.
        
        This method processes resources requested by the LLM (which the LLM API calls "tools").
        We maintain the "resources" terminology internally for consistency.

        Args:
            requested_resources: List of resources to execute (from LLM's "requested_tools")
            available_resources: Dictionary of available resources

        Returns:
            List of resource responses
        """
        try:
            resource_responses = []
            for requested_resource in requested_resources:
                function_name = requested_resource.function.name
                try:
                    # Parse the function name to extract resource name and tool name
                    # Format: [resource_name]__query__[tool_name]
                    resource_name, *_, tool_name = function_name.split("__")
                except ValueError:
                    self.warning(
                        f"Invalid function name format: {function_name}, "
                        "expected [resource_name]__query__[tool_name]"
                    )
                    continue

                my_resource = available_resources.get(resource_name)
                if not my_resource:
                    self.warning(f"Resource not found: {resource_name}")
                    continue

                params = requested_resource.function.arguments
                if isinstance(params, str):
                    params = json.loads(params)

                response = await self._query_one_resource(my_resource, tool_name, params)
                resource_responses.append({"resource_name": function_name, "response": response})

            return resource_responses

        except json.JSONDecodeError as e:
            self.error(f"Failed to parse resource arguments as JSON: {e}")
            return []
        except Exception as e:
            self.error(f"Error querying resource: {e}")
            return []

    # ===== Error Handling and Utilities =====
    def with_mock_llm_call(self, mock_llm_call: Union[bool, Callable[[Dict[str, Any]], Dict[str, Any]]]) -> 'LLMResource':
        """Set the mock LLM call function."""
        if isinstance(mock_llm_call, Callable) or isinstance(mock_llm_call, bool):
            self._mock_llm_call = mock_llm_call
        else:
            raise ValueError("mock_llm_call must be a Callable or a boolean")

        return self

    async def _mock_llm_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Return a mock response that matches the real implementation structure."""
        prompt = request.get('prompt', '')
        
        # Create a mock response that matches the real implementation
        return {
            "content": f"Mock response for: {prompt}",
            "model": self.model,
            "usage": None,
            "reasoning": None,
            "requested_tools": None
        }
