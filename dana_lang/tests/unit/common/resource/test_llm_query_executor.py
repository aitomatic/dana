"""Test the LLMQueryExecutor class."""

import asyncio
import os
import threading
import unittest
from threading import Thread
from unittest.mock import AsyncMock, MagicMock, patch

from dana_lang.common.exceptions import (
    LLMAuthenticationError,
    LLMContextLengthError,
    LLMError,
    LLMRateLimitError,
)
from dana_lang.common.mixins.queryable import QueryStrategy
from dana_lang.common.sys_resource.llm.llm_query_executor import LLMQueryExecutor
from dana_lang.common.utils.misc import Misc


class TestLLMQueryExecutor(unittest.IsolatedAsyncioTestCase):
    """Test the LLMQueryExecutor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.query_executor = LLMQueryExecutor()

    def test_initialization(self):
        """Test query executor initialization."""
        # Test default initialization
        self.assertIsNone(self.query_executor.client)
        self.assertIsNone(self.query_executor.model)
        self.assertEqual(self.query_executor.query_strategy, QueryStrategy.ITERATIVE)
        self.assertEqual(self.query_executor.query_max_iterations, 10)

        # Test custom initialization
        mock_client = MagicMock()
        custom_executor = LLMQueryExecutor(
            client=mock_client, model="openai:gpt-4", query_strategy=QueryStrategy.ONCE, query_max_iterations=5
        )
        self.assertEqual(custom_executor.client, mock_client)
        self.assertEqual(custom_executor.model, "openai:gpt-4")
        self.assertEqual(custom_executor.query_strategy, QueryStrategy.ONCE)
        self.assertEqual(custom_executor.query_max_iterations, 5)

    def test_property_setters(self):
        """Test property setters."""
        mock_client = MagicMock()
        self.query_executor.client = mock_client
        self.assertEqual(self.query_executor.client, mock_client)

        self.query_executor.model = "anthropic:claude-3-opus"
        self.assertEqual(self.query_executor.model, "anthropic:claude-3-opus")

        self.query_executor.query_strategy = QueryStrategy.ONCE
        self.assertEqual(self.query_executor.query_strategy, QueryStrategy.ONCE)

        self.query_executor.query_max_iterations = 3
        self.assertEqual(self.query_executor.query_max_iterations, 3)

    def test_set_mock_llm_call(self):
        """Test setting mock LLM call."""
        # Test with boolean
        self.query_executor.set_mock_llm_call(True)
        self.assertTrue(self.query_executor._mock_llm_call)

        # Test with callable
        mock_function = MagicMock()
        self.query_executor.set_mock_llm_call(mock_function)
        self.assertEqual(self.query_executor._mock_llm_call, mock_function)

        # Test with invalid type
        with self.assertRaises(LLMError):
            self.query_executor.set_mock_llm_call(123)  # type: ignore

    async def test_mock_llm_query(self):
        """Test mock LLM query functionality."""
        request = {"messages": [{"role": "user", "content": "Hello, how are you?"}]}

        response = await self.query_executor.mock_llm_query(request)

        self.assertIn("choices", response)
        self.assertEqual(len(response["choices"]), 1)
        self.assertEqual(response["choices"][0]["message"]["role"], "assistant")
        self.assertIn(
            "This is a mock response. In a real scenario, I would provide a thoughtful answer to: Hello, how are you?",
            response["choices"][0]["message"]["content"],
        )
        self.assertEqual(response["model"], "mock-model")

    async def test_mock_llm_query_no_messages(self):
        """Test mock LLM query with no messages."""
        request = {"messages": []}

        with self.assertRaises(LLMError) as context:
            await self.query_executor.mock_llm_query(request)

        self.assertIn("must be provided and non-empty", str(context.exception))

    async def test_mock_llm_query_no_user_messages(self):
        """Test mock LLM query with no user messages."""
        request = {"messages": [{"role": "system", "content": "You are a helpful assistant."}]}

        with self.assertRaises(LLMError) as context:
            await self.query_executor.mock_llm_query(request)

        self.assertIn("No user message found", str(context.exception))

    def test_build_default_request_params(self):
        """Test building default request parameters."""
        request = {"messages": [{"role": "user", "content": "test"}], "temperature": 0.8, "max_tokens": 100}

        self.query_executor.model = "openai:gpt-4"
        params = self.query_executor._build_default_request_params(request)

        self.assertEqual(params["messages"], request["messages"])
        self.assertEqual(params["temperature"], 0.8)
        self.assertEqual(params["max_tokens"], 100)
        self.assertEqual(params["model"], "openai:gpt-4")

    def test_build_default_request_params_defaults(self):
        """Test building default request parameters with defaults."""
        request = {"messages": []}

        params = self.query_executor._build_default_request_params(request)

        self.assertEqual(params["temperature"], 0.7)  # Default temperature
        self.assertNotIn("max_tokens", params)  # Default max_tokens should not be set
        self.assertIsNone(params["model"])  # No model set

    async def test_query_once_no_client(self):
        """Test query_once with no client."""
        # Temporarily disable mock mode for this test
        original_mock = os.environ.get("DANA_MOCK_LLM")
        os.environ["DANA_MOCK_LLM"] = "false"

        try:
            request = {"messages": [{"role": "user", "content": "test"}]}

            with self.assertRaises(LLMError) as context:
                await self.query_executor.query_once(request)

            self.assertIn("LLM client not initialized", str(context.exception))
        finally:
            # Restore original mock setting
            if original_mock is None:
                os.environ.pop("DANA_MOCK_LLM", None)
            else:
                os.environ["DANA_MOCK_LLM"] = original_mock

    async def test_query_once_no_model(self):
        """Test query_once with no model."""
        # Temporarily disable mock mode for this test
        original_mock = os.environ.get("DANA_MOCK_LLM")
        os.environ["DANA_MOCK_LLM"] = "false"

        try:
            self.query_executor.client = MagicMock()
            request = {"messages": [{"role": "user", "content": "test"}]}

            with self.assertRaises(LLMError) as context:
                await self.query_executor.query_once(request)

            self.assertIn("No LLM model specified", str(context.exception))
        finally:
            # Restore original mock setting
            if original_mock is None:
                os.environ.pop("DANA_MOCK_LLM", None)
            else:
                os.environ["DANA_MOCK_LLM"] = original_mock

    async def test_query_once_no_messages(self):
        """Test query_once with no messages."""
        self.query_executor.client = MagicMock()
        self.query_executor.model = "openai:gpt-4"
        request = {}

        with self.assertRaises(LLMError) as context:
            await self.query_executor.query_once(request)

        self.assertIn("must be provided and non-empty", str(context.exception))

    async def test_query_once_with_mock_function(self):
        """Test query_once with mock function."""
        mock_function = AsyncMock(return_value={"test": "response"})
        self.query_executor.set_mock_llm_call(mock_function)

        request = {"messages": [{"role": "user", "content": "test"}]}
        response = await self.query_executor.query_once(request)

        self.assertEqual(response, {"test": "response"})
        mock_function.assert_called_once_with(request)

    async def test_query_once_with_mock_boolean(self):
        """Test query_once with mock boolean."""
        self.query_executor.set_mock_llm_call(True)

        request = {"messages": [{"role": "user", "content": "test"}]}
        response = await self.query_executor.query_once(request)

        self.assertIn("choices", response)
        self.assertEqual(response["model"], "mock-model")

    async def test_query_once_with_env_mock(self):
        """Test query_once with environment variable mock."""
        request = {"messages": [{"role": "user", "content": "test"}]}
        response = await self.query_executor.query_once(request)

        self.assertIn("choices", response)
        self.assertEqual(response["model"], "mock-model")

    async def test_query_once_success(self):
        """Test successful query_once execution."""
        # Temporarily disable mock mode for this test
        original_mock = os.environ.get("DANA_MOCK_LLM")
        os.environ["DANA_MOCK_LLM"] = "false"

        try:
            # Set up mock client (aisuite is synchronous)
            mock_client = MagicMock()
            mock_response_dict = {
                "choices": [{"message": {"role": "assistant", "content": "Test response"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "model": "openai:gpt-4",
            }
            # Create a mock object that has a model_dump method
            mock_response_obj = MagicMock()
            mock_response_obj.model_dump.return_value = mock_response_dict

            mock_client.chat.completions.create = MagicMock(return_value=mock_response_obj)

            self.query_executor.client = mock_client
            self.query_executor.model = "openai:gpt-4"

            # Mock build_request_params function
            build_request_params = MagicMock(
                return_value={"messages": [{"role": "user", "content": "test"}], "model": "openai:gpt-4", "temperature": 0.7}
            )

            request = {"messages": [{"role": "user", "content": "test"}]}
            response = await self.query_executor.query_once(request, build_request_params)

            self.assertEqual(response, mock_response_dict)
            mock_client.chat.completions.create.assert_called_once()
            build_request_params.assert_called_once_with(request)
        finally:
            # Restore original mock setting
            if original_mock is None:
                os.environ.pop("DANA_MOCK_LLM", None)
            else:
                os.environ["DANA_MOCK_LLM"] = original_mock

    async def test_query_iterative_basic(self):
        """Test basic query_iterative functionality."""
        # Set up mock tool call handler and build params
        mock_tool_handler = AsyncMock(return_value=[])
        mock_build_params = MagicMock(return_value={"messages": [], "model": "openai:gpt-4", "temperature": 0.7})

        # Mock query_once to return a response without tool calls
        mock_response = {
            "choices": [{"message": {"role": "assistant", "content": "Test response", "tool_calls": None}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "model": "openai:gpt-4",
        }

        # Use patch to properly mock the query_once method
        with patch.object(self.query_executor, "query_once", new_callable=AsyncMock) as mock_query_once:
            mock_query_once.return_value = mock_response

            self.query_executor.query_strategy = QueryStrategy.ITERATIVE
            self.query_executor.query_max_iterations = 3

            request = {"user_messages": [{"role": "user", "content": "Hello"}], "available_resources": {}}

            response = await self.query_executor.query_iterative(request, mock_tool_handler, mock_build_params)

            # The query_iterative method transforms the response, so we expect the transformed format
            # Since mock_response is a dict (not BaseResponse), it gets transformed
            expected_response = {
                "choices": mock_response["choices"],
                "usage": mock_response["usage"],
                "model": mock_response["model"],
            }

            self.assertEqual(response, expected_response)
            mock_query_once.assert_called_once()

    async def test_query_iterative_with_tool_calls(self):
        """Test query_iterative with tool calls."""
        # Set up mock tool call handler
        mock_tool_handler = AsyncMock(return_value=[{"role": "tool", "content": "Tool response", "tool_call_id": "test_id"}])

        mock_build_params = MagicMock(return_value={"messages": [], "model": "openai:gpt-4", "temperature": 0.7})

        # Mock query_once to return responses with and without tool calls
        response_with_tools = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I'll use a tool",
                        "tool_calls": [{"id": "test_id", "type": "function", "function": {"name": "test_tool"}}],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "model": "openai:gpt-4",
        }

        response_final = {
            "choices": [{"message": {"role": "assistant", "content": "Final response", "tool_calls": None}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "model": "openai:gpt-4",
        }

        # Use patch to properly mock the query_once method
        with patch.object(self.query_executor, "query_once", new_callable=AsyncMock) as mock_query_once:
            mock_query_once.side_effect = [response_with_tools, response_final]

            self.query_executor.query_strategy = QueryStrategy.ITERATIVE
            self.query_executor.query_max_iterations = 3

            request = {"user_messages": [{"role": "user", "content": "Hello"}], "available_resources": {"test_resource": MagicMock()}}

            # Mock resource registry methods
            for resource in request["available_resources"].values():
                resource.add_to_registry = MagicMock()
                resource.remove_from_registry = MagicMock()

            response = await self.query_executor.query_iterative(request, mock_tool_handler, mock_build_params)

            # The query_iterative method transforms the response, so we expect the transformed format
            # Since response_final is a dict (not BaseResponse), it gets transformed
            expected_response = {
                "choices": response_final["choices"],
                "usage": response_final["usage"],
                "model": response_final["model"],
            }

            self.assertEqual(response, expected_response)
            self.assertEqual(mock_query_once.call_count, 2)
            mock_tool_handler.assert_called_once()

    async def test_query_iterative_max_iterations(self):
        """Test query_iterative reaching max iterations."""
        mock_tool_handler = AsyncMock(return_value=[{"role": "tool", "content": "Tool response", "tool_call_id": "test_id"}])

        mock_build_params = MagicMock(return_value={"messages": [], "model": "openai:gpt-4", "temperature": 0.7})

        # Always return a response with tool calls
        response_with_tools = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I'll use a tool",
                        "tool_calls": [{"id": "test_id", "type": "function", "function": {"name": "test_tool"}}],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "model": "openai:gpt-4",
        }

        self.query_executor.query_once = AsyncMock(return_value=response_with_tools)
        self.query_executor.query_strategy = QueryStrategy.ITERATIVE
        self.query_executor.query_max_iterations = 2

        request = {"user_messages": [{"role": "user", "content": "Hello"}], "available_resources": {"test_resource": MagicMock()}}

        # Mock resource registry methods
        for resource in request["available_resources"].values():
            resource.add_to_registry = MagicMock()
            resource.remove_from_registry = MagicMock()

        await self.query_executor.query_iterative(request, mock_tool_handler, mock_build_params)

        # Should have called query_once exactly max_iterations times
        self.assertEqual(self.query_executor.query_once.call_count, 2)


class TestLLMQueryExecutorIntegration(unittest.TestCase):
    """Integration tests for LLMQueryExecutor."""

    def test_logging_inheritance(self):
        """Test that query executor properly inherits logging."""
        query_executor = LLMQueryExecutor()

        # Should have logging methods from Loggable mixin
        self.assertTrue(hasattr(query_executor, "warning"))
        self.assertTrue(hasattr(query_executor, "error"))
        self.assertTrue(hasattr(query_executor, "debug"))
        self.assertTrue(hasattr(query_executor, "info"))


class TestLLMQueryExecutorAnthropicIntegration(unittest.TestCase):
    """Integration tests for Anthropic-specific functionality in LLMQueryExecutor."""

    def setUp(self):
        """Set up test environment."""
        self.executor = LLMQueryExecutor(model="anthropic:claude-3-5-sonnet-20240620")

    @patch("aisuite.Client")
    def test_anthropic_system_message_transformation_in_query_executor(self, mock_client_class):
        """Test that LLMQueryExecutor preserves system messages for AISuite to handle."""
        # Temporarily disable mock mode for this test
        original_mock = os.environ.get("DANA_MOCK_LLM")
        os.environ["DANA_MOCK_LLM"] = "false"

        try:
            # Mock AISuite client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Mock response with proper model_dump method
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.choices[0].message.role = "assistant"
            mock_response.choices[0].message.tool_calls = None
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.model = "claude-3-5-sonnet-20240620"

            # Properly mock the model_dump method that's called in query_once
            mock_response.model_dump.return_value = {
                "choices": [{"message": {"content": "Test response", "role": "assistant"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "model": "claude-3-5-sonnet-20240620",
            }

            # Since query_once calls .create synchronously, not async
            mock_client.chat.completions.create = MagicMock(return_value=mock_response)
            self.executor.client = mock_client
            self.executor._is_initialized = True  # Mark as initialized to skip auto-init
            self.executor._mock_llm_call = None  # Disable mock to use our mocked client

            # Create request with system messages
            request = {
                "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "what is pi?"}],
                "temperature": 0.7,
            }

            # Execute query
            _result = Misc.safe_asyncio_run(self.executor.query_once, request)

            # Verify the call was made
            self.assertTrue(mock_client.chat.completions.create.called)
            call_args = mock_client.chat.completions.create.call_args
            request_params = call_args.kwargs if call_args.kwargs else call_args.args[0]

            # Verify system messages remain in messages array for AISuite to handle
            messages = request_params.get("messages", [])
            system_messages_in_array = [msg for msg in messages if msg.get("role") == "system"]

            # System messages should remain for AISuite to transform automatically
            self.assertEqual(len(system_messages_in_array), 1, "System messages should remain in messages array for AISuite to handle")
            self.assertEqual(system_messages_in_array[0]["content"], "You are a helpful assistant.")

            # Verify NO manual system parameter is created (prevents conflicts)
            self.assertNotIn("system", request_params, "No manual system parameter should be created to avoid conflicts with AISuite")

            # Verify user message is preserved
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            self.assertEqual(len(user_messages), 1)
            self.assertEqual(user_messages[0]["content"], "what is pi?")
        finally:
            # Restore original mock setting
            if original_mock is None:
                os.environ.pop("DANA_MOCK_LLM", None)
            else:
                os.environ["DANA_MOCK_LLM"] = original_mock

    def test_build_default_request_params_anthropic_system_transformation(self):
        """Test that _build_default_request_params preserves system messages for AISuite to handle."""
        # Set up executor with Anthropic model
        executor = LLMQueryExecutor(model="anthropic:claude-3-5-sonnet-20240620")

        # Create request with system messages
        request = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "system", "content": "Always be accurate."},
                {"role": "user", "content": "test question"},
            ],
            "temperature": 0.7,
        }

        # Call the method that should preserve messages for AISuite
        result_params = executor._build_default_request_params(request)

        # Verify NO manual system parameter is created (AISuite handles this)
        self.assertNotIn("system", result_params, "No manual system parameter should be created")

        # Verify system messages remain in messages array for AISuite to transform
        messages = result_params.get("messages", [])
        system_in_messages = [msg for msg in messages if msg.get("role") == "system"]
        self.assertEqual(len(system_in_messages), 2, "System messages should remain in messages array for AISuite")
        self.assertEqual(system_in_messages[0]["content"], "You are a helpful assistant.")
        self.assertEqual(system_in_messages[1]["content"], "Always be accurate.")

        # Verify user message is preserved
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        self.assertEqual(len(user_messages), 1)

    def test_build_default_request_params_openai_unchanged(self):
        """Test that OpenAI models don't get system message transformation."""
        # Set up executor with OpenAI model
        executor = LLMQueryExecutor(model="openai:gpt-4")

        # Create request with system messages
        request = {
            "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "test question"}],
            "temperature": 0.7,
        }

        # Call the method
        result_params = executor._build_default_request_params(request)

        # For OpenAI, system messages should remain in messages array
        messages = result_params.get("messages", [])
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        self.assertEqual(len(system_messages), 1)

        # Should NOT have top-level system parameter
        self.assertNotIn("system", result_params)

    def test_build_default_request_params_vllm_unchanged(self):
        """Test that vLLM models don't get system message transformation."""
        # Set up executor with vLLM model (should be treated like OpenAI)
        executor = LLMQueryExecutor(model="vllm:llama3.2")

        # Create request with system messages
        request = {
            "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "test question"}],
            "temperature": 0.7,
        }

        # Call the method
        result_params = executor._build_default_request_params(request)

        # Check that vLLM translation happened correctly
        self.assertEqual(result_params["model"], "openai:llama3.2")

        # For vLLM (OpenAI-compatible), system messages should remain in messages array
        messages = result_params.get("messages", [])
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        self.assertEqual(len(system_messages), 1)

        # Should NOT have top-level system parameter for vLLM
        self.assertNotIn("system", result_params)

    def test_anthropic_system_message_edge_cases_in_query_executor(self):
        """Test edge cases for Anthropic system message transformation in query executor."""
        executor = LLMQueryExecutor(model="anthropic:claude-3-5-sonnet-20240620")

        # Test with empty system message
        request = {"messages": [{"role": "system", "content": ""}, {"role": "user", "content": "test"}]}

        result_params = executor._build_default_request_params(request)

        # Empty system messages should be excluded
        self.assertNotIn("system", result_params)

        # Test with only user messages (no system messages)
        request = {"messages": [{"role": "user", "content": "test"}]}

        result_params = executor._build_default_request_params(request)

        # Should not have system parameter
        self.assertNotIn("system", result_params)

        # Should preserve user message
        messages = result_params.get("messages", [])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")


class TestLLMQueryExecutorRetryLogic(unittest.TestCase):
    """Test retry logic in LLMQueryExecutor."""

    def setUp(self):
        """Set up test fixtures."""
        self.query_executor = LLMQueryExecutor(max_retry_attempts=2, retry_backoff_base=2.0, retry_jitter=0.5)

    def test_retry_initialization(self):
        """Test retry parameters initialization."""
        executor = LLMQueryExecutor(max_retry_attempts=3, retry_backoff_base=1.5, retry_jitter=0.2)
        self.assertEqual(executor._max_retry_attempts, 3)
        self.assertEqual(executor._retry_backoff_base, 1.5)
        self.assertEqual(executor._retry_jitter, 0.2)

        # Test defaults
        default_executor = LLMQueryExecutor()
        self.assertEqual(default_executor._max_retry_attempts, 2)
        self.assertEqual(default_executor._retry_backoff_base, 2.0)
        self.assertEqual(default_executor._retry_jitter, 0.5)

    def test_is_retryable_error_rate_limit(self):
        """Test _is_retryable_error with rate limit errors."""
        # Test various rate limit error messages
        rate_limit_errors = [
            Exception("Rate limit exceeded"),
            Exception("rate_limit error"),
            Exception("HTTP 429 Too Many Requests"),
            Exception("429 error occurred"),
            Exception("Too many requests"),
        ]

        for error in rate_limit_errors:
            self.assertTrue(
                self.query_executor._is_retryable_error(error),
                f"Should retry on: {error}",
            )

    def test_is_retryable_error_timeout(self):
        """Test _is_retryable_error with timeout errors."""
        timeout_errors = [
            Exception("Request timeout"),
            Exception("Timed out"),
            Exception("Deadline exceeded"),
            Exception("Connection timedout"),
        ]

        for error in timeout_errors:
            self.assertTrue(
                self.query_executor._is_retryable_error(error),
                f"Should retry on: {error}",
            )

    def test_is_retryable_error_server_errors(self):
        """Test _is_retryable_error with server errors."""
        server_errors = [
            Exception("HTTP 500 Internal Server Error"),
            Exception("502 Bad Gateway"),
            Exception("503 Service Unavailable"),
            Exception("504 Gateway Timeout"),
            Exception("Server error occurred"),
            Exception("Internal error"),
        ]

        for error in server_errors:
            self.assertTrue(
                self.query_executor._is_retryable_error(error),
                f"Should retry on: {error}",
            )

    def test_is_retryable_error_connection_errors(self):
        """Test _is_retryable_error with connection errors."""
        connection_errors = [
            Exception("Connection refused"),
            Exception("Network error"),
            Exception("Connection reset"),
            Exception("Unable to connect"),
            Exception("Connection unreachable"),
        ]

        for error in connection_errors:
            self.assertTrue(
                self.query_executor._is_retryable_error(error),
                f"Should retry on: {error}",
            )

    def test_is_retryable_error_non_retryable(self):
        """Test _is_retryable_error with non-retryable errors."""
        non_retryable_errors = [
            Exception("Authentication failed"),
            Exception("Invalid API key"),
            Exception("Bad request"),
            Exception("Not found"),
            Exception("Permission denied"),
            Exception("Some other error"),
        ]

        for error in non_retryable_errors:
            self.assertFalse(
                self.query_executor._is_retryable_error(error),
                f"Should NOT retry on: {error}",
            )

    def test_raise_classified_error_rate_limit(self):
        """Test _raise_classified_error with rate limit errors."""
        error = Exception("Rate limit exceeded (429)")

        with self.assertRaises(LLMRateLimitError) as context:
            self.query_executor._raise_classified_error(error)

        self.assertIn("rate limit", str(context.exception).lower())

    def test_raise_classified_error_authentication(self):
        """Test _raise_classified_error with authentication errors."""
        error = Exception("Authentication failed (401)")

        with self.assertRaises(LLMAuthenticationError) as context:
            self.query_executor._raise_classified_error(error)

        self.assertIn("authentication", str(context.exception).lower())

    def test_raise_classified_error_context_length(self):
        """Test _raise_classified_error with context length errors."""
        error = Exception("Context length exceeded (400)")

        with self.assertRaises(LLMContextLengthError) as context:
            self.query_executor._raise_classified_error(error)

        self.assertIn("context", str(context.exception).lower())

    def test_raise_classified_error_generic(self):
        """Test _raise_classified_error with generic errors."""
        error = Exception("Some unknown error")

        with self.assertRaises(LLMError):
            self.query_executor._raise_classified_error(error)

    def test_raise_classified_error_none(self):
        """Test _raise_classified_error with None error."""
        with self.assertRaises(LLMError) as context:
            self.query_executor._raise_classified_error(None)

        self.assertIn("Unknown error", str(context.exception))

    @patch("asyncio.sleep")
    @patch("asyncio.to_thread")
    async def test_execute_with_retry_success_first_attempt(self, mock_to_thread, mock_sleep):
        """Test _execute_with_retry succeeds on first attempt."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Success"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "model": "openai:gpt-4",
        }

        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        self.query_executor._client = mock_client
        self.query_executor.model = "openai:gpt-4"

        request_params = {
            "model": "openai:gpt-4",
            "messages": [{"role": "user", "content": "test"}],
        }

        result = await self.query_executor._execute_with_retry(request_params)

        self.assertEqual(result["model"], "openai:gpt-4")
        mock_to_thread.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("asyncio.sleep")
    @patch("asyncio.to_thread")
    async def test_execute_with_retry_succeeds_after_retry(self, mock_to_thread, mock_sleep):
        """Test _execute_with_retry succeeds after retry."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Success"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "model": "openai:gpt-4",
        }

        # First call fails with retryable error, second succeeds
        mock_to_thread.side_effect = [
            Exception("Rate limit exceeded"),
            mock_response,
        ]

        self.query_executor._client = mock_client
        self.query_executor.model = "openai:gpt-4"
        self.query_executor._max_retry_attempts = 2

        request_params = {
            "model": "openai:gpt-4",
            "messages": [{"role": "user", "content": "test"}],
        }

        result = await self.query_executor._execute_with_retry(request_params)

        self.assertEqual(result["model"], "openai:gpt-4")
        self.assertEqual(mock_to_thread.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("asyncio.sleep")
    @patch("asyncio.to_thread")
    async def test_execute_with_retry_exhausts_retries(self, mock_to_thread, mock_sleep):
        """Test _execute_with_retry exhausts retries and raises error."""
        mock_client = MagicMock()

        # All attempts fail with retryable error
        mock_to_thread.side_effect = Exception("Rate limit exceeded")

        self.query_executor._client = mock_client
        self.query_executor.model = "openai:gpt-4"
        self.query_executor._max_retry_attempts = 2

        request_params = {
            "model": "openai:gpt-4",
            "messages": [{"role": "user", "content": "test"}],
        }

        with self.assertRaises(LLMRateLimitError):
            await self.query_executor._execute_with_retry(request_params)

        # Should attempt max_retry_attempts + 1 times (initial + retries)
        self.assertEqual(mock_to_thread.call_count, 3)
        # Should sleep max_retry_attempts times
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("asyncio.sleep")
    @patch("asyncio.to_thread")
    async def test_execute_with_retry_non_retryable_error(self, mock_to_thread, mock_sleep):
        """Test _execute_with_retry does not retry non-retryable errors."""
        mock_client = MagicMock()

        # Non-retryable error
        mock_to_thread.side_effect = Exception("Authentication failed")

        self.query_executor._client = mock_client
        self.query_executor.model = "openai:gpt-4"
        self.query_executor._max_retry_attempts = 2

        request_params = {
            "model": "openai:gpt-4",
            "messages": [{"role": "user", "content": "test"}],
        }

        with self.assertRaises(LLMAuthenticationError):
            await self.query_executor._execute_with_retry(request_params)

        # Should only attempt once (no retries for non-retryable errors)
        self.assertEqual(mock_to_thread.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("asyncio.sleep")
    @patch("asyncio.to_thread")
    async def test_execute_with_retry_no_client(self, mock_to_thread, mock_sleep):
        """Test _execute_with_retry raises error when client is None."""
        self.query_executor._client = None

        request_params = {
            "model": "openai:gpt-4",
            "messages": [{"role": "user", "content": "test"}],
        }

        with self.assertRaises(LLMError) as context:
            await self.query_executor._execute_with_retry(request_params)

        self.assertIn("not initialized", str(context.exception))
        mock_to_thread.assert_not_called()
        mock_sleep.assert_not_called()


class TestLLMQueryExecutorSemaphore(unittest.IsolatedAsyncioTestCase):
    """Test semaphore functionality in LLMQueryExecutor."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset semaphore state before each test
        # Handle both old and new implementation
        if hasattr(LLMQueryExecutor, "_global_llm_semaphore"):
            LLMQueryExecutor._global_llm_semaphore = None
        if hasattr(LLMQueryExecutor, "_semaphores_by_loop"):
            LLMQueryExecutor._semaphores_by_loop = {}
        LLMQueryExecutor._max_concurrent_requests = 3
        # Clear environment variable if set
        if "DANA_LLM_MAX_CONCURRENT_REQUESTS" in os.environ:
            del os.environ["DANA_LLM_MAX_CONCURRENT_REQUESTS"]

    def tearDown(self):
        """Clean up after each test."""
        # Reset semaphore state after each test
        # Handle both old and new implementation
        if hasattr(LLMQueryExecutor, "_global_llm_semaphore"):
            LLMQueryExecutor._global_llm_semaphore = None
        if hasattr(LLMQueryExecutor, "_semaphores_by_loop"):
            LLMQueryExecutor._semaphores_by_loop = {}
        LLMQueryExecutor._max_concurrent_requests = 3
        # Clear environment variable if set
        if "DANA_LLM_MAX_CONCURRENT_REQUESTS" in os.environ:
            del os.environ["DANA_LLM_MAX_CONCURRENT_REQUESTS"]

    def test_semaphore_initialization_default_limit(self):
        """Test semaphore initialization with default limit."""
        # Semaphore dictionary should be empty initially
        if hasattr(LLMQueryExecutor, "_semaphores_by_loop"):
            self.assertEqual(len(LLMQueryExecutor._semaphores_by_loop), 0)
        elif hasattr(LLMQueryExecutor, "_global_llm_semaphore"):
            self.assertIsNone(LLMQueryExecutor._global_llm_semaphore)
        self.assertEqual(LLMQueryExecutor._max_concurrent_requests, 3)

        # Access semaphore - should create it (but only works in async context)
        # This test will need to be async or use asyncio.run()
        async def test_async():
            semaphore = LLMQueryExecutor._get_global_semaphore()
            self.assertIsNotNone(semaphore)
            self.assertIsInstance(semaphore, asyncio.Semaphore)
            self.assertEqual(semaphore._value, 3)

        asyncio.run(test_async())

    async def test_semaphore_shared_across_instances(self):
        """Test semaphore is shared for same event loop."""
        # Both should get the same semaphore instance for same loop
        semaphore1 = LLMQueryExecutor._get_global_semaphore()
        semaphore2 = LLMQueryExecutor._get_global_semaphore()

        self.assertIs(semaphore1, semaphore2)
        # Check that it's stored in the dictionary
        if hasattr(LLMQueryExecutor, "_semaphores_by_loop"):
            loop_id = id(asyncio.get_running_loop())
            self.assertIn(loop_id, LLMQueryExecutor._semaphores_by_loop)
            self.assertIs(LLMQueryExecutor._semaphores_by_loop[loop_id], semaphore1)

    @patch.dict(os.environ, {"DANA_LLM_MAX_CONCURRENT_REQUESTS": "5"})
    async def test_semaphore_env_var_configuration(self):
        """Test semaphore reads from environment variable."""
        # Reset semaphore to pick up env var
        if hasattr(LLMQueryExecutor, "_semaphores_by_loop"):
            LLMQueryExecutor._semaphores_by_loop = {}
        elif hasattr(LLMQueryExecutor, "_global_llm_semaphore"):
            LLMQueryExecutor._global_llm_semaphore = None

        semaphore = LLMQueryExecutor._get_global_semaphore()
        self.assertEqual(semaphore._value, 5)
        self.assertEqual(LLMQueryExecutor._max_concurrent_requests, 5)

    @patch.dict(os.environ, {"DANA_LLM_MAX_CONCURRENT_REQUESTS": "invalid"})
    async def test_semaphore_env_var_invalid_fallback(self):
        """Test semaphore falls back to default on invalid env var."""
        # Reset semaphore
        if hasattr(LLMQueryExecutor, "_semaphores_by_loop"):
            LLMQueryExecutor._semaphores_by_loop = {}
        elif hasattr(LLMQueryExecutor, "_global_llm_semaphore"):
            LLMQueryExecutor._global_llm_semaphore = None
        LLMQueryExecutor._max_concurrent_requests = 3

        semaphore = LLMQueryExecutor._get_global_semaphore()
        # Should use default (3) when env var is invalid
        self.assertEqual(semaphore._value, 3)

    async def test_set_max_concurrent_requests(self):
        """Test set_max_concurrent_requests class method."""
        # Create initial semaphore with default limit
        semaphore1 = LLMQueryExecutor._get_global_semaphore()
        self.assertEqual(semaphore1._value, 3)

        # Set new limit
        LLMQueryExecutor.set_max_concurrent_requests(5)

        # Semaphore should be recreated with new limit
        semaphore2 = LLMQueryExecutor._get_global_semaphore()
        self.assertIsNot(semaphore1, semaphore2)  # Should be new instance
        self.assertEqual(semaphore2._value, 5)
        self.assertEqual(LLMQueryExecutor._max_concurrent_requests, 5)

    @patch("asyncio.to_thread")
    async def test_semaphore_limits_concurrency(self, mock_to_thread):
        """CRITICAL: Verify semaphore actually limits concurrent requests."""
        # Set semaphore limit to 2
        LLMQueryExecutor.set_max_concurrent_requests(2)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Success"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "model": "openai:gpt-4",
        }

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        execution_lock = asyncio.Lock()

        async def delayed_response():
            """Simulate API call with delay and tracking."""
            nonlocal concurrent_count, max_concurrent
            async with execution_lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

            # Simulate API delay
            await asyncio.sleep(0.05)

            async with execution_lock:
                concurrent_count -= 1

            return mock_response

        mock_to_thread.return_value = delayed_response()

        executor = LLMQueryExecutor()
        executor._client = mock_client
        executor.model = "openai:gpt-4"
        executor._max_retry_attempts = 0  # No retries for this test

        request_params = {
            "model": "openai:gpt-4",
            "messages": [{"role": "user", "content": "test"}],
        }

        # Create 5 concurrent requests
        tasks = [executor._execute_with_retry(request_params) for _ in range(5)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all requests completed successfully
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertNotIsInstance(result, Exception)

        # CRITICAL: Verify semaphore limited concurrency to 2
        # max_concurrent should be at most 2 (the semaphore limit)
        msg = f"Semaphore should limit to 2 concurrent, but saw {max_concurrent}"
        self.assertLessEqual(max_concurrent, 2, msg)

    @patch("asyncio.sleep")
    @patch("asyncio.to_thread")
    async def test_semaphore_with_retry_logic(self, mock_to_thread, mock_sleep):
        """Test semaphore is held during entire retry loop."""
        LLMQueryExecutor.set_max_concurrent_requests(2)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Success"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "model": "openai:gpt-4",
        }

        # Track concurrent executions during retries
        concurrent_count = 0
        max_concurrent = 0
        execution_lock = asyncio.Lock()
        call_count = 0

        async def delayed_response_with_retry():
            """Simulate API call that fails once then succeeds."""
            nonlocal concurrent_count, max_concurrent, call_count
            call_count += 1

            async with execution_lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

            # First call fails, subsequent succeed
            if call_count <= 1:
                await asyncio.sleep(0.01)
                async with execution_lock:
                    concurrent_count -= 1
                raise Exception("Rate limit exceeded")

            await asyncio.sleep(0.01)
            async with execution_lock:
                concurrent_count -= 1

            return mock_response

        mock_to_thread.return_value = delayed_response_with_retry()

        executor = LLMQueryExecutor()
        executor._client = mock_client
        executor.model = "openai:gpt-4"
        executor._max_retry_attempts = 1

        request_params = {
            "model": "openai:gpt-4",
            "messages": [{"role": "user", "content": "test"}],
        }

        # Create 3 concurrent requests (limit is 2)
        tasks = [executor._execute_with_retry(request_params) for _ in range(3)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify requests completed (with retries)
        self.assertEqual(len(results), 3)
        # Verify semaphore limited concurrency during retries
        # max_concurrent should be at most 2 (the semaphore limit)
        msg = f"Semaphore should limit to 2 concurrent during retries, " f"but saw {max_concurrent}"
        self.assertLessEqual(max_concurrent, 2, msg)

    @patch("asyncio.to_thread")
    async def test_semaphore_with_mock_llm_calls(self, mock_to_thread):
        """Test semaphore behavior with mock LLM calls."""
        LLMQueryExecutor.set_max_concurrent_requests(2)

        executor = LLMQueryExecutor()
        executor.set_mock_llm_call(True)

        request = {"messages": [{"role": "user", "content": "test"}]}

        # Mock calls should not go through semaphore (they bypass _execute_with_retry)
        # But if they do, verify semaphore still works
        results = await asyncio.gather(*[executor.query_once(request) for _ in range(3)], return_exceptions=True)

        # All mock calls should succeed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertNotIsInstance(result, Exception)
            if isinstance(result, dict):
                self.assertIn("choices", result)

    @patch("asyncio.to_thread")
    def test_semaphore_works_across_multiple_threads(self, mock_to_thread):
        """CRITICAL: Test semaphore works when multiple threads create their own event loops."""
        # Set semaphore limit
        LLMQueryExecutor.set_max_concurrent_requests(3)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Success"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "model": "openai:gpt-4",
        }

        mock_to_thread.return_value = mock_response

        request_params = {
            "model": "openai:gpt-4",
            "messages": [{"role": "user", "content": "test"}],
        }

        results = []
        errors = []
        errors_lock = threading.Lock()

        def worker_thread(thread_id: int):
            """Worker thread that creates its own event loop."""

            # This simulates what safe_asyncio_run does
            async def run_query():
                executor = LLMQueryExecutor()
                executor._client = mock_client
                executor.model = "openai:gpt-4"
                executor._max_retry_attempts = 0  # No retries for this test
                return await executor._execute_with_retry(request_params)

            try:
                # Create new event loop in this thread (simulates safe_asyncio_run)
                result = asyncio.run(run_query())
                results.append(result)
            except Exception as e:
                with errors_lock:
                    errors.append((thread_id, str(e), type(e).__name__))

        # Create 5 threads, each with its own event loop
        threads = [Thread(target=worker_thread, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)  # Timeout to prevent hanging

        # Verify no "bound to different event loop" errors
        bound_to_different_loop_errors = [e for e in errors if "bound to a different event loop" in str(e[1])]
        self.assertEqual(
            len(bound_to_different_loop_errors),
            0,
            f"Found 'bound to different event loop' errors: {bound_to_different_loop_errors}",
        )

        # Verify all threads succeeded
        self.assertEqual(len(results), 5, f"Expected 5 results, got {len(results)}. Errors: {errors}")

        # Verify each result is valid
        for result in results:
            self.assertIn("choices", result)
            self.assertEqual(result["model"], "openai:gpt-4")


if __name__ == "__main__":
    unittest.main()
