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
    ToolCaller,
    WARCaller,
)
from dana.core.agent.star_agent import STARAgent


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

    @patch("dana_agent.core.agent.components.tool_caller.get_debug_logger")
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
        assert "Unknown function" in result["result"]

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
        assert 'type="agent" id="web-research-001"' in tool_calls[0]["function"]
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
        assert 'type="resource" id="workflow-selector-123"' in tool_calls[0]["function"]
        assert tool_calls[0]["arguments"]["method"] == "select_workflow"
        assert tool_calls[0]["arguments"]["request"] == "Research China's energy consumption trends and statistics for 2025"
        assert tool_calls[0]["arguments"]["target_url"] == "https://example.com/energy-data"

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
        assert 'type="workflow" id="single-source-deep-dive-123"' in tool_calls[0]["function"]
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
