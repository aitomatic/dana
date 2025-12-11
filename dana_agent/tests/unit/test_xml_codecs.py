"""
Unit tests for XML codec classes (CSXMLCodec and KLXMLCodec).

This module tests the parse_method_call functionality for both codec classes,
ensuring they can parse XML method call strings back into ToolCall objects.
"""

from dana.common.schemas.tool_call import MethodSignature, ParameterInfo, ParsedCodecResponse, ToolCall
from dana.core.knowledge.prompts.codecs.xml_format import CSXMLCodec, KLXMLCodec


class TestToolCallSchemas:
    """Test ToolCall and MethodSignature schemas with object_id field."""

    def test_method_signature_with_object_id(self):
        """Test MethodSignature can be created with object_id."""
        param = ParameterInfo(name="query", type="str", description="Search query", has_default=False)
        signature = MethodSignature(
            class_name="SearchResource", object_id="my-search-resource", name="search", description="Search method", parameters=[param]
        )

        assert signature.class_name == "SearchResource"
        assert signature.object_id == "my-search-resource"
        assert signature.name == "search"

    def test_method_signature_without_object_id(self):
        """Test MethodSignature backward compatibility - works without object_id."""
        param = ParameterInfo(name="query", type="str", description="Search query", has_default=False)
        signature = MethodSignature(class_name="SearchResource", name="search", description="Search method", parameters=[param])

        assert signature.class_name == "SearchResource"
        assert signature.object_id is None
        assert signature.name == "search"

    def test_tool_call_with_object_id(self):
        """Test ToolCall can be created with object_id."""
        tool_call = ToolCall(class_name="SearchResource", object_id="my-search-resource", name="search", parameters={"query": "test"})

        assert tool_call.class_name == "SearchResource"
        assert tool_call.object_id == "my-search-resource"
        assert tool_call.name == "search"
        assert tool_call.parameters == {"query": "test"}

    def test_tool_call_without_object_id(self):
        """Test ToolCall backward compatibility - works without object_id."""
        tool_call = ToolCall(class_name="SearchResource", name="search", parameters={"query": "test"})

        assert tool_call.class_name == "SearchResource"
        assert tool_call.object_id is None
        assert tool_call.name == "search"
        assert tool_call.parameters == {"query": "test"}


class TestKLXMLCodecParseMethodCall:
    """Test KLXMLCodec.parse_method_call functionality."""

    def test_parse_simple_xml(self):
        """Test parsing simple XML with single parameter."""
        xml_string = """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "CreateFileResource"
        assert result.name == "create"
        assert result.parameters == {"relative_workspace_path": "dana/hello.py"}

    def test_parse_xml_multiple_parameters(self):
        """Test parsing XML with multiple parameters."""
        xml_string = """<MyResource:myMethod>
<param1>value1</param1>
<param2>value2</param2>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters == {"param1": "value1", "param2": "value2"}

    def test_parse_xml_multiline_content(self):
        """Test parsing XML with multiline content in parameters."""
        xml_string = """<MyResource:myMethod>
<description>This is a
multiline
description</description>
<code>def hello():
    print("world")
</code>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert "This is a\nmultiline\ndescription" in result.parameters["description"]
        assert "def hello():" in result.parameters["code"]

    def test_parse_xml_missing_closing_tags(self):
        """Test parsing XML with missing closing tags using fallback approach."""
        xml_string = """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
<another_param>some value"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "CreateFileResource"
        assert result.name == "create"
        assert "relative_workspace_path" in result.parameters
        assert "another_param" in result.parameters

    def test_parse_xml_empty_parameters(self):
        """Test parsing XML with empty parameter tags."""
        xml_string = """<MyResource:myMethod>
<param1></param1>
<param2>value2</param2>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters["param1"] == "" or result.parameters.get("param1") is None
        assert result.parameters["param2"] == "value2"

    def test_parse_xml_no_parameters(self):
        """Test parsing XML with no parameters."""
        xml_string = """<MyResource:myMethod>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters == {}


class TestCSXMLCodecParseMethodCall:
    """Test CSXMLCodec.parse_method_call functionality."""

    def test_parse_full_function_call_format(self):
        """Test parsing full function_call format."""
        xml_string = """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "CreateFileResource"
        assert result.name == "create"
        assert result.parameters == {"relative_workspace_path": "dana/hello.py"}

    def test_parse_invoke_tags_multiple_parameters(self):
        """Test parsing invoke tags with multiple parameters."""
        xml_string = """<function_call>
<invoke name="MyResource:myMethod">
<parameter name="param1">value1</parameter>
<parameter name="param2">value2</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters == {"param1": "value1", "param2": "value2"}

    def test_parse_xml_missing_closing_tags(self):
        """Test parsing XML with missing closing tags."""
        xml_string = """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
<parameter name="another_param">some value"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "CreateFileResource"
        assert result.name == "create"
        assert "relative_workspace_path" in result.parameters
        assert "another_param" in result.parameters

    def test_parse_xml_empty_parameters(self):
        """Test parsing XML with empty parameter tags."""
        xml_string = """<function_call>
<invoke name="MyResource:myMethod">
<parameter name="param1"></parameter>
<parameter name="param2">value2</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters.get("param1") == "" or result.parameters.get("param1") is None
        assert result.parameters["param2"] == "value2"

    def test_parse_xml_no_parameters(self):
        """Test parsing XML with no parameters."""
        xml_string = """<function_call>
<invoke name="MyResource:myMethod">
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters == {}


class TestXMLCodecsRoundTrip:
    """Test round-trip conversion: construct → parse_method_call."""

    def test_klxml_round_trip(self):
        """Test KLXMLCodec round-trip conversion."""
        signature = MethodSignature(
            class_name="CreateFileResource",
            name="create",
            description="Create a new file",
            parameters=[
                ParameterInfo(
                    name="relative_workspace_path", type="str", description="Path to file", has_default=False, example="dana/hello.py"
                )
            ],
        )

        # Construct XML
        KLXMLCodec.construct(signature)

        # Extract just the usage example part (the XML call format)
        # The construct method returns a full description, we need the usage example
        usage_example = KLXMLCodec._usage_example(signature)

        # Parse back
        result = KLXMLCodec.parse_method_call(usage_example)

        assert result.class_name == signature.class_name
        assert result.name == signature.name
        assert result.parameters["relative_workspace_path"] == "dana/hello.py"

    def test_csxml_round_trip(self):
        """Test CSXMLCodec round-trip conversion."""
        signature = MethodSignature(
            class_name="CreateFileResource",
            name="create",
            description="Create a new file",
            parameters=[
                ParameterInfo(
                    name="relative_workspace_path", type="str", description="Path to file", has_default=False, example="dana/hello.py"
                )
            ],
        )

        # Construct XML
        CSXMLCodec.construct(signature)

        # Extract just the usage example part (the XML call format)
        usage_example = CSXMLCodec._usage_example(signature)

        # Parse back
        result = CSXMLCodec.parse_method_call(usage_example)

        assert result.class_name == signature.class_name
        assert result.name == signature.name
        assert result.parameters["relative_workspace_path"] == "dana/hello.py"


class TestCSXMLCodecParseResponse:
    """Test CSXMLCodec.parse_response functionality."""

    def test_parse_response_with_single_tool_call_and_thinking(self):
        """Test parse_response with single tool call and thinking block."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].class_name == "CreateFileResource"
        assert result.tool_calls[0].name == "create"
        assert result.tool_calls[0].parameters == {"relative_workspace_path": "dana/hello.py"}

    def test_parse_response_with_multiple_tool_calls(self):
        """Test parse_response with multiple tool calls."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>
<function_call>
<invoke name="MyResource:myMethod">
<parameter name="param1">value1</parameter>
<parameter name="param2">value2</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].class_name == "CreateFileResource"
        assert result.tool_calls[0].name == "create"
        assert result.tool_calls[1].class_name == "MyResource"
        assert result.tool_calls[1].name == "myMethod"
        assert result.tool_calls[1].parameters == {"param1": "value1", "param2": "value2"}

    def test_parse_response_with_multiple_invokes_in_single_function_call(self):
        """Test parse_response with multiple invoke tags inside a single function_call block."""
        xml_string = """<thinking>
I will get connected nodes for multiple node IDs in parallel.
</thinking>
<function_call>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">1</parameter>
  <parameter name="direction">both</parameter>
</invoke>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">3</parameter>
  <parameter name="direction">both</parameter>
</invoke>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">8</parameter>
  <parameter name="direction">both</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "I will get connected nodes for multiple node IDs in parallel."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 3
        assert result.tool_calls[0].class_name == "ontology"
        assert result.tool_calls[0].name == "get_connected_nodes"
        assert result.tool_calls[0].parameters == {"node_id": "1", "direction": "both"}
        assert result.tool_calls[1].parameters == {"node_id": "3", "direction": "both"}
        assert result.tool_calls[2].parameters == {"node_id": "8", "direction": "both"}

    def test_parse_response_without_thinking_block(self):
        """Test parse_response without thinking block (should treat text before tool calls as thinking)."""
        xml_string = """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == ""  # No text before tool calls
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_with_text_before_tool_calls_no_thinking_tag(self):
        """Test parse_response with text before tool calls but no <thinking> tag."""
        xml_string = """This is some thinking text
about what I should do.
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is some thinking text" in result.thinking
        assert "about what I should do" in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_without_tool_calls(self):
        """Test parse_response without tool calls (should return None)."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is None

    def test_parse_response_with_xml_comments_in_thinking(self):
        """Test parse_response with XML comments in thinking block."""
        xml_string = """<thinking>
<!-- 50-100 words max:
Intent: What user wants
Context: Current state
-->
This is my thinking about the task.
</thinking>
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        # XML comments should be stripped
        assert "<!--" not in result.thinking
        assert "Intent: What user wants" not in result.thinking
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is not None

    def test_parse_response_with_text_before_and_after_xml(self):
        """Test parse_response with text before and after XML blocks."""
        xml_string = """Some text before
<thinking>
This is my thinking about the task.
</thinking>
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>
Some text after"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_with_empty_function_call(self):
        """Test parse_response with empty function_call block (should skip it gracefully)."""
        xml_string = """<thinking>
Intent: Confirm and proceed with creating the financial health report for AMD.
Context: The data directory does not exist or is not found, so I cannot access the data files needed to perform the analysis.
Decision: Inform the user about the missing data directory so they can provide the necessary data or correct the path.
Approval: Request user confirmation or instructions on how to proceed given the missing data.
User Message: I attempted to access the data directory to locate AMD's financial data files but the directory was not found. Please verify the data location or provide the data files needed to proceed with the financial health report.
</thinking>

<function_call>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "Intent: Confirm and proceed" in result.thinking
        # Empty function_call should be skipped, so tool_calls should be None or empty list
        assert result.tool_calls is None or len(result.tool_calls) == 0

    def test_parse_response_fallback_thinking_with_text_after_function_calls(self):
        """Test parse_response fallback: extract thinking from text after function_call blocks when thinking is empty."""
        xml_string = """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>
This is some thinking text that should be extracted as thinking.
It appears after the function call."""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is some thinking text" in result.thinking
        assert "appears after the function call" in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_fallback_thinking_with_text_between_function_calls(self):
        """Test parse_response fallback: extract thinking from text between function_call blocks when thinking is empty."""
        xml_string = """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>
Some text between function calls
<function_call>
<invoke name="MyResource:myMethod">
<parameter name="param1">value1</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "Some text between function calls" in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 2

    def test_parse_response_fallback_thinking_only_function_calls(self):
        """Test parse_response fallback: when xml_string contains only function_call blocks, thinking should remain empty."""
        xml_string = """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == ""  # Should remain empty when only function calls exist
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_with_response_tag(self):
        """Test parse_response with response tag."""
        xml_string = """<response>
This is the response content.
</response>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.response == "This is the response content."
        assert result.thinking == ""  # No thinking tag
        assert result.tool_calls is None

    def test_parse_response_with_response_and_thinking(self):
        """Test parse_response with both response and thinking tags."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<response>
This is the response content.
</response>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.response == "This is the response content."
        assert result.tool_calls is None

    def test_parse_response_response_equals_thinking_when_only_thinking(self):
        """Test parse_response: when only thinking exists, response = thinking."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.response == "This is my thinking about the task."  # response = thinking
        assert result.tool_calls is None

    def test_parse_response_prioritizes_tool_calls_over_response(self):
        """Test parse_response: when both response and function_call exist, prioritize tool_calls (ignore response)."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<response>
This response should be ignored.
</response>
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.response is None  # Response should be ignored when tool_calls exist
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].class_name == "CreateFileResource"

    def test_parse_response_with_response_tag_only(self):
        """Test parse_response with only response tag (no thinking, no tool calls)."""
        xml_string = """<response>
This is the response content without thinking or tool calls.
</response>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.response == "This is the response content without thinking or tool calls."
        assert result.thinking == ""  # No thinking tag
        assert result.tool_calls is None

    def test_parse_response_missing_closing_response_tag(self):
        """Test parse_response with missing </response> closing tag (edge case from user)."""
        xml_string = """<thinking>

The search returned 20 results for polymers with compositions of the form IS/Yp/[PAG monomer], where the PAG monomer is one of the provided alternatives (including Ben, Est, Sen, Den, etc.), and filtered by the specified polymerization conditions (radical_method: Free, temperature: 100±10°C, solvent: 2, sm_value: 3.5±0.5, reaction_time: 7h-and-1h). The results include several matches for IS/Yp/Ben, IS/Yp/Sen, and IS/Yp/Est, as well as other related compositions. I will present the results in a markdown table and summarize the findings.

</thinking>

<response>

Here are the filtered search results for polymers with compositions IS/Yp/[PAG monomer] (where the PAG monomer shares the same anion as Ben), under the specified polymerization conditions:

| LotNo   | Composition         | PolymerizationCondition                        |

|---------|--------------------|-----------------------------------------------|

| AB-4231 | M0684/M0037/M0901  | 127 Free@100 in Solvent2, SM3.0, 9h-and-1h    |

| AB-4236 | M0557/M0013/M0757  | 127 Free@100 in Solvent2, SM3.2, 8h-and-1.5h  |

| AB-5479 | IS/Yp/Ben          | 127 Free@100 in Solvent2, SM3.5, 7h-and-1h    |

| AB-4065 | M0540/M0838/M0248  | 138 Free@106 in Solvent2, SM3.7, 8h-and-0h    |

| AB-4280 | M0494/M0447/M0540  | 164 Free@100 in Solvent2, SM3.0, 6h-and-0h    |

| AB-4106 | M0180/M0446/M0598  | 85 Free@92 in Solvent2, SM4.0, 5h-and-3h      |

| AB-4161 | M0166/M0321/M0086  | 105 Free@110 in Solvent2, SM3.8, 9h-and-2h    |

| AB-4199 | M0569/M0383/M0434  | 112 Free@98 in Solvent2, SM3.3, 7h-and-1h     |

| AB-4126 | M0274/M0079/J4Z    | 153 Free@96 in Solvent2, SM3.6, 8h-and-2h     |

| AB-4298 | M0676/M0621/M0454  | 168 Free@97 in Solvent2, SM3.6, 5h-and-0h     |

| AB-4069 | M0072/M0522/M0163  | 141 Free@103 in Solvent2, SM3.1, 8h-and-0h    |

| AB-4195 | M0370/M0194/M0886  | 113 Free@93 in Solvent2, SM3.2, 6h-and-2h     |

| AB-5242 | IS/Yp/Sen          | 127 Free@100 in Solvent2, SM3.5, 7h-and-1h    |

| AB-5075 | IS/Yp/Sen          | 127 Free@100 in Solvent2, SM3.5, 7h-and-1h    |

| AB-3040 | IS/Yp/Sen          | 109 Free@105 in Solvent2, SM3.0, 7h-and-1h    |

| AB-3667 | IS/Yp/Sen          | 73 Free@100 in Solvent2, SM4.0, 7h-and-1h     |

| AB-5581 | IS/Yp/Sen          | 73 Free@100 in Solvent2, SM4.0, 7h-and-1h     |

| AB-5505 | IS/Yp/Sen          | 127 Free@100 in Solvent2, SM3.5, 7h-and-1h    |

| AB-5484 | IS/Yp/Sen          | 98 Free@105 in Solvent2, SM4.0, 7h-and-1h     |

| AB-4518 | IS/Yp/Est          | 127 Free@100 in Solvent2, SM3.5, 7h-and-1h    |

**Summary of findings:**

- 20 results were found matching the specified compositions and polymerization conditions.

- Lot numbers of interest include AB-5479 (IS/Yp/Ben), AB-4518 (IS/Yp/Est), and several for IS/Yp/Sen.

- The search was filtered by: radical_method = Free, temperature = 100°C (±10°C), solvent = 2, sm_value = 3.5 (±0.5), reaction_time = 7h-and-1h.

- Most results are for IS/Yp/Ben, IS/Yp/Est, and IS/Yp/Sen, with a few other related compositions.

If you need more details on any specific lot or want to expand the search, let me know!

"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "The search returned 20 results" in result.thinking
        assert result.response is not None
        assert "Here are the filtered search results" in result.response
        assert "AB-5479" in result.response
        assert "If you need more details" in result.response
        assert result.tool_calls is None

    def test_parse_response_missing_closing_thinking_tag(self):
        """Test parse_response with missing </thinking> closing tag."""
        xml_string = """<thinking>
This is my thinking about the task.
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is my thinking about the task." in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_missing_closing_function_call_tag(self):
        """Test parse_response with missing </function_call> closing tag."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
"""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is my thinking about the task." in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].class_name == "CreateFileResource"

    def test_parse_response_missing_both_thinking_and_response_closing_tags(self):
        """Test parse_response with both thinking and response missing closing tags."""
        xml_string = """<thinking>
This is my thinking.
<response>
This is the response content."""

        result = CSXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is my thinking." in result.thinking
        assert result.response is not None
        assert "This is the response content." in result.response
        assert result.tool_calls is None


class TestKLXMLCodecParseResponse:
    """Test KLXMLCodec.parse_response functionality."""

    def test_parse_response_with_single_tool_call_and_thinking(self):
        """Test parse_response with single tool call and thinking block."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].class_name == "CreateFileResource"
        assert result.tool_calls[0].name == "create"
        assert result.tool_calls[0].parameters == {"relative_workspace_path": "dana/hello.py"}

    def test_parse_response_with_multiple_tool_calls(self):
        """Test parse_response with multiple tool calls."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>
<MyResource:myMethod>
<param1>value1</param1>
<param2>value2</param2>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].class_name == "CreateFileResource"
        assert result.tool_calls[0].name == "create"
        assert result.tool_calls[1].class_name == "MyResource"
        assert result.tool_calls[1].name == "myMethod"

    def test_parse_response_with_many_parallel_tool_calls(self):
        """Test parse_response with many parallel tool calls (6 calls)."""
        xml_string = """<thinking>
I will get connected nodes for multiple node IDs in parallel.
</thinking>
<ontology:get_connected_nodes>
<node_id>1</node_id>
<direction>both</direction>
</ontology:get_connected_nodes>
<ontology:get_connected_nodes>
<node_id>3</node_id>
<direction>both</direction>
</ontology:get_connected_nodes>
<ontology:get_connected_nodes>
<node_id>8</node_id>
<direction>both</direction>
</ontology:get_connected_nodes>
<ontology:get_connected_nodes>
<node_id>10</node_id>
<direction>both</direction>
</ontology:get_connected_nodes>
<ontology:get_connected_nodes>
<node_id>7</node_id>
<direction>both</direction>
</ontology:get_connected_nodes>
<ontology:get_connected_nodes>
<node_id>12</node_id>
<direction>both</direction>
</ontology:get_connected_nodes>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "I will get connected nodes for multiple node IDs in parallel."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 6
        # Verify all tool calls have correct class and method
        for tool_call in result.tool_calls:
            assert tool_call.class_name == "ontology"
            assert tool_call.name == "get_connected_nodes"
            assert tool_call.parameters["direction"] == "both"
        # Verify each node_id is correct
        assert result.tool_calls[0].parameters["node_id"] == "1"
        assert result.tool_calls[1].parameters["node_id"] == "3"
        assert result.tool_calls[2].parameters["node_id"] == "8"
        assert result.tool_calls[3].parameters["node_id"] == "10"
        assert result.tool_calls[4].parameters["node_id"] == "7"
        assert result.tool_calls[5].parameters["node_id"] == "12"

    def test_parse_response_without_thinking_block(self):
        """Test parse_response without thinking block (should treat text before tool calls as thinking)."""
        xml_string = """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == ""  # No text before tool calls
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_with_text_before_tool_calls_no_thinking_tag(self):
        """Test parse_response with text before tool calls but no <thinking> tag."""
        xml_string = """This is some thinking text
about what I should do.
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is some thinking text" in result.thinking
        assert "about what I should do" in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_without_tool_calls(self):
        """Test parse_response without tool calls (should return None)."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is None

    def test_parse_response_with_xml_comments_in_thinking(self):
        """Test parse_response with XML comments in thinking block."""
        xml_string = """<thinking>
<!-- 50-100 words max:
Intent: What user wants
Context: Current state
-->
This is my thinking about the task.
</thinking>
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        # XML comments should be stripped
        assert "<!--" not in result.thinking
        assert "Intent: What user wants" not in result.thinking
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is not None

    def test_parse_response_with_text_before_and_after_xml(self):
        """Test parse_response with text before and after XML blocks."""
        xml_string = """Some text before
<thinking>
This is my thinking about the task.
</thinking>
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>
Some text after"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_fallback_thinking_with_text_after_tool_calls(self):
        """Test parse_response fallback: extract thinking from text after tool call blocks when thinking is empty."""
        xml_string = """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>
This is some thinking text that should be extracted as thinking.
It appears after the tool call."""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is some thinking text" in result.thinking
        assert "appears after the tool call" in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_fallback_thinking_with_text_between_tool_calls(self):
        """Test parse_response fallback: extract thinking from text between tool call blocks when thinking is empty."""
        xml_string = """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>
Some text between tool calls
<MyResource:myMethod>
<param1>value1</param1>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "Some text between tool calls" in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 2

    def test_parse_response_fallback_thinking_only_tool_calls(self):
        """Test parse_response fallback: when xml_string contains only tool call blocks, thinking should remain empty."""
        xml_string = """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == ""  # Should remain empty when only tool calls exist
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_with_response_tag(self):
        """Test parse_response with response tag."""
        xml_string = """<response>
This is the response content.
</response>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.response == "This is the response content."
        assert result.thinking == ""  # No thinking tag
        assert result.tool_calls is None

    def test_parse_response_with_response_and_thinking(self):
        """Test parse_response with both response and thinking tags."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<response>
This is the response content.
</response>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.response == "This is the response content."
        assert result.tool_calls is None

    def test_parse_response_response_equals_thinking_when_only_thinking(self):
        """Test parse_response: when only thinking exists, response = thinking."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.response == "This is my thinking about the task."  # response = thinking
        assert result.tool_calls is None

    def test_parse_response_prioritizes_tool_calls_over_response(self):
        """Test parse_response: when both response and tool call blocks exist, prioritize tool_calls (ignore response)."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<response>
This response should be ignored.
</response>
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.thinking == "This is my thinking about the task."
        assert result.response is None  # Response should be ignored when tool_calls exist
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].class_name == "CreateFileResource"

    def test_parse_response_with_response_tag_only(self):
        """Test parse_response with only response tag (no thinking, no tool calls)."""
        xml_string = """<response>
This is the response content without thinking or tool calls.
</response>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert result.response == "This is the response content without thinking or tool calls."
        assert result.thinking == ""  # No thinking tag
        assert result.tool_calls is None

    def test_parse_response_missing_closing_response_tag(self):
        """Test parse_response with missing </response> closing tag."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<response>
This is the response content without closing tag."""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is my thinking about the task." in result.thinking
        assert result.response is not None
        assert "This is the response content without closing tag." in result.response
        assert result.tool_calls is None

    def test_parse_response_missing_closing_thinking_tag(self):
        """Test parse_response with missing </thinking> closing tag."""
        xml_string = """<thinking>
This is my thinking about the task.
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is my thinking about the task." in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1

    def test_parse_response_missing_closing_tool_call_tag(self):
        """Test parse_response with missing closing tag for tool call."""
        xml_string = """<thinking>
This is my thinking about the task.
</thinking>
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
"""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is my thinking about the task." in result.thinking
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].class_name == "CreateFileResource"

    def test_parse_response_missing_both_thinking_and_response_closing_tags(self):
        """Test parse_response with both thinking and response missing closing tags."""
        xml_string = """<thinking>
This is my thinking.
<response>
This is the response content."""

        result = KLXMLCodec.parse_response(xml_string)

        assert isinstance(result, ParsedCodecResponse)
        assert "This is my thinking." in result.thinking
        assert result.response is not None
        assert "This is the response content." in result.response
        assert result.tool_calls is None
