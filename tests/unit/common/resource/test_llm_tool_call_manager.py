"""Test the LLMToolCallManager class."""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.sys_resource.llm.llm_tool_call_manager import LLMToolCallManager


class MockToolCall:
    """Mock tool call for testing."""

    def __init__(self, function_name: str, arguments: dict, call_id: str = "test_id"):
        self.function = MagicMock()
        self.function.name = function_name
        self.function.arguments = json.dumps(arguments)
        self.id = call_id


class MockResource(BaseSysResource):
    """Mock resource for testing."""

    def __init__(self, name: str):
        super().__init__(name)
        self.call_tool = AsyncMock(return_value="mock_response")

    def list_openai_functions(self):
        return [{"type": "function", "function": {"name": f"{self.name}_test_function"}}]


class TestLLMToolCallManager(unittest.IsolatedAsyncioTestCase):
    """Test the LLMToolCallManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool_manager = LLMToolCallManager()

    def test_initialization(self):
        """Test tool call manager initialization."""
        self.assertEqual(self.tool_manager.max_response_length, 40000)

        # Test custom max response length
        custom_manager = LLMToolCallManager(max_response_length=5000)
        self.assertEqual(custom_manager.max_response_length, 5000)

    def test_build_request_params_basic(self):
        """Test basic request parameter building."""
        request = {"messages": [{"role": "user", "content": "test"}], "temperature": 0.8, "max_tokens": 100}

        params = self.tool_manager.build_request_params(request, "openai:gpt-4")

        self.assertEqual(params["messages"], request["messages"])
        self.assertEqual(params["temperature"], 0.8)
        self.assertEqual(params["max_tokens"], 100)
        self.assertEqual(params["model"], "openai:gpt-4")

    def test_build_request_params_with_tools(self):
        """Test request parameter building with tools."""
        request = {"messages": [{"role": "user", "content": "test"}]}
        resources: dict[str, BaseSysResource] = {"test_resource": MockResource("test_resource")}

        params = self.tool_manager.build_request_params(request, "openai:gpt-4", resources)

        self.assertIn("tools", params)
        self.assertIsInstance(params["tools"], list)

    def test_build_request_params_defaults(self):
        """Test building default request parameters with defaults."""
        request = {"messages": []}

        self.tool_manager.model = "test-model"
        params = self.tool_manager.build_request_params(request, model="test-model")

        self.assertEqual(params["temperature"], 0.7)  # Default temperature
        self.assertNotIn("max_tokens", params)  # Default max_tokens should not be set
        self.assertEqual(params["model"], "test-model")

    def test_get_openai_functions(self):
        """Test getting OpenAI functions from resources."""
        resources: dict[str, BaseSysResource] = {"resource1": MockResource("resource1"), "resource2": MockResource("resource2")}

        functions = self.tool_manager.get_openai_functions(resources)

        self.assertEqual(len(functions), 2)
        self.assertIsInstance(functions, list)

    def test_get_openai_functions_empty(self):
        """Test getting OpenAI functions from empty resources."""
        functions = self.tool_manager.get_openai_functions({})
        self.assertEqual(functions, [])

    async def test_call_requested_tools_success(self):
        """Test successful tool calling."""
        with (
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.ToolFormat") as mock_tool_format,
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.Registerable") as mock_registerable,
        ):
            # Setup mocks
            mock_tool_format.parse_tool_name.return_value = ("test_resource", "test_id", "test_tool")
            mock_resource = MockResource("test_resource")
            mock_resource.call_tool.return_value = "mock_response"
            mock_registerable.get_from_registry.return_value = mock_resource

            # Create test tool calls
            tool_calls = [MockToolCall("test_resource__test_id__test_tool", {"param": "value"})]

            # Call the method
            responses = await self.tool_manager.call_requested_tools(tool_calls)  # type: ignore

            # Verify results
            self.assertEqual(len(responses), 1)
            response = responses[0]
            self.assertEqual(response["role"], "tool")
            self.assertEqual(response["name"], "test_resource__test_id__test_tool")
            self.assertEqual(response["content"], "mock_response")
            self.assertEqual(response["tool_call_id"], "test_id")

    async def test_call_requested_tools_resource_not_found(self):
        """Test tool calling when resource is not found."""
        with (
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.ToolFormat") as mock_tool_format,
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.Registerable") as mock_registerable,
        ):
            # Setup mocks
            mock_tool_format.parse_tool_name.return_value = ("test_resource", "test_id", "test_tool")
            mock_registerable.get_from_registry.return_value = None

            # Create test tool calls
            tool_calls = [MockToolCall("test_resource__test_id__test_tool", {"param": "value"})]

            # Call the method
            responses = await self.tool_manager.call_requested_tools(tool_calls)  # type: ignore

            # Should return empty list when resource not found
            self.assertEqual(len(responses), 0)

    async def test_call_requested_tools_error_handling(self):
        """Test tool calling error handling."""
        with (
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.ToolFormat") as mock_tool_format,
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.Registerable") as mock_registerable,
        ):
            # Setup mocks
            mock_tool_format.parse_tool_name.return_value = ("test_resource", "test_id", "test_tool")
            mock_resource = MockResource("test_resource")
            mock_resource.call_tool.side_effect = Exception("Tool call failed")
            mock_registerable.get_from_registry.return_value = mock_resource

            # Create test tool calls
            tool_calls = [MockToolCall("test_resource__test_id__test_tool", {"param": "value"})]

            # Call the method
            responses = await self.tool_manager.call_requested_tools(tool_calls)  # type: ignore

            # Verify error response
            self.assertEqual(len(responses), 1)
            response = responses[0]
            self.assertEqual(response["role"], "tool")
            self.assertIn("Tool call failed", response["content"])

    async def test_call_requested_tools_json_response(self):
        """Test tool calling with JSON response conversion."""
        with (
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.ToolFormat") as mock_tool_format,
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.Registerable") as mock_registerable,
        ):
            # Setup mocks
            mock_tool_format.parse_tool_name.return_value = ("test_resource", "test_id", "test_tool")
            mock_resource = MockResource("test_resource")

            # Mock response with to_json method
            mock_response = MagicMock()
            mock_response.to_json.return_value = '{"result": "success"}'
            mock_resource.call_tool.return_value = mock_response
            mock_registerable.get_from_registry.return_value = mock_resource

            # Create test tool calls
            tool_calls = [MockToolCall("test_resource__test_id__test_tool", {"param": "value"})]

            # Call the method
            responses = await self.tool_manager.call_requested_tools(tool_calls)  # type: ignore

            # Verify JSON conversion
            self.assertEqual(len(responses), 1)
            response = responses[0]
            self.assertEqual(response["content"], '{"result": "success"}')

    async def test_call_requested_tools_response_truncation(self):
        """Test tool response truncation."""
        self.tool_manager.max_response_length = 10

        with (
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.ToolFormat") as mock_tool_format,
            patch("dana.common.sys_resource.llm.llm_tool_call_manager.Registerable") as mock_registerable,
        ):
            # Setup mocks
            mock_tool_format.parse_tool_name.return_value = ("test_resource", "test_id", "test_tool")
            mock_resource = MockResource("test_resource")
            mock_resource.call_tool.return_value = "This is a very long response that should be truncated"
            mock_registerable.get_from_registry.return_value = mock_resource

            # Create test tool calls
            tool_calls = [MockToolCall("test_resource__test_id__test_tool", {"param": "value"})]

            # Call the method
            responses = await self.tool_manager.call_requested_tools(tool_calls)  # type: ignore

            # Verify truncation
            self.assertEqual(len(responses), 1)
            response = responses[0]
            self.assertEqual(len(response["content"]), 10)
            self.assertEqual(response["content"], "This is a ")

    async def test_call_tools_legacy(self):
        """Test legacy tool calling method."""
        tool_calls = [{"name": "test_resource", "arguments": {"param": "value"}}]
        mock_resource = MockResource("test_resource")
        available_resources: list[BaseSysResource] = [mock_resource]

        responses = await self.tool_manager.call_tools_legacy(tool_calls, available_resources)

        self.assertEqual(len(responses), 1)
        # The mock resource.query should have been called
        # This tests the legacy format handling

    async def test_call_tools_legacy_resource_not_found(self):
        """Test legacy tool calling when resource not found."""
        tool_calls = [{"name": "nonexistent_resource", "arguments": {"param": "value"}}]
        available_resources: list[BaseSysResource] = []

        responses = await self.tool_manager.call_tools_legacy(tool_calls, available_resources)

        self.assertEqual(len(responses), 1)
        response = responses[0]
        self.assertFalse(response.success)
        if response.error:
            self.assertIn("not found", response.error)

    def test_format_tool_call_message(self):
        """Test tool call message formatting."""
        response_message = {"role": "assistant", "content": "I'll help you with that.", "other_field": "ignored"}

        tool_call = MagicMock()
        tool_call.model_dump.return_value = {"type": "function", "function": {"name": "test"}}
        tool_calls = [tool_call]

        formatted = self.tool_manager.format_tool_call_message(response_message, tool_calls)  # type: ignore

        self.assertEqual(formatted["role"], "assistant")
        self.assertEqual(formatted["content"], "I'll help you with that.")
        self.assertIn("tool_calls", formatted)
        self.assertEqual(len(formatted["tool_calls"]), 1)

    def test_has_tool_calls_true(self):
        """Test has_tool_calls with valid tool calls."""
        response_message = {"tool_calls": [{"type": "function", "function": {"name": "test"}}]}

        result = self.tool_manager.has_tool_calls(response_message)
        self.assertTrue(result)

    def test_has_tool_calls_false(self):
        """Test has_tool_calls with no tool calls."""
        response_message = {"tool_calls": None}
        result = self.tool_manager.has_tool_calls(response_message)
        self.assertFalse(result)

        response_message = {"tool_calls": []}
        result = self.tool_manager.has_tool_calls(response_message)
        self.assertFalse(result)

        response_message = {}
        result = self.tool_manager.has_tool_calls(response_message)
        self.assertFalse(result)

    def test_register_unregister_resources(self):
        """Test resource registration and unregistration."""
        mock_resource1 = MagicMock()
        mock_resource2 = MagicMock()
        available_resources = {"resource1": mock_resource1, "resource2": mock_resource2}

        # Test registration
        self.tool_manager.register_resources(available_resources)
        mock_resource1.add_to_registry.assert_called_once()
        mock_resource2.add_to_registry.assert_called_once()

        # Test unregistration
        self.tool_manager.unregister_resources(available_resources)
        mock_resource1.remove_from_registry.assert_called_once()
        mock_resource2.remove_from_registry.assert_called_once()


class TestLLMToolCallManagerIntegration(unittest.TestCase):
    """Integration tests for LLMToolCallManager with LLMResource."""

    def test_llm_resource_uses_tool_call_manager(self):
        """Test that LLMResource properly uses LLMToolCallManager."""
        import os

        from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource

        # Set up API key
        previous_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            # Create LLMResource
            llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")

            # Verify tool call manager is created
            self.assertIsNotNone(llm._tool_call_manager)
            self.assertIsInstance(llm._tool_call_manager, LLMToolCallManager)

            # Verify methods delegate to tool call manager
            test_resources = {}
            params = llm._build_request_params({"messages": []}, test_resources)
            self.assertIsInstance(params, dict)

            functions = llm._get_openai_functions(test_resources)
            self.assertIsInstance(functions, list)

        finally:
            # Clean up
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            if previous_key:
                os.environ["OPENAI_API_KEY"] = previous_key

    def test_tool_call_manager_logging(self):
        """Test that tool call manager properly inherits logging."""
        tool_manager = LLMToolCallManager()

        # Should have logging methods from Loggable mixin
        self.assertTrue(hasattr(tool_manager, "warning"))
        self.assertTrue(hasattr(tool_manager, "error"))
        self.assertTrue(hasattr(tool_manager, "debug"))
        self.assertTrue(hasattr(tool_manager, "info"))


if __name__ == "__main__":
    unittest.main()
