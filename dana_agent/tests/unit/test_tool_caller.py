"""
Unit tests for ToolCaller and its specialized classes.

Tests the 4-class architecture:
- ToolCaller (main orchestrator)
- ResourceCaller (resource invocation)
- AgentCaller (agent communication)
- WorkflowCaller (workflow execution)
"""

from unittest.mock import Mock, patch

import pytest

from dana.common.llm.types import LLMResponse
from dana.core.agent.components.tool_caller import (
    CodecToolCaller,
    ToolCaller,
    WARCaller,
)
from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec


class TestToolCallerArchitecture:
    """Test the overall 4-class architecture."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = Mock(spec=STARAgent)
        agent.agent_type = "test_agent"
        agent.object_id = "test-agent-123"
        agent.available_resources = []
        agent.available_workflows = []
        agent.available_agents = []
        return agent

    @pytest.fixture
    def tool_caller(self, mock_agent):
        """Create a ToolCaller instance for testing."""
        return ToolCaller(mock_agent)

    def test_tool_caller_initialization(self, tool_caller, mock_agent):
        """Test that ToolCaller initializes correctly."""
        assert tool_caller._agent == mock_agent
        assert isinstance(tool_caller, WARCaller)  # ToolCaller inherits from WARCaller

    def test_tool_caller_has_warcaller_methods(self, tool_caller):
        """Test that ToolCaller has all WARCaller methods."""
        assert hasattr(tool_caller, "execute_resource_call")
        assert hasattr(tool_caller, "execute_workflow_call")
        assert hasattr(tool_caller, "execute_agent_call")
        assert hasattr(tool_caller, "invoke")


class TestToolCallerResourceCalls:
    """Test ToolCaller resource functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with resources."""
        agent = Mock(spec=STARAgent)
        agent.agent_type = "test_agent"
        agent.object_id = "test-agent-123"

        # Create a mock resource
        mock_resource = Mock()
        mock_resource.object_id = "resource-123"
        mock_resource.write = Mock(return_value="Resource method executed successfully")

        agent.available_resources = [mock_resource]
        return agent

    @pytest.fixture
    def tool_caller(self, mock_agent):
        """Create a ToolCaller instance."""
        return ToolCaller(mock_agent)

    def test_execute_resource_call_success(self, tool_caller):
        """Test successful resource call execution."""
        arguments = {"resource_id": "resource-123", "method": "write", "parameters": {"data": "test"}}

        result = tool_caller.execute_resource_call(arguments)

        assert result["success"] is True
        assert result["type"] == "resource"
        assert result["target"] == "resource-123.write"
        assert "Resource method executed successfully" in result["result"]

    def test_execute_resource_call_missing_resource_id(self, tool_caller):
        """Test resource call with missing resource_id."""
        arguments = {"method": "write", "parameters": {"data": "test"}}

        result = tool_caller.execute_resource_call(arguments)

        assert result["success"] is False
        assert result["type"] == "resource"
        assert "Missing resource_id or method" in result["result"]

    def test_execute_resource_call_missing_method(self, tool_caller):
        """Test resource call with missing method."""
        arguments = {"resource_id": "resource-123", "parameters": {"data": "test"}}

        result = tool_caller.execute_resource_call(arguments)

        assert result["success"] is False
        assert result["type"] == "resource"
        assert "Missing resource_id or method" in result["result"]

    def test_execute_resource_call_with_xml_parameters(self, tool_caller):
        """Test resource call with XML parameters that need parsing."""
        arguments = {
            "resource_id": "resource-123",
            "method": "write",
            "parameters": "<todos><todo><content>Test</content><status>pending</status><id>1</id></todo></todos>",
        }

        result = tool_caller.execute_resource_call(arguments)

        assert result["success"] is True
        # The XML should be parsed and passed to the resource method

    def test_invoke_resource_structured_success(self, tool_caller):
        """Test structured resource invocation."""
        result = tool_caller.invoke("resource-123", "write", {"data": "test"}, "resource")

        assert "Resource method executed successfully" in result

    def test_invoke_resource_structured_resource_not_found(self, tool_caller):
        """Test structured resource invocation with non-existent resource."""
        result = tool_caller.invoke("nonexistent-resource", "write", {"data": "test"}, "resource")

        assert "Error: Resource nonexistent-resource not found" in result

    def test_invoke_resource_structured_method_not_found(self, tool_caller):
        """Test structured resource invocation with non-existent method."""
        with patch("builtins.hasattr", return_value=False):
            result = tool_caller.invoke("resource-123", "nonexistent_method", {"data": "test"}, "resource")

        assert "does not have method 'nonexistent_method'" in result


class TestToolCallerAgentCalls:
    """Test ToolCaller agent functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with registry."""
        agent = Mock(spec=STARAgent)
        agent.agent_type = "test_agent"
        agent.object_id = "test-agent-123"

        # Mock registry
        mock_registry = Mock()
        mock_target_agent = Mock()
        mock_target_agent.agent_type = "target_agent"
        mock_target_agent.query = Mock(return_value={"response": "Agent response", "success": True})

        mock_registry.get_agent = Mock(return_value=mock_target_agent)
        mock_registry.get = Mock(return_value=mock_target_agent)
        mock_registry._agents = {"test-agent-123": agent}
        mock_registry._items = {"test-agent-123": agent}

        agent._registry = mock_registry
        agent.ensure_registered = Mock()

        return agent

    @pytest.fixture
    def tool_caller(self, mock_agent):
        """Create a ToolCaller instance."""
        return ToolCaller(mock_agent)

    @patch("dana.core.agent.components.tool_caller.get_debug_logger")
    def test_execute_agent_call_success(self, mock_debug_logger, tool_caller):
        """Test successful agent call execution."""
        arguments = {"object_id": "target-agent-456", "message": "Hello target agent"}

        result = tool_caller.execute_agent_call(arguments)

        assert result["success"] is True
        assert result["type"] == "agent"
        assert result["target"] == "target-agent-456"
        assert "Agent response" in result["result"]

    def test_execute_agent_call_missing_object_id(self, tool_caller):
        """Test agent call with missing object_id."""
        arguments = {"message": "Hello target agent"}

        result = tool_caller.execute_agent_call(arguments)

        assert result["success"] is False
        assert result["type"] == "agent"
        assert "Missing object_id or message" in result["result"]

    def test_execute_agent_call_missing_message(self, tool_caller):
        """Test agent call with missing message."""
        arguments = {
            "object_id": "target-agent-456"
            # message is missing (None)
        }

        result = tool_caller.execute_agent_call(arguments)

        # Should fail validation when message is missing
        assert result["success"] is False
        assert result["type"] == "agent"
        assert "Missing object_id or message" in result["result"]

    def test_execute_agent_call_no_success_field(self, tool_caller):
        """Test agent call when target agent returns response without explicit success field."""
        # Mock the target agent to return a response without success field (like STARAgent does)
        mock_registry = tool_caller._agent._registry
        mock_target_agent = mock_registry.get_agent.return_value
        mock_target_agent.query = Mock(return_value={"response": "Agent response without success field"})

        arguments = {"object_id": "target-agent-456", "message": "Hello target agent"}

        result = tool_caller.execute_agent_call(arguments)

        # Should be successful because there's a response and no error
        assert result["success"] is True
        assert result["type"] == "agent"
        assert "Agent response without success field" in result["result"]


class TestToolCallerWorkflowCalls:
    """Test ToolCaller workflow functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with workflows."""
        agent = Mock(spec=STARAgent)
        agent.agent_type = "test_agent"
        agent.object_id = "test-agent-123"

        # Create a mock workflow
        mock_workflow = Mock()
        mock_workflow.workflow_id = "workflow-123"
        mock_workflow.execute = Mock(return_value={"status": "completed", "result": "workflow executed"})
        mock_workflow.validate = Mock(return_value={"status": "validated", "result": "workflow executed"})

        agent.available_workflows = [mock_workflow]
        return agent

    @pytest.fixture
    def tool_caller(self, mock_agent):
        """Create a ToolCaller instance."""
        return ToolCaller(mock_agent)

    def test_execute_workflow_call_success(self, tool_caller):
        """Test successful workflow call execution."""
        arguments = {"workflow_id": "workflow-123", "method": "execute", "parameters": {"input": "test"}}

        result = tool_caller.execute_workflow_call(arguments)

        assert result["success"] is True
        assert result["type"] == "workflow"
        assert result["target"] == "workflow-123.execute"
        assert "workflow executed" in result["result"]["result"]

    def test_execute_workflow_call_missing_workflow_id(self, tool_caller):
        """Test workflow call with missing workflow_id."""
        arguments = {"parameters": {"input": "test"}}

        result = tool_caller.execute_workflow_call(arguments)

        assert result["success"] is False
        assert result["type"] == "workflow"
        assert "Missing workflow_id" in result["result"]

    def test_execute_workflow_call_with_custom_method(self, tool_caller):
        """Test workflow call with custom method."""
        arguments = {"workflow_id": "workflow-123", "method": "validate", "parameters": {"input": "test"}}

        result = tool_caller.execute_workflow_call(arguments)

        assert result["success"] is True
        assert result["type"] == "workflow"
        assert result["target"] == "workflow-123.validate"
        assert "workflow executed" in result["result"]["result"]

    def test_execute_workflow_call_defaults_to_execute(self, tool_caller):
        """Test workflow call defaults to execute method when no method specified."""
        arguments = {"workflow_id": "workflow-123", "parameters": {"input": "test"}}

        result = tool_caller.execute_workflow_call(arguments)

        assert result["success"] is True
        assert result["type"] == "workflow"
        assert result["target"] == "workflow-123.execute"
        assert "workflow executed" in result["result"]["result"]

    def test_invoke_workflow_structured_not_found(self, tool_caller):
        """Test structured workflow invocation with non-existent workflow."""
        result = tool_caller.invoke("nonexistent-workflow", "execute", {}, "workflow")

        assert "Error: Workflow nonexistent-workflow not found" in result


class TestToolCallerIntegration:
    """Test the integration between ToolCaller and WARCaller methods."""

    @pytest.fixture
    def mock_agent(self):
        """Create a comprehensive mock agent."""
        agent = Mock(spec=STARAgent)
        agent.agent_type = "test_agent"
        agent.object_id = "test-agent-123"

        # Mock resource
        mock_resource = Mock()
        mock_resource.object_id = "resource-123"
        mock_resource.write = Mock(return_value="Resource executed")
        agent.available_resources = [mock_resource]

        # Mock workflow
        mock_workflow = Mock()
        mock_workflow.workflow_id = "workflow-123"
        mock_workflow.execute = Mock(return_value="Workflow executed")
        agent.available_workflows = [mock_workflow]

        return agent

    @pytest.fixture
    def tool_caller(self, mock_agent):
        """Create a ToolCaller instance."""
        return ToolCaller(mock_agent)

    def test_execute_single_call_resource(self, tool_caller):
        """Test single tool call execution for resource."""
        tool_call = {
            "function": 'type="resource" id="resource-123"',
            "arguments": {"method": "write", "data": "test"},
        }

        result = tool_caller._execute_single_call(tool_call)

        assert result["success"] is True
        assert result["type"] == "resource"

    def test_execute_single_call_workflow(self, tool_caller):
        """Test single tool call execution for workflow."""
        tool_call = {"function": 'type="workflow" id="workflow-123"', "arguments": {"input": "test"}}

        result = tool_caller._execute_single_call(tool_call)

        assert result["success"] is True
        assert result["type"] == "workflow"

    def test_execute_single_call_unknown_function(self, tool_caller):
        """Test single tool call execution with unknown function."""
        tool_call = {"function": "unknown_function", "arguments": {}}

        result = tool_caller._execute_single_call(tool_call)

        assert result["success"] is False
        # After refactoring, unknown functions may produce different error messages
        # depending on the code path taken (registry lookup, fault-tolerant parsing, etc.)
        assert "Error" in result["result"] or "Unknown" in result["result"]

    def test_execute_tool_calls_multiple(self, tool_caller):
        """Test execution of multiple tool calls."""
        tool_calls = [
            {"function": 'type="resource" id="resource-123"', "arguments": {"method": "write", "data": "test1"}},
            {"function": 'type="workflow" id="workflow-123"', "arguments": {"input": "test2"}},
        ]

        results = tool_caller.execute_tool_calls(tool_calls)

        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[0]["type"] == "resource"
        assert results[1]["success"] is True
        assert results[1]["type"] == "workflow"


class TestXMLJSONParsing:
    """Test the shared XML/JSON parsing utilities."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        return Mock(spec=STARAgent)

    @pytest.fixture
    def tool_caller(self, mock_agent):
        """Create a ToolCaller instance."""
        return ToolCaller(mock_agent)

    def test_convert_function_parameter_value_xml(self, tool_caller):
        """Test XML parameter parsing."""
        xml_input = "<todos><todo><content>Test</content><status>pending</status><id>1</id></todo></todos>"

        result = tool_caller._convert_function_parameter_value(xml_input)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["content"] == "Test"
        assert result[0]["status"] == "pending"
        assert result[0]["id"] == 1  # XML parser correctly converts "1" to integer

    def test_convert_function_parameter_value_json(self, tool_caller):
        """Test JSON parameter parsing."""
        json_input = '{"key": "value", "number": 42}'

        result = tool_caller._convert_function_parameter_value(json_input)

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_convert_function_parameter_value_plain_text(self, tool_caller):
        """Test plain text parameter parsing."""
        text_input = "simple text"

        result = tool_caller._convert_function_parameter_value(text_input)

        assert result == "simple text"

    def test_detect_json_format(self, tool_caller):
        """Test JSON format detection."""
        assert tool_caller._detect_json_format('{"key": "value"}') is True
        assert tool_caller._detect_json_format("[1, 2, 3]") is True
        assert tool_caller._detect_json_format("<xml>content</xml>") is False
        assert tool_caller._detect_json_format("plain text") is False

    def test_detect_xml_format(self, tool_caller):
        """Test XML format detection."""
        assert tool_caller._detect_xml_format("<xml>content</xml>") is True
        assert tool_caller._detect_xml_format('{"key": "value"}') is False
        assert tool_caller._detect_xml_format("plain text") is False

    def test_convert_text_to_typed_value(self, tool_caller):
        """Test text to typed value conversion."""
        assert tool_caller._convert_text_to_typed_value("true") is True
        assert tool_caller._convert_text_to_typed_value("false") is False
        assert tool_caller._convert_text_to_typed_value("42") == 42
        assert tool_caller._convert_text_to_typed_value("3.14") == 3.14
        assert tool_caller._convert_text_to_typed_value("text") == "text"


class TestLLMResponseParsing:
    """Test LLM response parsing functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        return Mock(spec=STARAgent)

    @pytest.fixture
    def tool_caller(self, mock_agent):
        """Create a ToolCaller instance."""
        return ToolCaller(mock_agent)

    def test_parse_llm_response_with_content_only(self, tool_caller):
        """Test parsing LLM response with only content."""
        llm_response = LLMResponse(
            content="<response><content>Hello, this is a simple response.</content></response>", model="test-model", tool_calls=[]
        )

        response_text, _reasoning, tool_calls = tool_caller.parse_llm_response(llm_response)

        assert response_text == "Hello, this is a simple response."
        assert len(tool_calls) == 0

    def test_parse_llm_response_with_agent_target_format(self, tool_caller):
        """Test parsing LLM response with agent target/method format."""
        llm_response = LLMResponse(
            content="""<response>
<type>in_progress</type>
<content>I will research China's energy consumption trends and data.</content>
<tool_calls>
<tool_call>
<target type="agent" id="web-research-001"/>
<method>invoke</method>
<arguments><message>Research current trends and data on China's energy consumption in 2025</message></arguments>
</tool_call>
</tool_calls>
</response>""",
            model="test-model",
            tool_calls=[],
        )

        response_text, _reasoning, tool_calls = tool_caller.parse_llm_response(llm_response)

        assert "I will research China's energy consumption trends and data." in response_text
        assert len(tool_calls) == 1
        # After refactoring, function name correctly extracts id value (id > type preference)
        assert tool_calls[0]["function"] == "web-research-001"
        assert tool_calls[0]["arguments"]["method"] == "invoke"
        assert tool_calls[0]["arguments"]["message"] == "Research current trends and data on China's energy consumption in 2025"

    def test_parse_llm_response_with_resource_target_format(self, tool_caller):
        """Test parsing LLM response with resource target/method format."""
        llm_response = LLMResponse(
            content="""<response>
<type>in_progress</type>
<content>I'll select the appropriate workflow for your research request.</content>
<tool_calls>
<tool_call>
<target type="resource" id="workflow-selector-123"/>
<method>select_workflow</method>
<arguments>
<request>Research China's energy consumption trends and statistics for 2025</request>
<target_url>https://example.com/energy-data</target_url>
</arguments>
</tool_call>
</tool_calls>
</response>""",
            model="test-model",
            tool_calls=[],
        )

        response_text, _reasoning, tool_calls = tool_caller.parse_llm_response(llm_response)

        assert "I'll select the appropriate workflow for your research request." in response_text
        assert len(tool_calls) == 1
        # After refactoring, function name correctly extracts id value (id > type preference)
        assert tool_calls[0]["function"] == "workflow-selector-123"
        assert tool_calls[0]["arguments"]["method"] == "select_workflow"
        assert tool_calls[0]["arguments"]["request"] == "Research China's energy consumption trends and statistics for 2025"
        assert tool_calls[0]["arguments"]["target_url"] == "https://example.com/energy-data"

    def test_parse_llm_response_with_json_in_arguments(self, tool_caller):
        """Test parsing LLM response with JSON inside <arguments> tag."""
        llm_response = LLMResponse(
            content="""<response>
<type>in_progress</type>
<reasoning>Creating tasks for research.</reasoning>
<content>Initializing research tasks.</content>
<tool_calls>
<tool_call>
<target type="resource" id="todo-resource"/>
<method>write</method>
<arguments>
{
  "todos": [
    {
      "id": "task1",
      "content": "Gather total primary energy consumption for China in 2025",
      "status": "in_progress"
    },
    {
      "id": "task2",
      "content": "Collect breakdown by source",
      "status": "pending"
    }
  ]
}
</arguments>
</tool_call>
</tool_calls>
</response>""",
            model="test-model",
            tool_calls=[],
        )

        response_text, _reasoning, tool_calls = tool_caller.parse_llm_response(llm_response)

        assert "Initializing research tasks." in response_text
        assert len(tool_calls) == 1
        # After refactoring, function name correctly extracts id value (id > type preference)
        assert tool_calls[0]["function"] == "todo-resource"
        assert tool_calls[0]["arguments"]["method"] == "write"
        # Verify the JSON was correctly parsed
        assert "todos" in tool_calls[0]["arguments"]
        todos = tool_calls[0]["arguments"]["todos"]
        assert len(todos) == 2
        assert todos[0]["id"] == "task1"
        assert todos[0]["status"] == "in_progress"
        assert todos[1]["id"] == "task2"
        assert todos[1]["status"] == "pending"

    def test_parse_llm_response_with_workflow_target_format(self, tool_caller):
        """Test parsing LLM response with workflow target/method format."""
        llm_response = LLMResponse(
            content="""<response>
<type>in_progress</type>
<content>I'll execute the single source deep dive workflow.</content>
<tool_calls>
<tool_call>
<target type="workflow" id="single-source-deep-dive-123"/>
<method>execute</method>
<arguments>
<url>https://example.com/energy-report</url>
<purpose>Analyze energy consumption trends</purpose>
<extract_code>true</extract_code>
<max_key_points>10</max_key_points>
</arguments>
</tool_call>
</tool_calls>
</response>""",
            model="test-model",
            tool_calls=[],
        )

        response_text, _reasoning, tool_calls = tool_caller.parse_llm_response(llm_response)

        assert "I'll execute the single source deep dive workflow." in response_text
        assert len(tool_calls) == 1
        # After refactoring, function name correctly extracts id value (id > type preference)
        assert tool_calls[0]["function"] == "single-source-deep-dive-123"
        assert tool_calls[0]["arguments"]["method"] == "execute"
        assert tool_calls[0]["arguments"]["url"] == "https://example.com/energy-report"
        assert tool_calls[0]["arguments"]["purpose"] == "Analyze energy consumption trends"
        assert tool_calls[0]["arguments"]["extract_code"] is True
        assert tool_calls[0]["arguments"]["max_key_points"] == 10

    def test_parse_llm_response_empty(self, tool_caller):
        """Test parsing empty LLM response."""
        response_text, reasoning, tool_calls = tool_caller.parse_llm_response(None)

        assert response_text is None
        assert reasoning is None
        assert len(tool_calls) == 0


class TestCodecToolCallerWithObjectId:
    """Test CodecToolCaller with object_id format."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with resources."""
        agent = Mock(spec=STARAgent)
        agent.agent_type = "test_agent"
        agent.object_id = "test-agent-123"
        agent.available_agents = []
        agent.available_workflows = []
        agent._registry = Mock()
        agent._registry._items = {}
        agent.ensure_registered = Mock()

        # Create mock resources with object_id
        mock_resource1 = Mock()
        mock_resource1.__class__.__name__ = "SearchResource"
        mock_resource1.object_id = "my-search-resource"
        mock_resource1.resource_id = "my-search-resource"
        search_method1 = Mock(return_value={"results": ["result1", "result2"]})
        search_method1.__name__ = "search"
        mock_resource1.search = search_method1

        mock_resource2 = Mock()
        mock_resource2.__class__.__name__ = "SearchResource"  # Same class, different instance
        mock_resource2.object_id = "another-search-resource"
        mock_resource2.resource_id = "another-search-resource"
        search_method2 = Mock(return_value={"results": ["result3"]})
        search_method2.__name__ = "search"
        mock_resource2.search = search_method2

        agent.available_resources = [mock_resource1, mock_resource2]
        return agent

    @pytest.fixture
    def codec_tool_caller(self, mock_agent):
        """Create a CodecToolCaller instance."""
        return CodecToolCaller(mock_agent, CSXMLCodec)

    def test_find_object_by_id_finds_resource(self, codec_tool_caller):
        """Test _find_object_by_id finds resource by object_id."""
        obj_info = codec_tool_caller._find_object_by_id("my-search-resource")

        assert obj_info is not None
        assert obj_info["type"] == "resource"
        assert obj_info["object"].object_id == "my-search-resource"

    def test_find_object_by_id_finds_correct_instance(self, codec_tool_caller):
        """Test _find_object_by_id finds the correct instance when multiple exist."""
        # Both resources have same class name but different object_id
        obj_info1 = codec_tool_caller._find_object_by_id("my-search-resource")
        obj_info2 = codec_tool_caller._find_object_by_id("another-search-resource")

        assert obj_info1 is not None
        assert obj_info2 is not None
        assert obj_info1["object"].object_id == "my-search-resource"
        assert obj_info2["object"].object_id == "another-search-resource"
        assert obj_info1["object"] != obj_info2["object"]

    def test_execute_single_call_with_object_id(self, codec_tool_caller):
        """Test _execute_single_call works with object_id:method format."""
        tool_call = {"function": "my-search-resource:search", "arguments": {"query": "test query"}}

        result = codec_tool_caller._execute_single_call(tool_call)

        assert result["success"] is True
        assert result["type"] == "resource"
        assert "my-search-resource.search" in result["target"]

    def test_execute_single_call_falls_back_to_class_name(self, codec_tool_caller):
        """Test _execute_single_call falls back to class_name lookup."""
        # Use class name format (backward compatibility)
        tool_call = {"function": "SearchResource:search", "arguments": {"query": "test query"}}

        result = codec_tool_caller._execute_single_call(tool_call)

        # Should still work with class_name format
        assert result["success"] is True
        assert result["type"] == "resource"


class TestValidateAndCastMethodArguments:
    """Test _validate_n_cast_method_arguments edge cases."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = Mock(spec=STARAgent)
        agent.agent_type = "test_agent"
        agent.object_id = "test-agent-123"
        agent.available_agents = []
        agent.available_resources = []
        agent.available_workflows = []
        agent._registry = Mock()
        agent._registry._items = {}
        agent.ensure_registered = Mock()
        return agent

    @pytest.fixture
    def codec_tool_caller(self, mock_agent):
        """Create a CodecToolCaller instance."""
        from dana.core.knowledge.prompts.codecs import CSXMLCodec

        return CodecToolCaller(mock_agent, CSXMLCodec)

    def test_cast_string_to_int(self, codec_tool_caller):
        """Test basic string to int conversion."""

        def test_method(value: int) -> int:
            """Test method.

            Args:
                value: Integer value
            """
            return value

        arguments = {"value": "42"}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)

        assert result["value"] == 42
        assert isinstance(result["value"], int)

    def test_cast_string_to_float(self, codec_tool_caller):
        """Test basic string to float conversion."""

        def test_method(value: float) -> float:
            """Test method.

            Args:
                value: Float value
            """
            return value

        arguments = {"value": "3.14"}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)

        assert result["value"] == 3.14
        assert isinstance(result["value"], float)

    def test_cast_string_bool_true_false(self, codec_tool_caller):
        """Test string 'true'/'false' to bool conversion."""

        def test_method(value: bool) -> bool:
            """Test method.

            Args:
                value: Boolean value
            """
            return value

        # Test "true" string
        arguments = {"value": "true"}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        assert result["value"] is True
        assert isinstance(result["value"], bool)

        # Test "false" string
        arguments = {"value": "false"}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        assert result["value"] is False
        assert isinstance(result["value"], bool)

    def test_cast_string_list_json(self, codec_tool_caller):
        """Test JSON list string to list conversion."""

        def test_method(items: list[str]) -> list[str]:
            """Test method.

            Args:
                items: List of strings
            """
            return items

        arguments = {"items": '["apple", "banana", "cherry"]'}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)

        assert result["items"] == ["apple", "banana", "cherry"]
        assert isinstance(result["items"], list)

    def test_cast_string_dict_json(self, codec_tool_caller):
        """Test JSON dict string to dict conversion."""

        def test_method(data: dict[str, int]) -> dict[str, int]:
            """Test method.

            Args:
                data: Dictionary mapping strings to integers
            """
            return data

        arguments = {"data": '{"a": 1, "b": 2}'}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)

        assert result["data"] == {"a": 1, "b": 2}
        assert isinstance(result["data"], dict)

    def test_already_correct_type_unchanged(self, codec_tool_caller):
        """Test that already correct types are not modified."""

        def test_method(value: int) -> int:
            """Test method.

            Args:
                value: Integer value
            """
            return value

        arguments = {"value": 42}  # Already an int
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)

        assert result["value"] == 42
        assert isinstance(result["value"], int)
        # Should not have been converted unnecessarily

    def test_optional_type_with_none(self, codec_tool_caller):
        """Test Optional[int] handles NoneType in __args__ without crashing."""

        def test_method(value: int | None) -> int | None:
            """Test method.

            Args:
                value: Optional integer value
            """
            return value

        # Test with None value
        arguments = {"value": None}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        assert result["value"] is None

        # Test with string that should convert to int
        arguments = {"value": "42"}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        assert result["value"] == 42

    def test_generic_list_type(self, codec_tool_caller):
        """Test List[int] doesn't crash issubclass."""

        def test_method(items: list[int]) -> list[int]:
            """Test method.

            Args:
                items: List of integers
            """
            return items

        arguments = {"items": "[1, 2, 3]"}
        # Should not crash with TypeError from issubclass
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        # Should convert JSON string to list
        assert isinstance(result["items"], list)

    def test_pydantic_model_conversion(self, codec_tool_caller):
        """Test BaseModel JSON conversion."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            age: int

        def test_method(model: TestModel) -> TestModel:
            """Test method.

            Args:
                model: Test model instance
            """
            return model

        arguments = {"model": '{"name": "Alice", "age": 30}'}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)

        assert isinstance(result["model"], TestModel)
        assert result["model"].name == "Alice"
        assert result["model"].age == 30

    def test_eval_injection_blocked(self, codec_tool_caller):
        """Test that eval() is NOT used (security test)."""

        def test_method(items: list[str]) -> list[str]:
            """Test method.

            Args:
                items: List of strings
            """
            return items

        # Try to inject malicious code - should NOT execute
        malicious_input = "__import__('os').system('echo vulnerable')"
        arguments = {"items": malicious_input}

        # Should fail safely without executing code
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        # The malicious code should remain as a string (not executed)
        # This is safe because we use json.loads() instead of eval()
        # The string will fail JSON parsing and remain unchanged
        assert isinstance(result.get("items"), str)
        assert result.get("items") == malicious_input
        # Verify it's still a string and wasn't executed as code

    def test_bool_already_bool(self, codec_tool_caller):
        """Test that bool values are not converted unnecessarily."""

        def test_method(value: bool) -> bool:
            """Test method.

            Args:
                value: Boolean value
            """
            return value

        arguments = {"value": True}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        assert result["value"] is True
        assert isinstance(result["value"], bool)

    def test_list_already_list(self, codec_tool_caller):
        """Test that list values are not converted unnecessarily."""

        def test_method(items: list[str]) -> list[str]:
            """Test method.

            Args:
                items: List of strings
            """
            return items

        arguments = {"items": ["apple", "banana"]}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        assert result["items"] == ["apple", "banana"]
        assert isinstance(result["items"], list)

    def test_dict_already_dict(self, codec_tool_caller):
        """Test that dict values are not converted unnecessarily."""

        def test_method(data: dict[str, int]) -> dict[str, int]:
            """Test method.

            Args:
                data: Dictionary mapping strings to integers
            """
            return data

        arguments = {"data": {"a": 1, "b": 2}}
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        assert result["data"] == {"a": 1, "b": 2}
        assert isinstance(result["data"], dict)

    def test_invalid_json_handled_gracefully(self, codec_tool_caller):
        """Test that invalid JSON strings are handled gracefully."""

        def test_method(items: list[str]) -> list[str]:
            """Test method.

            Args:
                items: List of strings
            """
            return items

        arguments = {"items": "not valid json"}
        # Should not crash, should handle error gracefully
        result = codec_tool_caller._validate_n_cast_method_arguments(test_method, arguments)
        # Should either keep original value or handle error
        assert "items" in result
