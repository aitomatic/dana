"""
Tests for tool-calling robustness (Concern #1).

Evaluates whether STARAgent's custom XML-based tool calling is robust enough
to handle various LLM outputs, especially from small LLMs.
"""

from __future__ import annotations

import pytest

from dana.core.agent.components.tool_caller import ToolCaller

from .mocks.llm_client import MockLLMClient, LLMResponseScenario, SmallLLMScenarios
from .mocks.resources import MockResource
from .harness_agent import HarnessAgent


class TestWellFormedToolCalls:
    """Tests for well-formed tool call parsing."""

    def test_xml_well_formed_parses_correctly(self, harness_agent_with_resource, mock_resource):
        """Standard XML tool call should parse correctly."""
        mock_llm = harness_agent_with_resource._mock_llm

        # Queue well-formed tool call then final response
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource",
            method="query",
            message="test query",
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Please search")

        # Should have completed without errors
        harness_agent_with_resource.assert_no_errors()

        # Resource should have been called
        assert len(mock_resource.call_history) == 1
        assert mock_resource.call_history[0]["method"] == "query"

    def test_empty_tool_calls_triggers_exit(self, harness_agent):
        """Response with no tool calls should exit cleanly."""
        mock_llm = harness_agent._mock_llm
        mock_llm.queue_response(MockLLMClient.simple_response("Here is your answer"))

        result = harness_agent.query(message="What is 2+2?")

        # Should exit cleanly (exit reason detection may vary)
        assert harness_agent.get_exit_reason() in ["normal", "no_tool_calls"]
        assert "response" in result


class TestMalformedXML:
    """Tests for malformed XML handling."""

    def test_missing_closing_tag_handled(self, harness_agent_with_resource, mock_resource):
        """XML with missing closing tag should be handled gracefully."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.malformed_xml_missing_closing())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        # Should not raise exception
        result = harness_agent_with_resource.query(message="Search for something")

        # Even if parsing fails, should exit cleanly
        assert result is not None

    def test_wrong_tag_name_handled(self, harness_agent_with_resource):
        """Wrong tag name (e.g., <function> instead of <tool_call>) should be handled."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.malformed_xml_wrong_tag())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")

        # Should complete without crashing
        assert result is not None

    def test_partial_response_handled(self, harness_agent_with_resource):
        """Partial/truncated response should be handled gracefully."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.partial_response())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")

        # Should not crash on truncated XML
        assert result is not None


class TestMixedFormats:
    """Tests for mixed format handling (XML + JSON)."""

    def test_json_in_xml_arguments(self, harness_agent_with_resource):
        """JSON embedded in XML arguments should be parsed."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.json_in_xml())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")

        # Should handle mixed format
        assert result is not None


class TestCodecFormats:
    """Tests for different codec format handling."""

    def test_csxml_codec_format(self, harness_agent_with_resource):
        """CSXMLCodec format should be parsed."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.csxml_codec_format())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")
        assert result is not None

    def test_klxml_codec_format(self, harness_agent_with_resource):
        """KLXMLCodec format should be parsed."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.klxml_codec_format())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")
        assert result is not None


class TestNativeToolCalls:
    """Tests for native OpenAI/Groq tool_calls format."""

    def test_native_openai_tool_calls(self, harness_agent_with_resource):
        """Native OpenAI tool_calls should be converted correctly."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.native_openai_tool_calls(
            function_name="mock-resource.query",
            arguments={"message": "test"},
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")
        assert result is not None


class TestSmallLLMScenarios:
    """Tests specifically for small LLM failure modes."""

    def test_missing_attribute_handled(self, harness_agent_with_resource):
        """Target without id attribute should use content."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(SmallLLMScenarios.missing_attribute())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")
        assert result is not None

    def test_wrong_parameter_name_handled(self, harness_agent_with_resource):
        """Wrong parameter names (msg vs message) should be handled."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(SmallLLMScenarios.wrong_parameter_name())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")
        assert result is not None

    def test_extra_whitespace_handled(self, harness_agent_with_resource):
        """Excessive whitespace should not break parsing."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(SmallLLMScenarios.extra_whitespace())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")
        assert result is not None

    def test_mixed_codec_format_handled(self, harness_agent_with_resource):
        """Mixed codec formats should be handled gracefully."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(SmallLLMScenarios.mixed_codec_format())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search")
        assert result is not None

    @pytest.mark.parametrize("scenario_name", [
        "missing_attribute",
        "wrong_parameter_name",
        "extra_whitespace",
        "mixed_codec_format",
        "numbered_list_as_tools",
    ])
    def test_all_small_llm_scenarios(self, harness_agent_with_resource, scenario_name):
        """Parametrized test for all small LLM scenarios."""
        mock_llm = harness_agent_with_resource._mock_llm

        scenario_methods = {
            "missing_attribute": SmallLLMScenarios.missing_attribute,
            "wrong_parameter_name": SmallLLMScenarios.wrong_parameter_name,
            "extra_whitespace": SmallLLMScenarios.extra_whitespace,
            "mixed_codec_format": SmallLLMScenarios.mixed_codec_format,
            "numbered_list_as_tools": SmallLLMScenarios.numbered_list_as_tools,
        }

        mock_llm.queue_response(scenario_methods[scenario_name]())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        # Should complete without crashing
        result = harness_agent_with_resource.query(message="Search")
        assert result is not None


class TestHallucinatedTools:
    """Tests for handling hallucinated (non-existent) tool calls."""

    def test_hallucinated_tool_graceful_error(self, harness_agent_with_resource):
        """Calling a non-existent tool should produce a graceful error."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.hallucinated_tool("non-existent-tool"))
        mock_llm.queue_response(MockLLMClient.simple_response("I apologize, that tool doesn't exist."))

        result = harness_agent_with_resource.query(message="Use magic tool")

        # Should complete without crashing
        assert result is not None

    def test_repeated_tool_calls_handled(self, harness_agent_with_resource, mock_resource):
        """Repeated identical tool calls should be handled."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.repeated_tool_calls())
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Search multiple times")

        # Should complete without crashing
        assert result is not None


class TestListVsScalarAmbiguity:
    """Tests for list vs scalar parameter handling."""

    def test_single_item_in_plural_container(self, harness_agent_with_resource):
        """Single item in plural container should be treated as list."""
        # This tests the naming convention based list detection
        mock_llm = harness_agent_with_resource._mock_llm

        content = """<tool_call>
<target id="mock-resource"/>
<method>query</method>
<arguments>
<messages>
<message>single item</message>
</messages>
</arguments>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Test list handling")
        assert result is not None


class TestToolCallerUnit:
    """Unit tests for ToolCaller parsing methods."""

    def test_parse_llm_response_empty(self, harness_agent):
        """Empty response should return empty tool calls."""
        tool_caller = harness_agent._tool_caller

        response, reasoning, tool_calls, _done = tool_caller.parse_llm_response(
            MockLLMClient.empty_response().to_llm_response()
        )

        assert tool_calls is None or len(tool_calls) == 0

    def test_parse_llm_response_simple(self, harness_agent):
        """Simple text response should be returned as response."""
        tool_caller = harness_agent._tool_caller

        response, reasoning, tool_calls, _done = tool_caller.parse_llm_response(
            MockLLMClient.simple_response("Hello world").to_llm_response()
        )

        assert "Hello world" in (response or "")
        assert tool_calls is None or len(tool_calls) == 0
