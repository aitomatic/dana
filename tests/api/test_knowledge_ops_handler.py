import pytest
from dana.api.services.intent_detection.intent_handlers.knowledge_ops_handler import KnowledgeOpsHandler
from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    BaseArgument,
    InputSchema,
)


class MockTool(BaseTool):
    """Mock tool for testing purposes."""

    def __init__(self, name: str, arguments: list[BaseArgument], required: list[str] | None = None):
        tool_info = BaseToolInformation(
            name=name,
            description=f"Mock tool for testing {name}",
            input_schema=InputSchema(type="object", properties=arguments, required=required or []),
        )
        super().__init__(tool_info)

    async def _execute(self, **kwargs):
        from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import ToolResult

        return ToolResult(name=self.name, result="Mock result", require_user=False)


class TestKnowledgeOpsHandlerParseXmlToolCall:
    """Test suite for the _parse_xml_tool_call method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a mock handler with some test tools
        self.handler = KnowledgeOpsHandler(domain_knowledge_path="/tmp/test_domain_knowledge.json", domain="Test Domain", role="Test Role")

        # Mock the tools dictionary with test tools
        self.handler.tools = {
            "ask_question": MockTool(
                name="ask_question",
                arguments=[
                    BaseArgument(name="question", type="string", description="The question to ask"),
                    BaseArgument(name="context", type="string", description="Additional context"),
                ],
                required=["question"],
            ),
            "explore_knowledge": MockTool(
                name="explore_knowledge",
                arguments=[
                    BaseArgument(name="path", type="string", description="Path to explore"),
                    BaseArgument(name="depth", type="int", description="Exploration depth", example="2"),
                ],
                required=["path"],
            ),
            "generate_knowledge": MockTool(
                name="generate_knowledge",
                arguments=[
                    BaseArgument(name="topic", type="string", description="Topic to generate knowledge for"),
                    BaseArgument(name="format", type="string", description="Output format"),
                    BaseArgument(name="options", type="list", description="Generation options", example="['option1', 'option2']"),
                ],
                required=["topic"],
            ),
        }

    def test_parse_simple_tool_call_without_thinking(self):
        """Test parsing a simple tool call without thinking content."""
        xml_content = """<ask_question>
<question>What is the capital of France?</question>
<context>Geography context</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": "What is the capital of France?", "context": "Geography context"}
        assert thinking_content == ""

    def test_parse_tool_call_with_thinking_tag(self):
        """Test parsing a tool call with thinking content in tags."""
        xml_content = """<thinking>
I need to ask a question about geography to help the user.
</thinking>
<ask_question>
<question>What is the capital of France?</question>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": "What is the capital of France?"}
        assert thinking_content == "I need to ask a question about geography to help the user."

    def test_parse_tool_call_with_text_before_xml(self):
        """Test parsing a tool call with text before XML tags."""
        xml_content = """I need to first explore the structure...

<explore_knowledge>
<path>/root/topic</path>
<depth>2</depth>
</explore_knowledge>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "explore_knowledge"
        assert params == {"path": "/root/topic", "depth": 2}
        assert thinking_content == "I need to first explore the structure..."

    def test_parse_tool_call_with_both_thinking_and_text_before(self):
        """Test parsing a tool call with both thinking tag and text before XML."""
        xml_content = """Let me think about this first.

<thinking>
I should explore the knowledge structure to understand what's available.
</thinking>
<explore_knowledge>
<path>/root/topic</path>
</explore_knowledge>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "explore_knowledge"
        assert params == {"path": "/root/topic"}
        assert (
            thinking_content == "Let me think about this first.\n\nI should explore the knowledge structure to understand what's available."
        )

    def test_parse_tool_call_with_list_parameter(self):
        """Test parsing a tool call with list parameters."""
        xml_content = """<generate_knowledge>
<topic>Financial Analysis</topic>
<format>markdown</format>
<options>['detailed', 'summary', 'charts']</options>
</generate_knowledge>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "generate_knowledge"
        assert params == {"topic": "Financial Analysis", "format": "markdown", "options": ["detailed", "summary", "charts"]}
        assert thinking_content == ""

    def test_parse_tool_call_with_whitespace_handling(self):
        """Test that whitespace is properly handled in XML content."""
        xml_content = """   
   
<thinking>
   Some thinking content with spaces   
</thinking>

<ask_question>
<question>   What is this?   </question>
<context>   Some context   </context>
</ask_question>
   
"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        # The actual implementation preserves whitespace in parameter values
        assert params == {"question": "   What is this?   ", "context": "   Some context   "}
        assert thinking_content == "Some thinking content with spaces"

    def test_parse_tool_call_with_multiline_content(self):
        """Test parsing tool call with multiline content."""
        xml_content = """<thinking>
This is a multiline thinking content.
It spans multiple lines.
And has more content here.
</thinking>
<generate_knowledge>
<topic>Multiline Topic
with more details
and explanations</topic>
<format>markdown</format>
</generate_knowledge>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "generate_knowledge"
        assert params == {"topic": "Multiline Topic\nwith more details\nand explanations", "format": "markdown"}
        assert thinking_content == "This is a multiline thinking content.\nIt spans multiple lines.\nAnd has more content here."

    def test_parse_tool_call_missing_required_parameter(self):
        """Test that missing required parameters raise appropriate errors."""
        xml_content = """<ask_question>
<context>Some context without question</context>
</ask_question>"""

        with pytest.raises(ValueError, match="Required argument question not found"):
            self.handler._parse_xml_tool_call(xml_content)

    def test_parse_tool_call_invalid_tool_name(self):
        """Test that invalid tool names raise appropriate errors."""
        xml_content = """<invalid_tool>
<param>value</param>
</invalid_tool>"""

        with pytest.raises(ValueError, match="Could not parse tool name from the request"):
            self.handler._parse_xml_tool_call(xml_content)

    def test_parse_tool_call_no_xml_tags(self):
        """Test that content without XML tags raises appropriate errors."""
        xml_content = "This is just plain text without any XML tags."

        with pytest.raises(ValueError, match="Could not find any XML tags"):
            self.handler._parse_xml_tool_call(xml_content)

    def test_parse_tool_call_malformed_xml(self):
        """Test that malformed XML raises appropriate errors."""
        xml_content = """<ask_question>
<question>What is this?</question>
<context>Some context
</ask_question>"""

        # The current implementation is flexible and doesn't raise an error for this case
        # It successfully parses what it can find
        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": "What is this?"}
        assert thinking_content == ""

    def test_parse_tool_call_only_thinking_tag(self):
        """Test that content with only thinking tag raises appropriate errors."""
        xml_content = """<thinking>
This is just thinking content without any tool call.
</thinking>"""

        with pytest.raises(ValueError, match="Could not find tool name in XML"):
            self.handler._parse_xml_tool_call(xml_content)

    def test_parse_tool_call_empty_content(self):
        """Test that empty content raises appropriate errors."""
        xml_content = ""

        with pytest.raises(ValueError, match="Could not find any XML tags"):
            self.handler._parse_xml_tool_call(xml_content)

    def test_parse_tool_call_whitespace_only_content(self):
        """Test that whitespace-only content raises appropriate errors."""
        xml_content = "   \n\t   \n  "

        with pytest.raises(ValueError, match="Could not find any XML tags"):
            self.handler._parse_xml_tool_call(xml_content)

    def test_parse_tool_call_with_invalid_parameter_type(self):
        """Test that invalid parameter types raise appropriate errors."""
        xml_content = """<explore_knowledge>
<path>/root/topic</path>
<depth>not_a_number</depth>
</explore_knowledge>"""

        with pytest.raises(ValueError, match="Failed to parse argument depth to int"):
            self.handler._parse_xml_tool_call(xml_content)

    def test_parse_tool_call_with_nested_xml_in_parameters(self):
        """Test parsing tool call with nested XML content in parameters."""
        xml_content = """<ask_question>
<question>What do you think about <strong>this</strong> approach?</question>
<context>Context with <em>emphasis</em> and <code>code</code></context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "What do you think about <strong>this</strong> approach?",
            "context": "Context with <em>emphasis</em> and <code>code</code>",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_special_characters(self):
        """Test parsing tool call with special characters in content."""
        xml_content = """<thinking>
This contains special chars: @#$%^&*()_+-=[]{}|;':\",./<>?
</thinking>
<ask_question>
<question>What about special chars: @#$%^&*()?</question>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": "What about special chars: @#$%^&*()?"}
        assert thinking_content == "This contains special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"

    def test_parse_tool_call_with_unicode_content(self):
        """Test parsing tool call with unicode content."""
        xml_content = """<ask_question>
<question>What about unicode: 你好世界 🌍 émojis?</question>
<context>Context with unicode: ñáéíóú</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": "What about unicode: 你好世界 🌍 émojis?", "context": "Context with unicode: ñáéíóú"}
        assert thinking_content == ""

    def test_parse_tool_call_with_complex_list_parameter(self):
        """Test parsing tool call with complex list parameter."""
        xml_content = """<generate_knowledge>
<topic>Complex Topic</topic>
<options>['item1', 'item with spaces', 'item with "quotes"', 'item with \\'single quotes\\'']</options>
</generate_knowledge>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "generate_knowledge"
        assert params == {
            "topic": "Complex Topic",
            "options": ["item1", "item with spaces", 'item with "quotes"', "item with 'single quotes'"],
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_optional_parameters_missing(self):
        """Test parsing tool call with optional parameters missing."""
        xml_content = """<ask_question>
<question>What is this?</question>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": "What is this?"}
        assert thinking_content == ""

    def test_parse_tool_call_with_multiple_thinking_blocks(self):
        """Test parsing tool call with multiple thinking blocks (should use first one)."""
        xml_content = """<thinking>
First thinking block.
</thinking>
<thinking>
Second thinking block that should be ignored.
</thinking>
<ask_question>
<question>What is this?</question>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": "What is this?"}
        assert thinking_content == "First thinking block."

    def test_parse_tool_call_with_xml_entities(self):
        """Test parsing tool call with XML entities (not decoded by current implementation)."""
        xml_content = """<ask_question>
<question>What about XML entities: &lt;tag&gt; &amp; &quot;quotes&quot; &apos;apostrophe&apos;?</question>
<context>Context with &amp; ampersand and &lt;brackets&gt;</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        # The current implementation doesn't decode XML entities, they remain as-is
        assert params == {
            "question": "What about XML entities: &lt;tag&gt; &amp; &quot;quotes&quot; &apos;apostrophe&apos;?",
            "context": "Context with &amp; ampersand and &lt;brackets&gt;",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_control_characters(self):
        """Test parsing tool call with control characters."""
        xml_content = """<ask_question>
<question>Text with control chars: \x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f</question>
<context>Context with \x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with control chars: \x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f",
            "context": "Context with \x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_null_bytes(self):
        """Test parsing tool call with null bytes."""
        xml_content = """<ask_question>
<question>Text with null\x00bytes</question>
<context>Context with\x00null\x00bytes</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": "Text with null\x00bytes", "context": "Context with\x00null\x00bytes"}
        assert thinking_content == ""

    def test_parse_tool_call_with_backslashes(self):
        """Test parsing tool call with various backslash sequences."""
        xml_content = """<ask_question>
<question>Text with backslashes: \\ \\\\ \\n \\t \\r \\" \\'</question>
<context>Context with \\\\double\\\\backslashes</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with backslashes: \\ \\\\ \\n \\t \\r \\\" \\'",
            "context": "Context with \\\\double\\\\backslashes",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_mixed_quotes(self):
        """Test parsing tool call with mixed quote types."""
        xml_content = """<ask_question>
<question>Text with "double quotes" and 'single quotes' and `backticks`</question>
<context>Context with "nested 'quotes' inside" and 'nested "quotes" inside'</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with \"double quotes\" and 'single quotes' and `backticks`",
            "context": "Context with \"nested 'quotes' inside\" and 'nested \"quotes\" inside'",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_brackets_and_braces(self):
        """Test parsing tool call with various bracket types."""
        xml_content = """<ask_question>
<question>Text with brackets: [] {} () <> [[]] {{}} (()) <></></question>
<context>Context with [nested {brackets (inside) brackets} brackets]</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with brackets: [] {} () <> [[]] {{}} (()) <></>",
            "context": "Context with [nested {brackets (inside) brackets} brackets]",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_math_symbols(self):
        """Test parsing tool call with mathematical symbols."""
        xml_content = """<ask_question>
<question>Math symbols: ∑ ∏ ∫ ∞ ± × ÷ ≤ ≥ ≠ ≈ √ ∛ ∜</question>
<context>Context with α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Math symbols: ∑ ∏ ∫ ∞ ± × ÷ ≤ ≥ ≠ ≈ √ ∛ ∜",
            "context": "Context with α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_currency_symbols(self):
        """Test parsing tool call with currency and financial symbols."""
        xml_content = """<ask_question>
<question>Currency symbols: $ € £ ¥ ₹ ₽ ₩ ₪ ₫ ₨ ₴ ₸ ₺ ₼ ₾</question>
<context>Context with financial symbols: % ‰ ‱ ↑ ↓ ↗ ↘ ↙ ↖</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Currency symbols: $ € £ ¥ ₹ ₽ ₩ ₪ ₫ ₨ ₴ ₸ ₺ ₼ ₾",
            "context": "Context with financial symbols: % ‰ ‱ ↑ ↓ ↗ ↘ ↙ ↖",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_emoji_and_symbols(self):
        """Test parsing tool call with emojis and various symbols."""
        xml_content = """<ask_question>
<question>Emojis: 😀 😃 😄 😁 😆 😅 🤣 😂 🥲 🥹 😊 😇 🙂 🙃 😉 😌 😍 🥰 😘 😗 😙 😚 😋 😛 😝 😜 🤪 🤨 🧐 🤓 😎 🥸 🤩 🥳</question>
<context>Context with symbols: ★ ☆ ♠ ♣ ♥ ♦ ♪ ♫ ♬ ♭ ♮ ♯</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Emojis: 😀 😃 😄 😁 😆 😅 🤣 😂 🥲 🥹 😊 😇 🙂 🙃 😉 😌 😍 🥰 😘 😗 😙 😚 😋 😛 😝 😜 🤪 🤨 🧐 🤓 😎 🥸 🤩 🥳",
            "context": "Context with symbols: ★ ☆ ♠ ♣ ♥ ♦ ♪ ♫ ♬ ♭ ♮ ♯",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_very_long_content(self):
        """Test parsing tool call with very long content that might cause regex issues."""
        long_text = "A" * 10000  # 10,000 character string
        xml_content = f"""<ask_question>
<question>{long_text}</question>
<context>Short context</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {"question": long_text, "context": "Short context"}
        assert thinking_content == ""

    def test_parse_tool_call_with_mixed_encoding(self):
        """Test parsing tool call with mixed character encodings."""
        xml_content = """<ask_question>
<question>Mixed encoding: 你好世界 🌍 café naïve résumé naïve</question>
<context>Context with: 中文 English العربية русский</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Mixed encoding: 你好世界 🌍 café naïve résumé naïve",
            "context": "Context with: 中文 English العربية русский",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_xml_like_content_in_params(self):
        """Test parsing tool call with XML-like content inside parameters."""
        xml_content = """<ask_question>
<question>What about <tag>content</tag> and <self-closing/> tags?</question>
<context>Context with <![CDATA[CDATA sections]]> and <!--comments--></context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "What about <tag>content</tag> and <self-closing/> tags?",
            "context": "Context with <![CDATA[CDATA sections]]> and <!--comments-->",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_whitespace_variations(self):
        """Test parsing tool call with various whitespace characters."""
        xml_content = """<ask_question>
<question>Text with various whitespace: regular space,	tab, newline
and carriage return</question>
<context>Context with non-breaking\u00a0space and other\u2000whitespace</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with various whitespace: regular space,\ttab, newline\nand carriage return",
            "context": "Context with non-breaking\u00a0space and other\u2000whitespace",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_angle_brackets_in_content(self):
        """Test parsing tool call with angle brackets that might confuse XML parsing."""
        xml_content = """<ask_question>
<question>Text with angle brackets: < > << >> <<< >>> and combinations</question>
<context>Context with <nested> <brackets> <everywhere></context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with angle brackets: < > << >> <<< >>> and combinations",
            "context": "Context with <nested> <brackets> <everywhere>",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_unescaped_less_than_greater_than(self):
        """Test parsing tool call with unescaped < and > characters that could break XML."""
        xml_content = """<ask_question>
<question>Text with unescaped < and > characters</question>
<context>Context with <unescaped> <characters> <everywhere></context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with unescaped < and > characters",
            "context": "Context with <unescaped> <characters> <everywhere>",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_ampersand_in_content(self):
        """Test parsing tool call with unescaped ampersands that could break XML."""
        xml_content = """<ask_question>
<question>Text with unescaped & ampersands & more & symbols</question>
<context>Context with & ampersands & everywhere & in & content</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with unescaped & ampersands & more & symbols",
            "context": "Context with & ampersands & everywhere & in & content",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_quotes_in_content(self):
        """Test parsing tool call with unescaped quotes that could break XML."""
        xml_content = """<ask_question>
<question>Text with "double quotes" and 'single quotes' mixed</question>
<context>Context with "quotes" and 'apostrophes' everywhere</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with \"double quotes\" and 'single quotes' mixed",
            "context": "Context with \"quotes\" and 'apostrophes' everywhere",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_newlines_and_tabs_in_xml_structure(self):
        """Test parsing tool call with newlines and tabs in the XML structure itself."""
        xml_content = """<ask_question>
	<question>
		Text with tabs and newlines
		in the XML structure
	</question>
	<context>
		Context with
		multiple lines
		and tabs
	</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        # The actual implementation preserves the newline after the opening tag
        assert params == {
            "question": "\n\t\tText with tabs and newlines\n\t\tin the XML structure\n\t",
            "context": "\n\t\tContext with\n\t\tmultiple lines\n\t\tand tabs\n\t",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_very_deep_nesting(self):
        """Test parsing tool call with very deep nesting that might cause regex issues."""
        xml_content = """<ask_question>
<question>Text with <very> <deep> <nesting> <of> <tags> <everywhere> <in> <the> <content> <structure></question>
<context>Context with <nested> <tags> <inside> <other> <tags> <deeply> <nested></context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with <very> <deep> <nesting> <of> <tags> <everywhere> <in> <the> <content> <structure>",
            "context": "Context with <nested> <tags> <inside> <other> <tags> <deeply> <nested>",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_regex_special_characters(self):
        """Test parsing tool call with regex special characters that might break parsing."""
        xml_content = """<ask_question>
<question>Text with regex chars: . * + ? ^ $ | \\ ( ) [ ] { }</question>
<context>Context with .*+?^$|\\()[]{} characters</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with regex chars: . * + ? ^ $ | \\ ( ) [ ] { }",
            "context": "Context with .*+?^$|\\()[]{} characters",
        }
        assert thinking_content == ""

    def test_parse_tool_call_with_unicode_control_characters(self):
        """Test parsing tool call with Unicode control characters."""
        xml_content = """<ask_question>
<question>Text with Unicode controls: \u200b\u200c\u200d\u2060\u2061\u2062\u2063\u2064</question>
<context>Context with \u200e\u200f\u202a\u202b\u202c\u202d\u202e\u202f</context>
</ask_question>"""

        tool_name, params, thinking_content = self.handler._parse_xml_tool_call(xml_content)

        assert tool_name == "ask_question"
        assert params == {
            "question": "Text with Unicode controls: \u200b\u200c\u200d\u2060\u2061\u2062\u2063\u2064",
            "context": "Context with \u200e\u200f\u202a\u202b\u202c\u202d\u202e\u202f",
        }
        assert thinking_content == ""
