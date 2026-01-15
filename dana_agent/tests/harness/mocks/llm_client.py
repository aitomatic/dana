"""
Mock LLM Client for STARAgent robustness testing.

Provides configurable responses, fault injection, and call history tracking.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from dana.common.llm.types import LLMMessage, LLMResponse


@dataclass
class LLMResponseScenario:
    """Configurable LLM response scenario for testing."""

    content: str = ""
    tool_calls: list[dict] | None = None
    finish_reason: str = "stop"
    model: str = "mock-model"
    usage: dict[str, int] | None = None
    delay_ms: int = 0
    raise_exception: Exception | None = None

    def to_llm_response(self) -> LLMResponse:
        """Convert scenario to LLMResponse."""
        return LLMResponse(
            content=self.content,
            model=self.model,
            usage=self.usage or {"prompt_tokens": 10, "completion_tokens": 5},
            finish_reason=self.finish_reason,
            tool_calls=self.tool_calls,
        )


class MockLLMClient:
    """
    Configurable mock LLM client for testing.

    Features:
    - Response queue for deterministic multi-turn testing
    - Call history for verification
    - Preset scenarios for common failure modes
    - Delay simulation for timeout testing
    """

    def __init__(self):
        self.response_queue: list[LLMResponseScenario] = []
        self.call_history: list[dict[str, Any]] = []
        self.default_response = LLMResponseScenario(content="Default mock response")
        self._call_count = 0

    def queue_response(self, scenario: LLMResponseScenario) -> None:
        """Add a response scenario to the queue."""
        self.response_queue.append(scenario)

    def queue_responses(self, scenarios: list[LLMResponseScenario]) -> None:
        """Add multiple response scenarios to the queue."""
        self.response_queue.extend(scenarios)

    def clear_queue(self) -> None:
        """Clear the response queue."""
        self.response_queue.clear()

    def clear_history(self) -> None:
        """Clear call history."""
        self.call_history.clear()
        self._call_count = 0

    def get_next_response(self) -> LLMResponseScenario:
        """Get the next response from the queue or default."""
        if self.response_queue:
            return self.response_queue.pop(0)
        return self.default_response

    def _record_call(self, messages: list[LLMMessage], **kwargs) -> None:
        """Record a call to the mock LLM."""
        self._call_count += 1
        self.call_history.append({
            "call_number": self._call_count,
            "timestamp": time.time(),
            "messages": [{"role": m.role, "content": m.content[:100]} for m in messages],
            "message_count": len(messages),
            "kwargs": kwargs,
        })

    async def chat_response(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Async chat response - matches LLM interface."""
        self._record_call(messages, **kwargs)
        scenario = self.get_next_response()

        # Simulate delay
        if scenario.delay_ms > 0:
            await asyncio.sleep(scenario.delay_ms / 1000)

        # Raise exception if configured
        if scenario.raise_exception:
            raise scenario.raise_exception

        return scenario.to_llm_response()

    def chat_response_sync(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Sync chat response - matches LLM interface."""
        self._record_call(messages, **kwargs)
        scenario = self.get_next_response()

        # Simulate delay
        if scenario.delay_ms > 0:
            time.sleep(scenario.delay_ms / 1000)

        # Raise exception if configured
        if scenario.raise_exception:
            raise scenario.raise_exception

        return scenario.to_llm_response()

    # ==================== Preset Scenarios ====================

    @staticmethod
    def empty_response() -> LLMResponseScenario:
        """Empty response - triggers retry logic."""
        return LLMResponseScenario(content="", tool_calls=None)

    @staticmethod
    def simple_response(content: str) -> LLMResponseScenario:
        """Simple text response with no tool calls."""
        return LLMResponseScenario(content=content)

    @staticmethod
    def well_formed_tool_call(
        target_id: str = "test-resource",
        method: str = "query",
        message: str = "test message",
    ) -> LLMResponseScenario:
        """Well-formed XML tool call."""
        xml = f"""I'll help you with that.

<tool_call>
<target id="{target_id}"/>
<method>{method}</method>
<arguments>
<message>{message}</message>
</arguments>
</tool_call>"""
        return LLMResponseScenario(content=xml)

    @staticmethod
    def malformed_xml_missing_closing() -> LLMResponseScenario:
        """XML with missing closing tag - common small LLM failure."""
        return LLMResponseScenario(content="""I'll search for that.

<tool_call>
<target id="search"/>
<method>query</method>
<arguments><message>test</message></arguments>
<!-- missing </tool_call> -->
""")

    @staticmethod
    def malformed_xml_wrong_tag() -> LLMResponseScenario:
        """Wrong tag name - common small LLM variation."""
        return LLMResponseScenario(content="""<function name="search.query">
<param>test query</param>
</function>""")

    @staticmethod
    def json_in_xml() -> LLMResponseScenario:
        """JSON content inside XML tags - mixed format."""
        return LLMResponseScenario(content="""<tool_call>
{"target": "search", "method": "query", "args": {"message": "test"}}
</tool_call>""")

    @staticmethod
    def hallucinated_tool(tool_id: str = "non-existent-tool") -> LLMResponseScenario:
        """Call to non-existent tool - common small LLM failure."""
        return LLMResponseScenario(content=f"""<tool_call>
<target id="{tool_id}"/>
<method>do_thing</method>
</tool_call>""")

    @staticmethod
    def repeated_tool_calls() -> LLMResponseScenario:
        """Same tool call repeated multiple times."""
        xml = """<tool_call>
<target id="search"/>
<method>query</method>
<arguments><message>test</message></arguments>
</tool_call>

<tool_call>
<target id="search"/>
<method>query</method>
<arguments><message>test</message></arguments>
</tool_call>

<tool_call>
<target id="search"/>
<method>query</method>
<arguments><message>test</message></arguments>
</tool_call>"""
        return LLMResponseScenario(content=xml)

    @staticmethod
    def partial_response() -> LLMResponseScenario:
        """Incomplete response cut off mid-tool-call."""
        return LLMResponseScenario(
            content="""<tool_call>
<target id="search"/>
<method>que""",
            finish_reason="length",  # Indicates truncation
        )

    @staticmethod
    def error_in_reasoning() -> LLMResponseScenario:
        """Response with error in reasoning text."""
        return LLMResponseScenario(
            content="I encountered an error while processing your request."
        )

    @staticmethod
    def csxml_codec_format(
        class_name: str = "SearchResource",
        method: str = "query",
        param_name: str = "message",
        param_value: str = "test",
    ) -> LLMResponseScenario:
        """CSXMLCodec format tool call."""
        return LLMResponseScenario(content=f"""<thinking>I need to search for information.</thinking>
<function_call>
<invoke name="{class_name}:{method}">
<parameter name="{param_name}">{param_value}</parameter>
</invoke>
</function_call>""")

    @staticmethod
    def klxml_codec_format(
        class_name: str = "SearchResource",
        method: str = "query",
        param_name: str = "message",
        param_value: str = "test",
    ) -> LLMResponseScenario:
        """KLXMLCodec format tool call."""
        return LLMResponseScenario(content=f"""<thinking>I need to search for information.</thinking>
<{class_name}:{method}>
<param name="{param_name}">{param_value}</param>
</{class_name}:{method}>""")

    @staticmethod
    def native_openai_tool_calls(
        function_name: str = "search",
        arguments: dict | str = None,
    ) -> LLMResponseScenario:
        """Native OpenAI tool_calls format."""
        if arguments is None:
            arguments = {"message": "test"}
        return LLMResponseScenario(
            content="",  # Content typically empty with native tool calls
            tool_calls=[{
                "function": function_name,
                "arguments": arguments,
            }],
            finish_reason="tool_calls",
        )

    @staticmethod
    def timeout_response(delay_ms: int = 5000) -> LLMResponseScenario:
        """Response with delay to test timeout handling."""
        return LLMResponseScenario(
            content="This response is delayed",
            delay_ms=delay_ms,
        )

    @staticmethod
    def exception_response(
        exception: Exception | None = None,
    ) -> LLMResponseScenario:
        """Response that raises an exception."""
        return LLMResponseScenario(
            raise_exception=exception or RuntimeError("Mock LLM error"),
        )


# ==================== Small LLM Specific Scenarios ====================

@dataclass
class SmallLLMScenarios:
    """Collection of common small LLM failure patterns."""

    @staticmethod
    def all_scenarios() -> list[LLMResponseScenario]:
        """Return all small LLM failure scenarios for comprehensive testing."""
        return [
            MockLLMClient.malformed_xml_missing_closing(),
            MockLLMClient.malformed_xml_wrong_tag(),
            MockLLMClient.json_in_xml(),
            MockLLMClient.hallucinated_tool(),
            MockLLMClient.repeated_tool_calls(),
            MockLLMClient.partial_response(),
            SmallLLMScenarios.missing_attribute(),
            SmallLLMScenarios.wrong_parameter_name(),
            SmallLLMScenarios.extra_whitespace(),
            SmallLLMScenarios.mixed_codec_format(),
        ]

    @staticmethod
    def missing_attribute() -> LLMResponseScenario:
        """Target without id attribute - uses content instead."""
        return LLMResponseScenario(content="""<tool_call>
<target>search-resource</target>
<method>query</method>
<arguments><message>test</message></arguments>
</tool_call>""")

    @staticmethod
    def wrong_parameter_name() -> LLMResponseScenario:
        """Common parameter name variations."""
        return LLMResponseScenario(content="""<tool_call>
<target id="search"/>
<method>query</method>
<arguments>
<msg>test message</msg>
<q>search query</q>
</arguments>
</tool_call>""")

    @staticmethod
    def extra_whitespace() -> LLMResponseScenario:
        """Excessive whitespace that might break parsing."""
        return LLMResponseScenario(content="""

    <tool_call>

        <target    id="search"   />

        <method>  query  </method>

        <arguments>
            <message>  test  </message>
        </arguments>

    </tool_call>

""")

    @staticmethod
    def mixed_codec_format() -> LLMResponseScenario:
        """CSXMLCodec tag with KLXMLCodec parameter style."""
        return LLMResponseScenario(content="""<thinking>Processing...</thinking>
<SearchResource:query>
<parameter name="message">test</parameter>
</SearchResource:query>""")

    @staticmethod
    def numbered_list_as_tools() -> LLMResponseScenario:
        """Small LLM outputs numbered list instead of tool calls."""
        return LLMResponseScenario(content="""I'll help you with that. Here are the steps:

1. Search for information using the search resource
2. Process the results
3. Return the answer

Let me start with step 1:
<tool_call>
<target id="search"/>
<method>query</method>
</tool_call>""")
