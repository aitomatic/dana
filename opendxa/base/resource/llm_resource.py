"""LLM resource implementation."""

import json
from typing import Any, Dict, Optional, Union, Callable, List

import aisuite as ai
from openai.types.chat import ChatCompletion
from opendxa.common.exceptions import LLMError
from opendxa.base.resource.base_resource import BaseResource, ResourceResponse, QueryStrategy
from opendxa.common.utils.misc import get_field
from opendxa.common.mixins.tool_callable import ToolCallable, OpenAIFunctionCall
from opendxa.common.mixins.registerable import Registerable
from opendxa.common.mixins.queryable import QueryParams
class LLMResource(BaseResource):
    """LLM resource implementation using AISuite."""

    # To avoid accidentally sending too much data to the LLM,
    # we limit the total length of tool-call responses.
    MAX_TOOL_CALL_RESPONSE_LENGTH = 10000

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
        self._mock_llm_call: Optional[Union[bool, Callable[[Dict[str, Any]], Dict[str, Any]]]] = self.config.get("mock_llm_call", None)
        # By default, use iterative querying for tool-calling LLMs
        self._query_strategy = self.config.get("query_strategy", QueryStrategy.ITERATIVE)
        self._query_max_iterations = self.config.get("query_max_iterations", 10)

    # ===== Public Interface Methods =====
    @ToolCallable.tool
    async def query(self, params: QueryParams = None) -> ResourceResponse:
        """Query the LLM with the given request.

        This method determines whether to use iterative or single-shot querying based on
        the request parameters and available resources.

        Args:
            params: Dictionary containing:
                - user_messages: The user messages
                - system_messages: Optional system messages
                - available_resources: Optional list of BaseResource objects to use as tools
                - max_iterations: Optional maximum number of resource calling iterations
                - max_tokens: Optional maximum tokens for response
                - temperature: Optional temperature for generation
                - additional parameters

        Returns:
            QueryResponse with "content", "model", "usage".
        """

        # Use iterative querying if tools are provided, otherwise use single-shot
        response = await self._query_iterative(params)
        return ResourceResponse(success=True, content=response)

    async def initialize(self) -> None:
        """Initialize the AISuite client etc."""
        if not self._client:
            # Handle backward compatibility for top-level api_key
            if "api_key" in self.config and "openai" not in self.provider_configs:
                self.provider_configs["openai"] = {"api_key": self.config["api_key"]}

            self._client = ai.Client(provider_configs=self.provider_configs)
            # Only log if we have a model
            if self.model:
                self.info("LLM client initialized successfully for model: %s", self.model)
            else:
                self.info("LLM client initialized without a model")
        
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
                - user_messages: The user messages
                - system_messages: Optional system messages
                - available_resources: Dictionary of available tools/resources
                - max_iterations: Optional. Maximum number of tool call iterations
                - max_tokens: Optional. Maximum tokens for each response
                - temperature: Optional. Controls response randomness (0.0 to 1.0)
            
        Returns:
            Dict[str, Any]: The final LLM response after all tool calls are complete,
            containing the assistant's message and any tool calls.
        """
        # Initialize variables for the loop
        if self.get_query_strategy() == QueryStrategy.ITERATIVE:
            max_iterations = request.get("max_iterations", self.get_query_max_iterations())
        else:
            max_iterations = 1

        # Add a system prompt that encourages resource use if not provided
        system_messages = request.get("system_messages", [
            "You are an assistant. Use tools when necessary to complete tasks. "
            "After receiving tool results, you can request additional tools if needed."
        ])

        user_messages = request.get("user_messages", [
            "Hello, how are you?"
        ])
        
        # Initialize message history with system and user messages
        message_history: List[Dict[str, Any]] = []
        message_history.append({"role": "system", "content": '\n'.join(system_messages)})
        message_history.append({"role": "user", "content": '\n'.join(user_messages)})

        # Register all resources in the registry
        available_resources = request.get("available_resources", {})
        for resource in available_resources.values():
            resource.add_to_registry()
        
        iteration = 0
        while iteration < max_iterations:
            self.info(f"Resource calling iteration {iteration}/{max_iterations}")
            iteration += 1
            
            # TODO: Guard rail the total message length before sending

            # Make the LLM query with available resources and message history
            response = await self._query_once({
                "available_resources": request.get("available_resources", {}),
                "max_tokens": request.get("max_tokens"),
                "temperature": request.get("temperature", 0.7),
                "messages": message_history  # Pass read-only message history
            })
            
            choices = get_field(response, "choices", [])
            response_message = get_field(choices[0], "message") if choices and len(choices) > 0 else None

            if response_message:
                # Only add tool_calls if they exist and are a valid list
                tool_calls: List[OpenAIFunctionCall] = get_field(response_message, "tool_calls")
                has_valid_tool_calls = tool_calls and isinstance(tool_calls, list)
                
                if has_valid_tool_calls:
                    # Store the tool request message and get responses for all tool calls
                    self.info("LLM is requesting tools, storing tool request message and calling resources")
                    
                    # First add the assistant message with all tool calls
                    message_history.append({
                        "role": get_field(response_message, "role"),
                        "content": get_field(response_message, "content"),
                        "tool_calls": [i.model_dump() if hasattr(i, "model_dump") else i for i in tool_calls]
                    })
                    
                    # Get responses for all tool calls at once
                    tool_responses = await self._call_requested_tools(tool_calls)
                    message_history.extend(tool_responses)
                else:
                    # If LLM is not requesting tools, we're done
                    self.info("LLM is not requesting tools, returning final response")
                    break

        # If we've reached the maximum iterations, return the final response
        if iteration == max_iterations:
            self.info(f"Reached maximum iterations ({max_iterations}), returning final response")

        # Unregister all resources in the registry (to avoid memory leaks)
        for resource in available_resources.values():
            resource.remove_from_registry()

        return response if isinstance(response, ResourceResponse) else {
            "choices": (response.choices if hasattr(response, "choices") else []),
            "usage": (response.usage if hasattr(response, "usage") else {}),
            "model": (response.model if hasattr(response, "model") else "")
        }

    async def _query_once(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single call to the LLM with the given request.
        
        This method makes a single API call to the LLM using the provided message history.
        The message history is treated as read-only and should contain the complete
        conversation context including system prompts, user messages, and previous
        tool calls and responses.
        
        Args:
            request: Dictionary containing:
                - message_history: List of previous messages (read-only)
                - available_resources: Dictionary of available tools/resources
                - max_tokens: Optional. Maximum tokens for the response
                - temperature: Optional. Controls response randomness (0.0 to 1.0)
            
        Returns:
            Dict[str, Any]: The LLM response object containing:
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
        messages = get_field(request, "messages", [])
        if not messages:
            raise ValueError("messages must be provided and non-empty")
        
        # Build request parameters
        request = self._build_request_params(request)
        
        # Make the API call
        try:
            response = self._client.chat.completions.create(**request)
            self._log_llm_response(response)
            return response
        except Exception as e:
            self.error("LLM query failed: %s", str(e))
            raise LLMError(f"LLM query failed: {str(e)}") from e

    async def _mock_llm_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mock LLM query for testing purposes.
        
        Args:
            request: Dictionary containing the request parameters
            
        Returns:
            Dict[str, Any]: Mock response
        """
        messages = get_field(request, "messages", [])
        if not messages:
            raise ValueError("messages must be provided and non-empty")
            
        # Get the last user message
        last_message = next((msg for msg in reversed(messages) if msg["role"] == "user"), None)
        if not last_message:
            raise ValueError("No user message found in message history")
            
        # Create a mock response
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Mock response to: {last_message['content']}",
                    "tool_calls": []
                }
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "model": "mock-model"
        }

    def _build_request_params(self, request: Dict[str, Any], available_resources: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build request parameters for LLM API call.
        
        Args:
            request: Dictionary containing request parameters
            available_resources: Optional dictionary of available resources
            
        Returns:
            Dict[str, Any]: Dictionary of request parameters
        """
        params = {
            "messages": get_field(request, "messages", []),
            "temperature": request.get("temperature", 0.7),
            "max_tokens": request.get("max_tokens"),
        }

        if not available_resources:
            available_resources = get_field(request, "available_resources", {})
        
        # Only add model if it's available
        if self.model:
            params["model"] = self.model
            
        if available_resources:
            params["tools"] = self._get_openai_functions(available_resources)
            
        return params

    def _get_openai_functions(self, resources: Dict[str, BaseResource]) -> List[OpenAIFunctionCall]:
        """Get OpenAI functions from available resources.
        
        Args:
            resources: Dictionary of available resources
            
        Returns:
            List[OpenAIFunctionCall]: List of tool definitions
        """
        functions = []
        for _, resource in resources.items():
            functions.extend(resource.list_openai_functions())
        return functions

    async def _call_requested_tools(
        self, 
        tool_calls: List[OpenAIFunctionCall],
        max_response_length: Optional[int] = MAX_TOOL_CALL_RESPONSE_LENGTH
    ) -> List[ResourceResponse]:
        """Call requested resources and get responses.
        
        This method handles tool calls from the LLM, executing each requested tool
        and collecting their responses.
        
        Expected Tool Call Format:
            The format of tool calls is defined by the ToolCallable mixin, which
            converts tool definitions into OpenAI's function calling format.
            
            Each tool call should be a dictionary with:
            {
                "type": "function",
                "function": {
                    "name": str,  # Format: "{resource_name}__{resource_id}__{tool_name}"
                    "arguments": str  # JSON string of parameter values
                }
            }
            
            Example:
            {
                "type": "function",
                "function": {
                    "name": "search__123__query",
                    "arguments": '{"query": "find documents", "limit": 5}'
                }
            }
            
            The method will:
            1. Parse the function name to identify resource and tool
            2. Parse the arguments from JSON string to Python dict
            3. Call the appropriate tool with the arguments
            4. Collect and return all responses
            
            Each response will be in OpenAI's tool response format:
            {
                "role": "tool",
                "name": str,  # The original function name
                "content": str  # The tool's response or error message
            }
        
        Args:
            tool_calls: List of tool calls from the LLM
            max_response_length: Optional maximum length for tool responses
            
        Returns:
            List[ResourceResponse]: List of tool responses in OpenAI format
        """
        responses: List[ResourceResponse] = []
        for tool_call in tool_calls:
            try:
                # Get the function name and arguments
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Parse the function name to get the resource name, id, and tool name
                resource_name, resource_id, tool_name = ToolCallable.parse_name_id_function_string(
                    function_name
                )
                
                # Get the resource
                resource: Optional[ToolCallable] = Registerable.get_from_registry(resource_id)
                if resource is None:
                    self.warning(f"Resource {resource_name} with id {resource_id} not found")
                    continue
                
                if not isinstance(resource, ToolCallable):
                    self.warning(f"Resource {resource_name} with id {resource_id} is not a ToolCallable")
                    continue
                
                # Call the tool
                response = await resource.call_tool(tool_name, arguments)
                
                # Convert response to JSON string to ensure JSON-serializability
                if hasattr(response, "to_json") and callable(response.to_json):
                    response = response.to_json()

                # Truncate response if needed
                if max_response_length and isinstance(response, str):
                    response = response[:max_response_length]
                
            except Exception as e:
                response = f"Tool call failed: {str(e)}"
                self.error(response)

            responses.append({
                "role": "tool",
                "name": function_name,
                "content": response,
                "tool_call_id": tool_call.id 
            })
                
        return responses

    def _log_llm_request(self, request: Dict[str, Any]) -> None:
        """Log LLM request.
        
        Args:
            request: Dictionary containing request parameters
        """
        self.debug("LLM request: %s", json.dumps(request, indent=2))

    def _log_llm_response(self, response: ChatCompletion) -> None:
        """Log LLM response.
        
        Args:
            response: ChatCompletion object containing the response
        """
        self.debug("LLM response: %s", str(response))

    def _get_default_model(self) -> str:
        """Get default model identifier.
        
        Returns:
            str: Default model identifier
        """
        return "openai:gpt-4o-mini"
