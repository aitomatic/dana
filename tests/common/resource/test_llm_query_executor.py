"""Test the LLMQueryExecutor class."""

import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from dana.common.exceptions import LLMError
from dana.common.mixins.queryable import QueryStrategy
from dana.common.resource.llm_query_executor import LLMQueryExecutor
from dana.common.utils.misc import Misc


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

    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "false"})
    async def test_query_once_no_client(self):
        """Test query_once with no client."""
        request = {"messages": [{"role": "user", "content": "test"}]}

        with self.assertRaises(LLMError) as context:
            await self.query_executor.query_once(request)

        self.assertIn("LLM client not initialized", str(context.exception))

    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "false"})
    async def test_query_once_no_model(self):
        """Test query_once with no model."""
        self.query_executor.client = MagicMock()
        request = {"messages": [{"role": "user", "content": "test"}]}

        with self.assertRaises(LLMError) as context:
            await self.query_executor.query_once(request)

        self.assertIn("No LLM model specified", str(context.exception))

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

    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "true"})
    async def test_query_once_with_env_mock(self):
        """Test query_once with environment variable mock."""
        request = {"messages": [{"role": "user", "content": "test"}]}
        response = await self.query_executor.query_once(request)

        self.assertIn("choices", response)
        self.assertEqual(response["model"], "mock-model")

    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "false"})
    async def test_query_once_success(self):
        """Test successful query_once execution."""
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

    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "false"}, clear=False)
    @patch("aisuite.Client")
    def test_anthropic_system_message_transformation_in_query_executor(self, mock_client_class):
        """Test that LLMQueryExecutor preserves system messages for AISuite to handle."""
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
        result = Misc.safe_asyncio_run(self.executor.query_once, request)

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


if __name__ == "__main__":
    unittest.main()
