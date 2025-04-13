"""LLM resource implementation."""

import os
import json
from typing import Any, Dict, Optional, Union, Callable, List

import aisuite as ai
from openai.types.chat import ChatCompletion
from ...common.exceptions import LLMError
from .base_resource import BaseResource, ResourceResponse
from .mcp import McpResource
from .base_resource import QueryStrategy
from ..utils.registerable import Registerable

class LLMResource(BaseResource, Registerable[BaseResource]):
    """LLM resource implementation using AISuite."""

    _DEFAULT_MODEL = "deepseek:deepseek-chat"

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
        # By default, use iterative querying for tool-calling LLMs
        self._query_strategy = self.config.get("query_strategy", QueryStrategy.ITERATIVE)
        self._query_max_iterations = self.config.get("query_max_iterations", 10)

    # ===== Public Interface Methods =====
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the LLM with the given request.

        This method determines whether to use iterative or single-shot querying based on
        the request parameters and available resources.

        Args:
            request: Dictionary containing:
                - prompt: The user message
                - system_prompt: Optional system prompt
                - resources: Optional list of BaseResource objects to use as tools
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

    async def initialize(self) -> None:
        """Initialize the AISuite client etc."""
        if not self._client:
            # Handle backward compatibility for top-level api_key
            if "api_key" in self.config and "openai" not in self.provider_configs:
                self.provider_configs["openai"] = {"api_key": self.config["api_key"]}

            self._client = ai.Client(provider_configs=self.provider_configs)
            self.info("LLM client initialized successfully for model: %s", self.model)
        
        # Initialize the registerable registry etc.
        Registerable.__init__(self)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            self._client = None

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request contains prompt."""
        return "prompt" in request

    def with_mock_llm_call(self, mock_llm_call: Union[bool, Callable[[Dict[str, Any]], Dict[str, Any]]]) -> 'LLMResource':
        """Set the mock LLM call function."""
        if isinstance(mock_llm_call, Callable) or isinstance(mock_llm_call, bool):
            self._mock_llm_call = mock_llm_call
        else:
            raise ValueError("mock_llm_call must be a Callable or a boolean")

        return self

    # ===== Core Query Processing Methods =====
    async def _query_iterative(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a conversation with the LLM that may involve multiple tool calls.
        
        This method manages the complete conversation flow:
        1. Send initial user request
        2. If LLM requests tools:
           - Store the tool request message
           - Process all requested tool calls
           - Send all tool results back to LLM
           - Continue until LLM provides final response
        3. Return the final response
        
        Args:
            request: Dictionary containing:
                - prompt: The user's original question/request
                - system_prompt: Optional. Instructions for the LLM's behavior
                - available_resources: Dictionary of available tools/resources
                - max_iterations: Optional. Maximum number of tool call iterations
                - max_tokens: Optional. Maximum tokens for each response
                - temperature: Optional. Controls response randomness (0.0 to 1.0)
            
        Returns:
            The final LLM response after all tool calls are complete.
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
            "Before any response, first repeat verbatim what you are told about tools and how to request them."
        ))
        
        # Initialize message history with system and user messages
        message_history = []
        message_history.append({"role": "system", "content": system_prompt})
        message_history.append({"role": "user", "content": request["prompt"]})
        
        iteration = 0
        while iteration < max_iterations:
            self.info(f"Resource calling iteration {iteration}/{max_iterations}")
            iteration += 1
            
            # Make the LLM query with available resources and message history
            response = await self._query_once({
                "available_resources": request.get("available_resources", {}),
                "max_tokens": request.get("max_tokens"),
                "temperature": request.get("temperature", 0.7),
                "messages": message_history  # Pass read-only message history
            })
            
            if "choices" in response and len(response["choices"]) > 0:
                response_message = response["choices"][0]["message"]
            else:
                response_message = response.choices[0].message

            response_message_dict = {
                "role": response_message["role"] if "role" in response_message else response_message.role,
                "content": response_message["content"] if "content" in response_message else response_message.content
            }
            message_history.append(response_message_dict)
            
            # Check if the LLM is requesting to use tools
            tool_calls = None
            if "tool_calls" in response_message:
                tool_calls = response_message["tool_calls"]
            elif hasattr(response_message, "tool_calls"):
                tool_calls = response_message.tool_calls
            
            if tool_calls:
                response_message_dict["tool_calls"] = tool_calls

                # Store the tool request message and get responses for all tool calls
                self.info("LLM is requesting tools, storing tool request message and calling resources")
                tool_call_responses = await self._call_requested_resources(tool_calls)

                # Add tool responses to history
                for tool_response in tool_call_responses:
                    message_history.append(tool_response)
            else:
                # If LLM is not requesting tools, we're done
                self.info("LLM is not requesting tools, returning final response")
                break

        # If we've reached the maximum iterations, return the final response
        if iteration == max_iterations:
            self.info(f"Reached maximum iterations ({max_iterations}), returning final response")

        if hasattr(response, "choices"):
            # Convert to a Dict
            return {
                "choices": response.choices,
                "usage": response.usage,
                "model": response.model
            }
        else:
            return response

    async def _query_once(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single call to the LLM with the given request.
        
        This method uses the provided message history to make a single LLM call.
        The message history is treated as read-only.
        
        Args:
            request: Dictionary containing:
                - messages: List of messages, including all previous messages (read-only)
                - available_resources: Dictionary of available tools/resources
                - max_tokens: Optional. Maximum tokens for the response
                - temperature: Optional. Controls response randomness (0.0 to 1.0)
            
        Returns:
            The complete LLM response object, including:
            - choices[0].message: The assistant's message, which may contain tool_calls
            - usage: Token usage statistics
        """
        # Check for mock flag or function
        if callable(self._mock_llm_call):
            return await self._mock_llm_call(request)
        elif self._mock_llm_call:
            return await self._mock_llm_query(request)

        if not self._client:
            await self.initialize()
        assert self._client is not None

        # Get message history (read-only)
        messages = request.get("messages", [])
        if not messages:
            raise ValueError("messages must be provided and non-empty")
        
        # Build request parameters
        request_params = await self._build_request_params(
            request, 
            request.get("available_resources")
        )

        try:
            # Log the request
            self._log_llm_request(messages)
        
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                **request_params
            )

            # Log the response
            self._log_llm_response(response)
            
            return response

        except Exception as e:
            self.error("Error querying LLM: %s", str(e))
            raise LLMError("Error querying LLM") from e

    async def _mock_llm_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Return a mock response that matches the OpenAI API response format.
        
        The response structure matches what we get from the real API:
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Mock response",
                        "tool_calls": None  # Or a list of tool calls if needed
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        """
        prompt = request.get('prompt', '')
        
        # Create a mock response that matches the OpenAI API format
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": f"Mock response for: {prompt}",
                        "tool_calls": None
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }

    # ===== Message and Request Building Methods =====
    async def _build_request_params(self, request: Dict[str, Any], available_resources: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build the request parameters for the LLM call.
        
        Args:
            request: Dictionary containing request parameters
            available_resources: Optional dictionary of available tools/resources
            
        Returns:
            Dictionary of request parameters with None values filtered out.
        """
        request_params = {
            "temperature": float(request.get("temperature", self.config.get("temperature", 0.7))),
            "top_p": float(self.config.get("top_p", 1.0)),
            "max_tokens": request.get("max_tokens", self.config.get("max_tokens")),
            "frequency_penalty": self.config.get("frequency_penalty"),
            "presence_penalty": self.config.get("presence_penalty"),
        }

        # Add tool strings for resources if provided
        if available_resources:
            assert isinstance(available_resources, Dict), "available_resources must be a dictionary"
            request_params["tools"] = await self.__get_function_calls(available_resources)

        # Filter out None values
        return {k: v for k, v in request_params.items() if v is not None}

    async def __get_function_calls(self, resources: Dict[str, BaseResource]) -> List[Dict[str, Any]]:
        """Get tool strings for the list of resources.

        Args:
            resources: Dictionary of available resources

        Returns:
            List of tool specifications for the underlying LLM to use
        """
        resource_strings: List[Dict[str, Any]] = []
        for resource in resources.values():
            resource_strings.extend(await resource.as_function_calls())
            # Put the resource in our registry so we can call on it as needed later
            self.add_to_registry(resource.resource_id, resource)
        return resource_strings

    # ===== Resource Calling Methods =====
    async def _call_requested_resources(
        self, 
        tool_calls: List[Any]
    ) -> List[Dict[str, Any]]:
        """Call multiple requested tools and format their responses.
        
        This method:
        1. Processes each tool call request
        2. Calls the corresponding tool for each request
        3. Returns a list of tool response messages
        
        Args:
            tool_calls: List of tool call objects from the LLM response
        
        Returns:
            List of tool response messages, each containing:
                - role: "tool"
                - tool_call_id: Matches the id from the tool call request
                - content: The JSON-serialized response from the tool
        """
        if not tool_calls:
            return []

        tool_call_responses: List[Dict[str, Any]] = []
        for tool_call in tool_calls:
            # Expected format: name-uuid-function_name
            resource_name, resource_id, function_name = self._parse_name_id_function_string(tool_call.function.name)
            self.info(f"Resource name: {resource_name}, resource id: {resource_id}, function name: {function_name}")

            resource = self.get_from_registry(resource_id)
            if not resource:
                self.error(f"Resource not found: {resource_id}")
                continue
            
            if isinstance(resource, McpResource):
                response = await resource.query({"tool": function_name, "arguments": tool_call.function.arguments})
                if isinstance(response, ResourceResponse) and response.content:
                    # Get at the lower-level MCP Tool response content
                    if hasattr(response.content, 'content') and isinstance(response.content.content, list):
                        # Extract text content from the first content item
                        response = response.content.content[0].text
                    else:
                        response = response.content
            else:
                response = await resource.query(tool_call.function.arguments)

            # Format the response as a proper tool response message
            tool_call_responses.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(response) if not isinstance(response, str) else response
            })

        return tool_call_responses

    async def _call_one_resource(
        self,
        resource: BaseResource,
        tool_name: Optional[str],
        params: Dict[str, Any]
    ) -> Any:
        """Execute a resource with appropriate calling conventions.
        
        This method handles the execution of a resource's functionality (which the LLM API calls a "tool").
        We maintain the "resource" terminology internally for consistency.

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

    # ===== Logging and Utility Methods =====
    def _log_llm_request(self, request: Dict[str, Any]) -> None:
        """Log the LLM request.
        
        Args:
            request: The request object from the LLM API call
        """
        self.info(f"REQUEST TO {self.model}:\n{'-' * 80}\n{request}\n{'-' * 80}")

    def _log_llm_response(self, response: ChatCompletion) -> None:
        """Log the LLM response and usage statistics.
        
        Args:
            response: The response object from the LLM API call
        """
        # Log the response from the LLM
        self.info(f"RESPONSE FROM {self.model}:\n{'-' * 80}\n{response}\n{'-' * 80}")
        
        # Log usage statistics if available
        usage = response.usage
        if usage:
            self.info(
                f"USAGE: prompt_tokens={usage.prompt_tokens}, "
                f"completion_tokens={usage.completion_tokens}, "
                f"total_tokens={usage.total_tokens}"
            )

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
